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
    help = 'Загружает товары из CSV с изображениями, атрибутами и категориями'

    def add_arguments(self, parser):
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
                
                # 3. Загружаем товары из CSV (основные товары)
                self.load_products_from_csv(csv_data)
                
                # 4. Загружаем вариации из CSV
                self.load_variations_from_csv(csv_data)
                
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
                    
                    # Загружаем все товары (с изображением или без)
                    if True:  # Загружаем все товары
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
                        
                        # Извлекаем атрибуты
                        attributes = []
                        for i in range(1, 4):  # 3 атрибута
                            attr_name_index = headers.index(f'Название атрибута {i}') if f'Название атрибута {i}' in headers else None
                            attr_value_index = headers.index(f'Значения атрибутов {i}') if f'Значения атрибутов {i}' in headers else None
                            
                            if attr_name_index and attr_value_index and len(row) > attr_name_index and len(row) > attr_value_index:
                                attr_name = row[attr_name_index] if row[attr_name_index] else ''
                                attr_values = row[attr_value_index] if row[attr_value_index] else ''
                                
                                if attr_name and attr_values:
                                    attributes.append({
                                        'name': attr_name,
                                        'values': attr_values
                                    })
                        
                        csv_data[product_id] = {
                            'name': product_name,
                            'type': product_type,
                            'image_url': image_url,
                            'price': row[price_index] if price_index and len(row) > price_index else '',
                            'promo_price': row[promo_price_index] if promo_price_index and len(row) > promo_price_index else '',
                            'category': row[category_index] if category_index and len(row) > category_index else '',
                            'description': description,
                            'parent_id': parent_id,
                            'attributes': attributes
                        }
                            
                except Exception as e:
                    continue
        
        self.stdout.write(f'Загружено {len(csv_data)} товаров с изображениями из CSV')
        return csv_data


    def load_products_from_csv(self, csv_data):
        """Загружает основные товары из CSV"""
        self.stdout.write('Загрузка основных товаров из CSV...')
        
        products_created = 0
        
        for product_id, csv_item in csv_data.items():
            # Загружаем только основные товары (simple, variable, grouped, external)
            if csv_item.get('type') not in ['variation']:
                try:
                    # Создаем товар
                    product = self.create_product_from_csv(csv_item)
                    if product:
                        products_created += 1
                        if products_created % 50 == 0:
                            self.stdout.write(f'Создано {products_created} товаров...')
                            
                except Exception as e:
                    self.stdout.write(f'Ошибка при создании товара {csv_item["name"]}: {e}')
                    continue
        
        self.stdout.write(f'Создано {products_created} основных товаров')

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

    def create_product_from_csv(self, csv_item):
        """Создает основной товар из CSV данных"""
        try:
            # Создаем slug для товара
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
                    'photo': '',  # Будет заполнено при скачивании изображения
                    'meta_title': csv_item['name'],
                    'meta_description': f'Купить {csv_item["name"]} в интернет-магазине TopCvetok'
                }
            )
            
            if created:
                # Скачиваем изображение если есть
                if self.download_images and csv_item.get('image_url'):
                    image_path = self.download_product_image(csv_item, {'title': csv_item['name']})
                    if image_path:
                        product.photo = image_path
                        product.save()
                
                # Добавляем категории если есть
                if csv_item.get('category'):
                    # Разбиваем категории по запятым
                    category_list = [cat.strip() for cat in csv_item['category'].split(',')]
                    categories = self.get_or_create_categories(category_list)
                    product.categories.set(categories)
                
                # Добавляем атрибуты если есть
                if csv_item.get('attributes'):
                    self.add_csv_attributes_to_product(product, csv_item['attributes'])
            
            return product
            
        except Exception as e:
            self.stdout.write(f'Ошибка при создании товара: {e}')
            return None

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
                    image_path = self.download_product_image(csv_item, {'title': csv_item['name']})
                    if image_path:
                        product.photo = image_path
                        product.save()
                
                # Добавляем категории если есть
                if csv_item.get('category'):
                    # Разбиваем категории по запятым
                    category_list = [cat.strip() for cat in csv_item['category'].split(',')]
                    categories = self.get_or_create_categories(category_list)
                    product.categories.set(categories)
            
            return product
            
        except Exception as e:
            self.stdout.write(f'Ошибка при создании товара-вариации: {e}')
            return None



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
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
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


    def get_or_create_categories(self, category_names):
        """Создает или получает категории с поддержкой иерархии"""
        categories = []
        
        for category_name in category_names:
            # Обрабатываем иерархические категории
            if '>' in category_name:
                # Разбиваем по символу >
                category_parts = [part.strip() for part in category_name.split('>')]
                
                # Создаем категории по уровням иерархии
                parent_category = None
                for i, part in enumerate(category_parts):
                    slug = self.create_slug(part)
                    
                    category, created = Category.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'name': part,
                            'description': '',
                            'is_active': True,
                            'display_order': i,
                            'parent': parent_category
                        }
                    )
                    
                    # Если категория уже существовала, обновляем родителя
                    if not created and category.parent != parent_category:
                        category.parent = parent_category
                        category.save()
                    
                    parent_category = category
                    categories.append(category)
            else:
                # Обычная категория без иерархии
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

    def add_csv_attributes_to_product(self, product, attributes_data):
        """Добавляет атрибуты к товару из CSV данных"""
        for attr_data in attributes_data:
            try:
                attribute_name = attr_data['name']
                attribute_values = attr_data['values']
                
                # Создаем slug для атрибута
                slug = self.create_slug(attribute_name)
                
                # Разбиваем значения по запятым
                values = [v.strip() for v in attribute_values.split(',')]
                
                # Создаем атрибут для каждого значения
                for value in values:
                    if value:
                        # Создаем атрибут с конкретным значением
                        value_slug = f'{slug}_{self.create_slug(value)}'
                        attribute, created = Attribute.objects.get_or_create(
                            slug=value_slug,
                            defaults={
                                'display_name': f'{attribute_name}',
                                'value': value,
                                'is_active': True
                            }
                        )
                        
                        # Создаем связь товар-атрибут
                        ProductAttribute.objects.get_or_create(
                            product=product,
                            attribute=attribute
                        )
                        
            except Exception as e:
                self.stdout.write(f'Ошибка при добавлении атрибута {attr_data}: {e}')
                continue

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
