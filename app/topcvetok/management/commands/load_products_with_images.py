import xml.etree.ElementTree as ET
import csv
import os
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from decimal import Decimal
import re
from PIL import Image

from topcvetok.models import (
    Category, Attribute, Product, ProductAttribute,
    Service, DeliveryMethod, PaymentMethod
)


class Command(BaseCommand):
    help = 'Загружает товары из XML и соотносит их с изображениями из CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--xml-file',
            type=str,
            default='topcvetok_xml.xml',
            help='Путь к XML файлу'
        )
        parser.add_argument(
            '--csv-file',
            type=str,
            default='wc-product.csv',
            help='Путь к CSV файлу'
        )
        parser.add_argument(
            '--max-products',
            type=int,
            default=100,
            help='Максимальное количество товаров для загрузки'
        )
        parser.add_argument(
            '--download-images',
            action='store_true',
            help='Скачивать изображения'
        )
        parser.add_argument(
            '--images-dir',
            type=str,
            default='media/downloaded_images/',
            help='Директория для сохранения изображений'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Задержка между скачиванием изображений'
        )
        parser.add_argument(
            '--clear-tables',
            action='store_true',
            help='Очистить таблицы перед загрузкой'
        )

    def handle(self, *args, **options):
        self.xml_file = options['xml_file']
        self.csv_file = options['csv_file']
        self.max_products = options['max_products']
        self.download_images = options['download_images']
        self.images_dir = options['images_dir']
        self.delay = options['delay']
        self.clear_tables = options['clear_tables']
        
        self.stdout.write('Загрузка товаров с изображениями...')
        
        try:
            with transaction.atomic():
                # 0. Очищаем таблицы если нужно
                if self.clear_tables:
                    self.clear_product_tables()
                
                # 1. Создаем базовые данные
                self.create_basic_data()
                
                # 2. Загружаем данные из CSV (изображения)
                csv_data = self.load_csv_data()
                
                # 3. Загружаем товары из XML и соотносим с изображениями
                self.load_products_from_xml(csv_data)
                
                self.stdout.write(
                    self.style.SUCCESS('Загрузка товаров завершена успешно!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке: {e}')
            )
            raise

    def clear_product_tables(self):
        """Очищает таблицы товаров перед загрузкой"""
        self.stdout.write('Очистка таблиц товаров...')
        
        # Очищаем в правильном порядке (сначала связи, потом основные таблицы)
        ProductAttribute.objects.all().delete()
        self.stdout.write('  - Очищены связи товар-атрибут')
        
        Product.objects.all().delete()
        self.stdout.write('  - Очищены товары')
        
        Attribute.objects.all().delete()
        self.stdout.write('  - Очищены атрибуты')
        
        Category.objects.all().delete()
        self.stdout.write('  - Очищены категории')
        
        self.stdout.write('Таблицы очищены успешно!')

    def create_basic_data(self):
        """Создает базовые данные (услуги, способы доставки, оплаты)"""
        self.stdout.write('Создание базовых данных...')
        
        # Создаем услуги
        services_data = [
            {
                'name': 'Атласной лентой',
                'description': 'Упаковка в атласную ленту',
                'price': None,
                'is_available': True
            },
            {
                'name': 'С оформлением',
                'description': 'Оформление заказа',
                'price': Decimal('12.00'),
                'is_available': True
            }
        ]
        
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                self.stdout.write(f'Создана услуга: {service.name}')

        # Создаем способы доставки
        delivery_methods_data = [
            {
                'name': 'Доставка по Минску',
                'description': 'Доставка по городу Минску в течение 2 часов',
                'delivery_type': 'minsk',
                'base_price': Decimal('0.00'),
                'free_delivery_min_amount': Decimal('250.00'),
                'working_hours_start': '08:00:00',
                'working_hours_end': '22:00:00',
                'low_amount_delivery_price': Decimal('12.00'),
                'low_amount_early_price': Decimal('24.00'),
                'low_amount_late_price': Decimal('24.00'),
                'late_delivery_min_amount': Decimal('170.00'),
                'is_active': True
            },
            {
                'name': 'Доставка по Беларуси',
                'description': 'Доставка по всей территории Беларуси',
                'delivery_type': 'belarus',
                'base_price': Decimal('15.00'),
                'free_delivery_min_amount': Decimal('500.00'),
                'working_hours_start': '09:00:00',
                'working_hours_end': '18:00:00',
                'low_amount_delivery_price': Decimal('15.00'),
                'low_amount_early_price': Decimal('25.00'),
                'low_amount_late_price': Decimal('25.00'),
                'late_delivery_min_amount': Decimal('300.00'),
                'is_active': True
            },
            {
                'name': 'Самовывоз',
                'description': 'Самовывоз из нашего магазина',
                'delivery_type': 'pickup',
                'base_price': Decimal('0.00'),
                'pickup_address': 'г. Минск, ул. Примерная, 123',
                'pickup_hours': 'Пн-Вс: 9:00 - 21:00',
                'is_active': True
            }
        ]
        
        for delivery_data in delivery_methods_data:
            delivery, created = DeliveryMethod.objects.get_or_create(
                name=delivery_data['name'],
                defaults=delivery_data
            )
            if created:
                self.stdout.write(f'Создан способ доставки: {delivery.name}')

        # Создаем способы оплаты
        payment_methods_data = [
            {
                'name': 'Наличными при получении',
                'description': 'Оплата наличными при получении заказа',
                'is_active': True
            },
            {
                'name': 'Банковской картой',
                'description': 'Оплата банковской картой при получении заказа',
                'is_active': True
            }
        ]
        
        for payment_data in payment_methods_data:
            payment, created = PaymentMethod.objects.get_or_create(
                name=payment_data['name'],
                defaults=payment_data
            )
            if created:
                self.stdout.write(f'Создан способ оплаты: {payment.name}')

    def load_csv_data(self):
        """Загружает данные изображений из CSV файла"""
        self.stdout.write('Загрузка данных изображений из CSV...')
        
        csv_path = os.path.join(settings.BASE_DIR, self.csv_file)
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.WARNING(f'CSV файл не найден: {csv_path}'))
            return {}
        
        csv_data = {}
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Очищаем заголовки от BOM
            headers = [h.strip().replace('\ufeff', '') for h in headers]
            
            try:
                id_index = headers.index('ID')
                type_index = headers.index('Тип')
                name_index = headers.index('Имя')
                image_index = headers.index('Изображения')
                price_index = headers.index('Базовая цена') if 'Базовая цена' in headers else None
                promo_price_index = headers.index('Акционная цена') if 'Акционная цена' in headers else None
                category_index = headers.index('Категории') if 'Категории' in headers else None
                desc_index = headers.index('Описание') if 'Описание' in headers else None
                parent_index = headers.index('Родительский') if 'Родительский' in headers else None
            except ValueError as e:
                self.stdout.write(f'Ошибка: не найдена колонка {e}')
                return {}
            
            for row in reader:
                try:
                    product_id = row[id_index] if len(row) > id_index else ''
                    product_type = row[type_index] if len(row) > type_index else ''
                    product_name = row[name_index] if len(row) > name_index else ''
                    image_url = row[image_index].strip() if len(row) > image_index else ''
                    
                    # Пропускаем товары с пустыми или проблемными названиями
                    if not product_name or product_name.strip() == '' or len(product_name.strip()) < 3:
                        continue
                    
                    # Пропускаем товары с "Копировать" в названии
                    if 'копировать' in product_name.lower():
                        continue
                    
                    # Обрабатываем только simple, variable и variation товары
                    if product_type not in ['simple', 'variable', 'variation']:
                        continue
                    
                    # Для обычных товаров требуем изображение, для вариаций - нет
                    if product_type == 'variation' or (image_url and image_url.startswith('http') and any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])):
                        # Извлекаем описания
                        description = row[desc_index] if desc_index and len(row) > desc_index else ''
                        
                        # Очищаем HTML теги из описаний
                        description = self.clean_html(description)
                        
                        # Для вариаций получаем родительский товар
                        parent_id = None
                        if product_type == 'variation' and parent_index and len(row) > parent_index:
                            parent_value = row[parent_index]
                            if parent_value and 'id:' in parent_value:
                                parent_id = parent_value.replace('id:', '')
                        
                            csv_data[product_id] = {
                                'name': product_name,
                                'type': product_type,
                                'image_url': image_url,
                                'price': row[price_index] if price_index and len(row) > price_index else '',
                                'promo_price': row[promo_price_index] if promo_price_index and len(row) > promo_price_index else '',
                                'category': row[category_index] if category_index and len(row) > category_index else '',
                                'description': description,
                                'parent_id': parent_id
                            }
                            
                except Exception as e:
                    continue
        
        self.stdout.write(f'Загружено {len(csv_data)} товаров с изображениями из CSV')
        return csv_data

    def load_products_from_xml(self, csv_data):
        """Загружает товары из XML и соотносит с изображениями из CSV"""
        self.stdout.write('Загрузка товаров из XML...')
        
        # Парсим XML файл
        xml_path = os.path.join(settings.BASE_DIR, self.xml_file)
        
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f'XML файл не найден: {xml_path}')
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Создаем директорию для изображений
        if self.download_images:
            os.makedirs(self.images_dir, exist_ok=True)
        
        created_count = 0
        matched_count = 0
        
        # Находим все элементы item
        for item in root.findall('.//item'):
            try:
                # Проверяем, что это товар
                post_type_elem = item.find('.//{http://wordpress.org/export/1.2/}post_type')
                if post_type_elem is None or post_type_elem.text != 'product':
                    continue
                
                # Извлекаем данные товара
                product_data = self.extract_product_data(item)
                if not product_data:
                    continue
                
                # Ищем соответствующие данные в CSV
                csv_match = self.find_csv_match(product_data, csv_data)
                
                if csv_match:
                    matched_count += 1
                    # Добавляем данные CSV к product_data
                    product_data['csv_match'] = csv_match
                    
                    # Скачиваем изображение если нужно
                    if self.download_images and csv_match['image_url']:
                        image_path = self.download_product_image(csv_match, product_data)
                        if image_path:
                            product_data['image_path'] = image_path
                
                # Создаем товар
                product = self.create_product(product_data)
                if product:
                    created_count += 1
                    if created_count % 50 == 0:
                        self.stdout.write(f'Создано {created_count} товаров...')
                
                if created_count >= self.max_products:
                    break
                    
            except Exception as e:
                self.stdout.write(f'Ошибка при обработке товара: {e}')
                continue
        
        self.stdout.write(f'Создано {created_count} товаров, найдено совпадений с CSV: {matched_count}')
        
        # Загружаем вариации из CSV
        self.load_variations_from_csv(csv_data)

    def load_variations_from_csv(self, csv_data):
        """Загружает вариации товаров из CSV"""
        self.stdout.write('Загрузка вариаций товаров из CSV...')
        
        variations_created = 0
        
        for product_id, csv_item in csv_data.items():
            if csv_item.get('type') == 'variation':
                try:
                    # Создаем товар-вариацию
                    product = self.create_variation_product(csv_item)
                    if product:
                        variations_created += 1
                        if variations_created % 50 == 0:
                            self.stdout.write(f'Создано {variations_created} вариаций...')
                            
                except Exception as e:
                    self.stdout.write(f'Ошибка при создании вариации {csv_item["name"]}: {e}')
                    continue
        
        self.stdout.write(f'Создано {variations_created} вариаций товаров')

    def create_variation_product(self, csv_item):
        """Создает товар-вариацию из CSV данных"""
        try:
            # Создаем slug для вариации
            slug = self.create_slug(csv_item['name'])
            
            # Получаем цену
            price = Decimal('0.00')
            if csv_item.get('price'):
                try:
                    price = Decimal(str(csv_item['price']).replace(',', '.'))
                except (ValueError, TypeError):
                    price = Decimal('0.00')
            
            # Получаем акционную цену
            promo_price = None
            if csv_item.get('promo_price'):
                try:
                    promo_price = Decimal(str(csv_item['promo_price']).replace(',', '.'))
                except (ValueError, TypeError):
                    promo_price = None
            
            # Создаем товар
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': csv_item['name'],
                    'description': csv_item.get('description', ''),
                    'price': price,
                    'promotional_price': promo_price,
                    'is_available': True,
                    'photo': '',  # У вариаций обычно нет отдельного изображения
                    'meta_title': csv_item['name'],
                    'meta_description': f'Купить {csv_item["name"]} в интернет-магазине TopCvetok'
                }
            )
            
            if created:
                # Скачиваем изображение если есть
                if self.download_images and csv_item.get('image_url'):
                    image_path = self.download_image_from_url(csv_item['image_url'], csv_item['name'])
                    if image_path:
                        product.photo = image_path
                        product.save()
                
                # Добавляем категории если есть
                if csv_item.get('category'):
                    categories = self.get_or_create_categories([csv_item['category']])
                    product.categories.set(categories)
            
            return product
            
        except Exception as e:
            self.stdout.write(f'Ошибка при создании товара-вариации: {e}')
            return None

    def extract_product_data(self, item):
        """Извлекает данные товара из XML элемента"""
        try:
            # Основные данные
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else ''
            
            # Пропускаем товары с пустыми или проблемными названиями
            if not title or title.strip() == '' or len(title.strip()) < 3:
                return None
            
            # Пропускаем товары с "Копировать" в названии
            if 'копировать' in title.lower():
                return None
            
            link_elem = item.find('link')
            link = link_elem.text if link_elem is not None else ''
            
            # Извлекаем мета-данные
            meta_data = {}
            for meta in item.findall('.//{http://wordpress.org/export/1.2/}postmeta'):
                key_elem = meta.find('{http://wordpress.org/export/1.2/}meta_key')
                value_elem = meta.find('{http://wordpress.org/export/1.2/}meta_value')
                
                if key_elem is not None and value_elem is not None:
                    key = key_elem.text
                    value = value_elem.text
                    meta_data[key] = value
            
            # Извлекаем цену
            price = self.extract_price(meta_data)
            if not price:
                return None
            
            # Извлекаем категории
            categories = []
            for category in item.findall('category'):
                domain = category.get('domain', '')
                text = category.text if category.text else ''
                
                if domain == 'product_cat' and text:
                    categories.append(text)
            
            # Извлекаем атрибуты
            attributes = []
            for category in item.findall('category'):
                domain = category.get('domain', '')
                text = category.text if category.text else ''
                
                if domain.startswith('pa_') and text:
                    attributes.append({
                        'domain': domain,
                        'value': text
                    })
            
            return {
                'title': title,
                'link': link,
                'price': price,
                'categories': categories,
                'attributes': attributes,
                'meta_data': meta_data
            }
            
        except Exception as e:
            self.stdout.write(f'Ошибка при извлечении данных товара: {e}')
            return None

    def find_csv_match(self, product_data, csv_data):
        """Ищет соответствие товара в CSV данных с улучшенным алгоритмом"""
        product_name = product_data['title']
        
        # Сначала ищем точное совпадение
        for product_id, csv_data_item in csv_data.items():
            if csv_data_item['name'] == product_name:
                return csv_data_item
        
        # Если точного совпадения нет, используем улучшенный алгоритм
        best_match = None
        best_score = 0
        
        for product_id, csv_data_item in csv_data.items():
            similarity = self.calculate_similarity(product_data, csv_data_item)
            
            if similarity >= 0.7 and similarity > best_score:  # Порог схожести
                best_match = csv_data_item
                best_score = similarity
        
        return best_match

    def calculate_similarity(self, xml_item, csv_item):
        """Вычисляет схожесть между XML и CSV товарами"""
        # Схожесть названий
        name_sim = self.calculate_name_similarity(xml_item['title'], csv_item['name'])
        
        # Схожесть цен
        price_sim = self.calculate_price_similarity(xml_item.get('price'), csv_item.get('price'))
        
        # Схожесть категорий
        category_sim = self.calculate_category_similarity(
            xml_item.get('categories', []), 
            csv_item.get('category', '')
        )
        
        # Взвешенная схожесть
        overall_sim = (
            name_sim * 0.6 +      # Название - основной критерий
            price_sim * 0.25 +    # Цена - важный критерий
            category_sim * 0.15   # Категории - дополнительный критерий
        )
        
        return overall_sim

    def calculate_name_similarity(self, name1, name2):
        """Вычисляет схожесть названий (0-1)"""
        if not name1 or not name2:
            return 0
        
        # Нормализуем названия
        norm1 = re.sub(r'[^\w\s]', '', name1.lower().strip())
        norm2 = re.sub(r'[^\w\s]', '', name2.lower().strip())
        
        if norm1 == norm2:
            return 1.0
        
        # Схожесть по словам
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        word_similarity = len(intersection) / len(union) if union else 0
        
        # Схожесть по символам
        from difflib import SequenceMatcher
        char_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Комбинированная схожесть
        combined_similarity = (word_similarity * 0.7 + char_similarity * 0.3)
        
        return combined_similarity

    def calculate_price_similarity(self, price1, price2):
        """Вычисляет схожесть цен (0-1)"""
        if not price1 or not price2:
            return 0
        
        try:
            p1 = float(price1) if isinstance(price1, (int, float, Decimal)) else float(price1)
            p2 = float(price2) if isinstance(price2, (int, float, Decimal)) else float(price2)
            
            if p1 == 0 and p2 == 0:
                return 1.0
            
            if p1 == 0 or p2 == 0:
                return 0
            
            # Относительная разница
            diff = abs(p1 - p2) / max(p1, p2)
            return max(0, 1 - diff)
        except:
            return 0

    def calculate_category_similarity(self, categories1, categories2_str):
        """Вычисляет схожесть категорий (0-1)"""
        if not categories1 or not categories2_str:
            return 0
        
        # Нормализуем категории из XML
        norm_cats1 = set(re.sub(r'[^\w\s]', '', cat.lower().strip()) for cat in categories1)
        
        # Нормализуем категории из CSV
        norm_cats2 = set()
        for cat in categories2_str.split(','):
            cat = cat.strip()
            if '>' in cat:
                # Иерархические категории
                parts = cat.split('>')
                for part in parts:
                    norm_cats2.add(re.sub(r'[^\w\s]', '', part.strip().lower()))
            else:
                norm_cats2.add(re.sub(r'[^\w\s]', '', cat.lower()))
        
        if not norm_cats1 or not norm_cats2:
            return 0
        
        intersection = norm_cats1.intersection(norm_cats2)
        union = norm_cats1.union(norm_cats2)
        
        return len(intersection) / len(union) if union else 0

    def download_product_image(self, csv_match, product_data):
        """Скачивает изображение товара"""
        try:
            image_url = csv_match['image_url']
            product_name = product_data['title']
            
            # Создаем имя файла
            filename = self.create_image_filename(product_name, image_url)
            file_path = os.path.join(self.images_dir, filename)
            
            # Скачиваем изображение
            if self.download_image(image_url, file_path):
                # Возвращаем относительный путь для Django
                return f'downloaded_images/{filename}'
            
        except Exception as e:
            self.stdout.write(f'Ошибка при скачивании изображения: {e}')
        
        return None

    def create_image_filename(self, product_name, image_url):
        """Создает имя файла для изображения"""
        # Извлекаем расширение из URL
        extension = image_url.split('.')[-1].lower()
        if extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            extension = 'jpg'
        
        # Создаем безопасное имя файла
        safe_name = self.create_safe_filename(product_name)
        filename = f'{safe_name}.{extension}'
        
        # Ограничиваем длину
        if len(filename) > 100:
            filename = f'product_{hash(product_name) % 100000}.{extension}'
        
        return filename

    def create_safe_filename(self, text):
        """Создает безопасное имя файла из текста"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        text = text.strip('_')
        
        if len(text) > 50:
            text = text[:50]
        
        return text

    def download_image(self, url, file_path):
        """Скачивает изображение по URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Проверяем, что это изображение
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
            
            # Проверяем размер файла
            if len(response.content) < 1024:
                return False
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Проверяем, что файл корректный
            try:
                with Image.open(file_path) as img:
                    img.verify()
                return True
            except Exception:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return False
            
        except Exception:
            return False

    def create_product(self, product_data):
        """Создает товар в базе данных"""
        try:
            # Создаем slug из названия
            slug = self.create_slug(product_data['title'])
            
            # Получаем описание из CSV если есть совпадение
            description = ''  # По умолчанию пустое описание
            promo_price = None  # По умолчанию нет акционной цены
            
            if 'csv_match' in product_data and product_data['csv_match']:
                csv_desc = product_data['csv_match'].get('description', '')
                csv_promo_price = product_data['csv_match'].get('promo_price', '')
                
                # Используем полное описание, если есть
                if csv_desc:
                    description = csv_desc
                
                # Используем акционную цену, если есть
                if csv_promo_price and csv_promo_price.strip() and csv_promo_price != '0':
                    try:
                        promo_price = Decimal(str(csv_promo_price).replace(',', '.'))
                    except (ValueError, TypeError):
                        promo_price = None
                
            # Создаем товар
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': product_data['title'],
                    'description': description,
                    'price': product_data['price'],
                    'promotional_price': promo_price,
                    'is_available': True,
                    'photo': product_data.get('image_path', ''),
                    'meta_title': product_data['title'],
                    'meta_description': f'Купить {product_data["title"]} в интернет-магазине TopCvetok'
                }
            )
            
            if created:
                # Добавляем категории
                categories = self.get_or_create_categories(product_data['categories'])
                product.categories.set(categories)
                
                # Добавляем атрибуты
                self.add_attributes_to_product(product, product_data['attributes'])
                
                return product
            
        except Exception as e:
            self.stdout.write(f'Ошибка при создании товара {product_data["title"]}: {e}')
        
        return None

    def get_or_create_categories(self, category_names):
        """Создает или получает категории"""
        categories = []
        
        for category_name in category_names:
            slug = self.create_slug(category_name)
            
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': category_name,
                    'description': '',
                    'is_active': True,
                    'display_order': 0
                }
            )
            categories.append(category)
        
        return categories

    def add_attributes_to_product(self, product, attributes_data):
        """Добавляет атрибуты к товару"""
        for attr_data in attributes_data:
            try:
                attribute_type = attr_data['domain'].replace('pa_', '')
                value = attr_data['value']
                slug = self.create_slug(value)
                
                # Определяем модификатор цены для размеров
                price_modifier = 0
                if 'variation' in attr_data['domain'] and 'см' in value:
                    size_match = re.search(r'(\d+)', value)
                    if size_match:
                        size = int(size_match.group(1))
                        price_modifier = max(0, (size - 40) * 0.5)
                
                # Определяем HEX код для цветов
                hex_code = None
                if 'color' in attr_data['domain']:
                    hex_code = self.get_color_hex(value)
                
                attribute, created = Attribute.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'display_name': attribute_type,
                        'value': value,
                        'hex_code': hex_code,
                        'price_modifier': price_modifier,
                        'is_active': True
                    }
                )
                
                product.add_attribute(attribute)
                
            except Exception as e:
                continue

    def extract_price(self, meta_data):
        """Извлекает цену из мета-данных"""
        price_keys = ['_regular_price', '_price', '_sale_price']
        
        for key in price_keys:
            if key in meta_data and meta_data[key]:
                try:
                    price_str = meta_data[key].replace(',', '.')
                    return Decimal(price_str)
                except (ValueError, TypeError):
                    continue
        
        return None

    def create_slug(self, text):
        """Создает slug из текста с транслитерацией"""
        if not text:
            return ''
        
        # Транслитерация русских букв в английские
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        
        # Транслитерация
        result = ''
        for char in text:
            if char in translit_map:
                result += translit_map[char]
            else:
                result += char
        
        # Нормализация
        result = result.lower()
        result = re.sub(r'[^\w\s-]', '', result)
        result = re.sub(r'[-\s]+', '-', result)
        result = result.strip('-')
        
        return result

    def get_color_hex(self, color_name):
        """Возвращает HEX код для цвета"""
        color_map = {
            'красные': '#FF0000',
            'белые': '#FFFFFF',
            'розовые': '#FFC0CB',
            'желтые': '#FFFF00',
            'синие': '#0000FF',
            'зеленые': '#00FF00',
            'кремовые': '#F5F5DC',
            'малиновые': '#DC143C',
            'персиковые': '#FFCCCB',
            'микс': '#FFD700',
            'радужные': '#FFD700',
            'медовые': '#DAA520',
            'нежно-розовые': '#FFC0CB',
            'светло-розовые': '#FFB6C1',
            'бело-розовые': '#FFB6C1',
            'красно-розовые': '#FF1493',
            'бабл гам': '#FF69B4',
        }
        
        return color_map.get(color_name.lower(), None)

    def clean_html(self, text):
        """Очищает HTML теги из текста"""
        if not text:
            return ''
        
        import re
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Заменяем HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
