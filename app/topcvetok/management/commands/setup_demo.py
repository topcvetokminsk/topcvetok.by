from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import os


class Command(BaseCommand):
    help = 'Полная настройка демо-данных: создание данных + загрузка из XML + скачивание изображений'

    def add_arguments(self, parser):
        parser.add_argument(
            '--xml-file',
            type=str,
            default='topcvetok_xml.xml',
            help='Путь к XML файлу (относительно директории app)'
        )
        parser.add_argument(
            '--max-products',
            type=int,
            default=1000,
            help='Максимальное количество товаров для загрузки'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустить скачивание изображений'
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Начинаем полную настройку демо-данных...')
        
        try:
            with transaction.atomic():
                # Загружаем товары из XML с соотнесением изображений из CSV
                self.stdout.write('\n📦 Загрузка товаров из XML с изображениями из CSV...')
                xml_file = options['xml_file']
                
                # Проверяем существование файлов
                if not os.path.exists(xml_file):
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  XML файл не найден: {xml_file}')
                    )
                    self.stdout.write('Пропускаем загрузку...')
                else:
                    max_products = options['max_products']
                    download_images = not options.get('skip_images', False)
                    
                    call_command(
                        'load_products_with_images',
                        xml_file=xml_file,
                        max_products=max_products,
                        download_images=download_images
                    )
                    self.stdout.write(self.style.SUCCESS('✅ Товары с изображениями загружены'))
                
                self.stdout.write('\n🎉 Полная настройка демо-данных завершена успешно!')
                self.stdout.write('\n📊 Статистика:')
                self.print_statistics()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при настройке демо-данных: {e}')
            )
            raise

    def print_statistics(self):
        """Выводит статистику созданных данных"""
        from topcvetok.models import Category, Attribute, Product, Service, DeliveryMethod, PaymentMethod
        
        try:
            categories_count = Category.objects.count()
            attributes_count = Attribute.objects.count()
            products_count = Product.objects.count()
            services_count = Service.objects.count()
            delivery_methods_count = DeliveryMethod.objects.count()
            payment_methods_count = PaymentMethod.objects.count()
            
            self.stdout.write(f'📁 Категории: {categories_count}')
            self.stdout.write(f'🏷️ Атрибуты: {attributes_count}')
            self.stdout.write(f'🛍️ Товары: {products_count}')
            self.stdout.write(f'🔧 Услуги: {services_count}')
            self.stdout.write(f'🚚 Способы доставки: {delivery_methods_count}')
            self.stdout.write(f'💳 Способы оплаты: {payment_methods_count}')
            
        except Exception as e:
            self.stdout.write(f'⚠️  Не удалось получить статистику: {e}')
