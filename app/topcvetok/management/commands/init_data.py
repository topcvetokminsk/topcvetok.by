from django.core.management.base import BaseCommand
from django.db import transaction
from topcvetok.models import Category, AttributeType, Attribute, Service, DeliveryMethod, PaymentMethod, Product, Review
from topcvetok.enums import DeliveryType, AttributeFilterType
from decimal import Decimal


class Command(BaseCommand):
    help = 'Инициализирует базовые данные для приложения'


    def handle(self, *args, **options):
        self.stdout.write('Начинаем инициализацию данных...')
        
        try:
            with transaction.atomic():
                # Создаем базовые данные
                self.create_categories()
                self.create_attribute_types()
                self.create_attributes()
                self.create_services()
                self.create_delivery_methods()
                self.create_payment_methods()
                self.create_products()
                self.create_reviews()
                
                self.stdout.write(
                    self.style.SUCCESS('Инициализация данных завершена успешно!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при инициализации: {e}')
            )
            raise


    def create_categories(self):
        """Создает базовые категории"""
        categories_data = [
            {'name': 'Розы', 'slug': 'rozy', 'display_order': 1},
            {'name': 'Тюльпаны', 'slug': 'tyulpany', 'display_order': 2},
            {'name': 'Хризантемы', 'slug': 'khrizantemy', 'display_order': 3},
            {'name': 'Герберы', 'slug': 'gerbery', 'display_order': 4},
            {'name': 'Пионы', 'slug': 'piony', 'display_order': 5},
            {'name': 'Лилии', 'slug': 'lilii', 'display_order': 6},
            {'name': 'Орхидеи', 'slug': 'orkhidei', 'display_order': 7},
            {'name': 'Гвоздики', 'slug': 'gvozdiki', 'display_order': 8},
            {'name': 'Ирисы', 'slug': 'irisy', 'display_order': 9},
            {'name': 'Альстромерии', 'slug': 'alstromerii', 'display_order': 10},
            {'name': 'Антуриумы', 'slug': 'anturiumy', 'display_order': 11},
            {'name': 'Гипсофилы', 'slug': 'gipsofily', 'display_order': 12},
            {'name': 'Эустомы', 'slug': 'eustomy', 'display_order': 13},
            {'name': 'Фрезии', 'slug': 'freziya', 'display_order': 14},
            {'name': 'Смешанные букеты', 'slug': 'smeshannye-bukety', 'display_order': 15},
            {'name': 'Сезонные цветы', 'slug': 'sezonnye-cvety', 'display_order': 16},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Создана категория: {category.name}')

    def create_attribute_types(self):
        """Создает типы атрибутов"""
        attribute_types_data = [
            {
                'name': 'Цвет',
                'slug': 'color',
                'filter_type': AttributeFilterType.COLOR,
                'description': 'Цветовая палитра цветов'
            },
            {
                'name': 'Количество',
                'slug': 'select-size',
                'filter_type': AttributeFilterType.SELECT,
                'description': 'Количество цветов в букете'
            },
            {
                'name': 'По типу',
                'slug': 'po-tipu',
                'filter_type': AttributeFilterType.CHECKBOX,
                'description': 'Тип букета и стиль оформления'
            },
            {
                'name': 'По составу',
                'slug': 'po-sostavu',
                'filter_type': AttributeFilterType.CHECKBOX,
                'description': 'Состав букета по видам цветов'
            },
            {
                'name': 'Вариация',
                'slug': 'variation',
                'filter_type': AttributeFilterType.SELECT,
                'description': 'Размер и длина стеблей'
            },
            {
                'name': 'По цене',
                'slug': 'po-cene',
                'filter_type': AttributeFilterType.RANGE,
                'description': 'Ценовые диапазоны товаров'
            }
        ]
        
        for attr_type_data in attribute_types_data:
            attr_type, created = AttributeType.objects.get_or_create(
                slug=attr_type_data['slug'],
                defaults=attr_type_data
            )
            if created:
                self.stdout.write(f'Создан тип атрибута: {attr_type.name}')

    def create_attributes(self):
        """Создает атрибуты"""
        # Цвета
        colors = [
            {'display_name': 'Бабл гам', 'slug': 'babl-gam', 'hex_code': '#FF69B4', 'price_modifier': 0},
            {'display_name': 'бело-розовые', 'slug': 'belo-rozovye', 'hex_code': '#FFB6C1', 'price_modifier': 0},
            {'display_name': 'Белые', 'slug': 'belye', 'hex_code': '#FFFFFF', 'price_modifier': 0},
            {'display_name': 'Желтые', 'slug': 'zheltye', 'hex_code': '#FFFF00', 'price_modifier': 0},
            {'display_name': 'зеленые', 'slug': 'zelenye', 'hex_code': '#00FF00', 'price_modifier': 0},
            {'display_name': 'Красно-розовые', 'slug': 'krasno-rozovye', 'hex_code': '#FF1493', 'price_modifier': 0},
            {'display_name': 'Красные', 'slug': 'krasnye', 'hex_code': '#FF0000', 'price_modifier': 0},
            {'display_name': 'Кремовые', 'slug': 'kremovye', 'hex_code': '#F5F5DC', 'price_modifier': 0},
            {'display_name': 'Кремовый', 'slug': 'kremovyy', 'hex_code': '#FFF8DC', 'price_modifier': 0},
            {'display_name': 'Малиновые', 'slug': 'malinovye', 'hex_code': '#DC143C', 'price_modifier': 0},
            {'display_name': 'Медовые', 'slug': 'medovye', 'hex_code': '#DAA520', 'price_modifier': 0},
            {'display_name': 'Микс', 'slug': 'miks', 'hex_code': '#FFD700', 'price_modifier': 0},
            {'display_name': 'Нежно-розовые', 'slug': 'nezno-rozovye', 'hex_code': '#FFC0CB', 'price_modifier': 0},
            {'display_name': 'Персиковые', 'slug': 'persikovye', 'hex_code': '#FFCCCB', 'price_modifier': 0},
            {'display_name': 'Персиковый', 'slug': 'persikovyy', 'hex_code': '#FFE4B5', 'price_modifier': 0},
            {'display_name': 'Радужные', 'slug': 'raduzhnye', 'hex_code': '#FFD700', 'price_modifier': 0},
            {'display_name': 'Розовые', 'slug': 'rozovye', 'hex_code': '#FFC0CB', 'price_modifier': 0},
            {'display_name': 'Розовый', 'slug': 'rozovyy', 'hex_code': '#FFB6C1', 'price_modifier': 0},
            {'display_name': 'Светло-розовые', 'slug': 'svetlo-rozovye', 'hex_code': '#FFB6C1', 'price_modifier': 0},
            {'display_name': 'Синие', 'slug': 'sinie', 'hex_code': '#0000FF', 'price_modifier': 0},
        ]
        
        color_type = AttributeType.objects.get(slug='color')
        for color_data in colors:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=color_type,
                slug=color_data['slug'],
                defaults={
                    'display_name': color_data['display_name'],
                    'hex_code': color_data['hex_code'],
                    'price_modifier': color_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

        # Количество (select-size)
        quantities = [
            {'display_name': '1', 'slug': '1', 'price_modifier': 0},
            {'display_name': '101', 'slug': '101', 'price_modifier': 0},
            {'display_name': '101 роза (15 веток)', 'slug': '101-roza-15-vetok', 'price_modifier': 0},
            {'display_name': '101 ромашка (11-13 веток)', 'slug': '101-romashka-11-13-vetok', 'price_modifier': 0},
            {'display_name': '11', 'slug': '11', 'price_modifier': 0},
            {'display_name': '13', 'slug': '13', 'price_modifier': 0},
            {'display_name': '15', 'slug': '15', 'price_modifier': 0},
            {'display_name': '151', 'slug': '151', 'price_modifier': 0},
            {'display_name': '151 ромашка (15-17 веток)', 'slug': '151-romashka-15-17-vetok', 'price_modifier': 0},
            {'display_name': '17', 'slug': '17', 'price_modifier': 0},
            {'display_name': '171 роза (25 веток)', 'slug': '171-roza-25-vetok', 'price_modifier': 0},
            {'display_name': '19', 'slug': '19', 'price_modifier': 0},
            {'display_name': '201', 'slug': '201', 'price_modifier': 0},
            {'display_name': '201 ромашка (21-23 ветки)', 'slug': '201-romashka-21-23-vetki', 'price_modifier': 0},
            {'display_name': '21', 'slug': '21', 'price_modifier': 0},
            {'display_name': '241 роза (35 веток)', 'slug': '241-roza-35-vetok', 'price_modifier': 0},
            {'display_name': '25', 'slug': '25', 'price_modifier': 0},
            {'display_name': '251', 'slug': '251', 'price_modifier': 0},
            {'display_name': '251 ромашка (25-27 веток)', 'slug': '251-romashka-25-27-vetok', 'price_modifier': 0},
            {'display_name': '3', 'slug': '3', 'price_modifier': 0},
            {'display_name': '301', 'slug': '301', 'price_modifier': 0},
            {'display_name': '301 ромашка (31-33 ветки)', 'slug': '301-romashka-31-33-vetki', 'price_modifier': 0},
            {'display_name': '31', 'slug': '31', 'price_modifier': 0},
            {'display_name': '35', 'slug': '35', 'price_modifier': 0},
            {'display_name': '351', 'slug': '351', 'price_modifier': 0},
            {'display_name': '351 роза (51 ветка)', 'slug': '351-roza-51-vetka', 'price_modifier': 0},
            {'display_name': '351 ромашка (35-37 веток)', 'slug': '351-romashka-35-37-vetok', 'price_modifier': 0},
            {'display_name': '401', 'slug': '401', 'price_modifier': 0},
            {'display_name': '401 ромашка (41-43 ветки)', 'slug': '401-romashka-41-43-vetki', 'price_modifier': 0},
            {'display_name': '5', 'slug': '5', 'price_modifier': 0},
            {'display_name': '501', 'slug': '501', 'price_modifier': 0},
            {'display_name': '51', 'slug': '51', 'price_modifier': 0},
            {'display_name': '51 ромашка (5-7 веток)', 'slug': '51-romashka-5-7-vetok', 'price_modifier': 0},
            {'display_name': '7', 'slug': '7', 'price_modifier': 0},
            {'display_name': '707 роза (101 ветка)', 'slug': '707-roza-101-vetka', 'price_modifier': 0},
            {'display_name': '71 роза (11 веток)', 'slug': '71-roza-11-vetok', 'price_modifier': 0},
            {'display_name': '9', 'slug': '9', 'price_modifier': 0},
        ]
        
        quantity_type = AttributeType.objects.get(slug='select-size')
        for qty_data in quantities:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=quantity_type,
                slug=qty_data['slug'],
                defaults={
                    'display_name': qty_data['display_name'],
                    'price_modifier': qty_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

        # По типу (po-tipu)
        types = [
            {'display_name': 'VIP букеты', 'slug': 'vip-bukety', 'price_modifier': 0},
            {'display_name': 'Из игрушек', 'slug': 'iz-igrushek', 'price_modifier': 0},
            {'display_name': 'Крафт', 'slug': 'kraft', 'price_modifier': 0},
            {'display_name': 'Монобукеты', 'slug': 'monobukety', 'price_modifier': 0},
            {'display_name': 'Полевык', 'slug': 'polevyk', 'price_modifier': 0},
            {'display_name': 'Современная флористика', 'slug': 'sovremennaya-floristika', 'price_modifier': 0},
            {'display_name': 'Сухоцветы', 'slug': 'sukhotsvety', 'price_modifier': 0},
        ]
        
        type_attr_type = AttributeType.objects.get(slug='po-tipu')
        for type_data in types:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=type_attr_type,
                slug=type_data['slug'],
                defaults={
                    'display_name': type_data['display_name'],
                    'price_modifier': type_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

        # По составу (po-sostavu)
        compositions = [
            {'display_name': 'c розой', 'slug': 'c-rozoi', 'price_modifier': 0},
            {'display_name': 'с альстромерией', 'slug': 's-alstromeriei', 'price_modifier': 0},
            {'display_name': 'с брунией', 'slug': 's-bruniei', 'price_modifier': 0},
            {'display_name': 'с гвоздикой', 'slug': 's-gvozdikoi', 'price_modifier': 0},
            {'display_name': 'с гербером', 'slug': 's-gerberom', 'price_modifier': 0},
            {'display_name': 'с гипсофилой', 'slug': 's-gipsofilyu', 'price_modifier': 0},
            {'display_name': 'с гортензией', 'slug': 's-gortenziei', 'price_modifier': 0},
            {'display_name': 'с зеленью', 'slug': 's-zelenyu', 'price_modifier': 0},
            {'display_name': 'с кустовой розой', 'slug': 's-kustovoi-rozoi', 'price_modifier': 0},
            {'display_name': 'с лиммониумом', 'slug': 's-limmomiumom', 'price_modifier': 0},
            {'display_name': 'с лимониумом', 'slug': 's-limoniumom', 'price_modifier': 0},
            {'display_name': 'с лимонниумом', 'slug': 's-limoniumom-alt', 'price_modifier': 0},
            {'display_name': 'с маттиолой', 'slug': 's-mattioloi', 'price_modifier': 0},
            {'display_name': 'с пионом', 'slug': 's-pionom', 'price_modifier': 0},
            {'display_name': 'с розой', 'slug': 's-rozoi', 'price_modifier': 0},
            {'display_name': 'с хризантемой', 'slug': 's-khrizantemoi', 'price_modifier': 0},
            {'display_name': 'с эвкалиптом', 'slug': 's-evkaliptom', 'price_modifier': 0},
            {'display_name': 'С эустомой', 'slug': 's-eustomoi', 'price_modifier': 0},
            {'display_name': 'со статицей', 'slug': 'so-statsiei', 'price_modifier': 0},
        ]
        
        composition_type = AttributeType.objects.get(slug='po-sostavu')
        for comp_data in compositions:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=composition_type,
                slug=comp_data['slug'],
                defaults={
                    'display_name': comp_data['display_name'],
                    'price_modifier': comp_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

        # Вариация (variation)
        variations = [
            {'display_name': '100', 'slug': '100', 'price_modifier': 0},
            {'display_name': '100 см', 'slug': '100-sm', 'price_modifier': 30},
            {'display_name': '40 см', 'slug': '40-sm', 'price_modifier': 0},
            {'display_name': '41 см', 'slug': '41-sm', 'price_modifier': 1},
            {'display_name': '42 см', 'slug': '42-sm', 'price_modifier': 2},
            {'display_name': '43 см', 'slug': '43-sm', 'price_modifier': 3},
            {'display_name': '44 см', 'slug': '44-sm', 'price_modifier': 4},
            {'display_name': '45 см', 'slug': '45-sm', 'price_modifier': 5},
            {'display_name': '45-50см', 'slug': '45-50sm', 'price_modifier': 5},
            {'display_name': '50 см', 'slug': '50-sm', 'price_modifier': 5},
            {'display_name': '55-60см', 'slug': '55-60sm', 'price_modifier': 10},
            {'display_name': '60 см', 'slug': '60-sm', 'price_modifier': 10},
            {'display_name': '65-70 см', 'slug': '65-70-sm', 'price_modifier': 15},
            {'display_name': '70 см', 'slug': '70-sm', 'price_modifier': 15},
            {'display_name': '80 мм', 'slug': '80-mm', 'price_modifier': 0},
            {'display_name': '80 см', 'slug': '80-sm', 'price_modifier': 20},
            {'display_name': '90 см', 'slug': '90-sm', 'price_modifier': 25},
        ]
        
        variation_type = AttributeType.objects.get(slug='variation')
        for var_data in variations:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=variation_type,
                slug=var_data['slug'],
                defaults={
                    'display_name': var_data['display_name'],
                    'price_modifier': var_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

        # По цене (po-cene)
        price_ranges = [
            {'display_name': '35-55', 'slug': '35-55', 'price_modifier': 0},
            {'display_name': '40–100 BYN', 'slug': '40-100-byn', 'price_modifier': 0},
            {'display_name': '55-75', 'slug': '55-75', 'price_modifier': 0},
            {'display_name': '75-95', 'slug': '75-95', 'price_modifier': 0},
            {'display_name': '95-115', 'slug': '95-115', 'price_modifier': 0},
            {'display_name': '101–150 BYN', 'slug': '101-150-byn', 'price_modifier': 0},
            {'display_name': '115-135', 'slug': '115-135', 'price_modifier': 0},
            {'display_name': '135-155', 'slug': '135-155', 'price_modifier': 0},
            {'display_name': '151–200 BYN', 'slug': '151-200-byn', 'price_modifier': 0},
            {'display_name': '155-175', 'slug': '155-175', 'price_modifier': 0},
            {'display_name': '201–250 BYN', 'slug': '201-250-byn', 'price_modifier': 0},
            {'display_name': '235-255', 'slug': '235-255', 'price_modifier': 0},
            {'display_name': 'от 251 BYN', 'slug': 'ot-251-byn', 'price_modifier': 0},
            {'display_name': 'С бесплатной доставкой', 'slug': 's-besplatnoy-dostavkoy', 'price_modifier': 0},
        ]
        
        price_type = AttributeType.objects.get(slug='po-cene')
        for price_data in price_ranges:
            attr, created = Attribute.objects.get_or_create(
                attribute_type=price_type,
                slug=price_data['slug'],
                defaults={
                    'display_name': price_data['display_name'],
                    'price_modifier': price_data['price_modifier']
                }
            )
            if created:
                self.stdout.write(f'Создан атрибут: {attr.display_name}')

    def create_services(self):
        """Создает услуги"""
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

    def create_delivery_methods(self):
        """Создает способы доставки"""
        delivery_methods_data = [
            {
                'name': 'Доставка по Минску',
                'description': 'Доставка по городу Минску в течение 2 часов',
                'delivery_type': DeliveryType.MINSK,
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
                'description': 'Доставка по всей Беларуси в течение дня',
                'delivery_type': DeliveryType.BELARUS,
                'base_price': Decimal('0.00'),
                'free_delivery_min_amount': Decimal('500.00'),
                'working_hours_start': '08:00:00',
                'working_hours_end': '18:00:00',
                'low_amount_delivery_price': Decimal('25.00'),
                'low_amount_early_price': Decimal('35.00'),
                'low_amount_late_price': Decimal('35.00'),
                'late_delivery_min_amount': Decimal('300.00'),
                'is_active': True
            },
            {
                'name': 'Самовывоз',
                'description': 'Самовывоз из нашего магазина',
                'delivery_type': DeliveryType.PICKUP,
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

    def create_payment_methods(self):
        """Создает способы оплаты"""
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
            },
        ]
        
        for payment_data in payment_methods_data:
            payment, created = PaymentMethod.objects.get_or_create(
                name=payment_data['name'],
                defaults=payment_data
            )
            if created:
                self.stdout.write(f'Создан способ оплаты: {payment.name}')

    def create_products(self):
        """Создает тестовые продукты"""
        products_data = [
            {
                'name': 'Букет роз "Классика"',
                'slug': 'buket-roz-klassika',
                'description': 'Классический букет из красных роз. Идеально подходит для романтических моментов.',
                'price': Decimal('45.00'),
                'is_available': True,
                'categories': ['rozy'],
                'attributes': ['krasnye', '11', 'monobukety', 's-rozoi', '45-sm']
            },
            {
                'name': 'Букет тюльпанов "Весенний"',
                'slug': 'buket-tyulpanov-vesenniy',
                'description': 'Яркий весенний букет из разноцветных тюльпанов. Символ весны и обновления.',
                'price': Decimal('35.00'),
                'is_available': True,
                'categories': ['tyulpany'],
                'attributes': ['raduzhnye', '15', 'monobukety', 's-zelenyu', '50-sm']
            },
            {
                'name': 'Букет хризантем "Осенний"',
                'slug': 'buket-khrizantem-osennyy',
                'description': 'Теплый осенний букет из хризантем различных оттенков. Создает уютную атмосферу.',
                'price': Decimal('40.00'),
                'is_available': True,
                'categories': ['khrizantemy'],
                'attributes': ['zheltye', '13', 'monobukety', 's-khrizantemoi', '60-sm']
            },
            {
                'name': 'Букет гербер "Солнечный"',
                'slug': 'buket-gerber-solnechnyy',
                'description': 'Яркий и жизнерадостный букет из гербер. Поднимает настроение в любое время года.',
                'price': Decimal('38.00'),
                'is_available': True,
                'categories': ['gerbery'],
                'attributes': ['zheltye', '9', 'monobukety', 's-gerberom', '45-sm']
            },
            {
                'name': 'Букет пионов "Нежность"',
                'slug': 'buket-pionov-nezhnost',
                'description': 'Нежный букет из пионов. Символ роскоши и элегантности.',
                'price': Decimal('65.00'),
                'is_available': True,
                'categories': ['piony'],
                'attributes': ['rozovye', '7', 'vip-bukety', 's-pionom', '70-sm']
            },
            {
                'name': 'Букет лилий "Королевский"',
                'slug': 'buket-liliy-korolevskiy',
                'description': 'Величественный букет из белых лилий. Символ чистоты и благородства.',
                'price': Decimal('55.00'),
                'is_available': True,
                'categories': ['lilii'],
                'attributes': ['belye', '5', 'vip-bukety', 's-zelenyu', '80-sm']
            },
            {
                'name': 'Букет орхидей "Экзотика"',
                'slug': 'buket-orkhidey-ekzotika',
                'description': 'Экзотический букет из орхидей. Редкая красота и изысканность.',
                'price': Decimal('85.00'),
                'is_available': True,
                'categories': ['orkhidei'],
                'attributes': ['sinie', '3', 'vip-bukety', 's-zelenyu', '90-sm']
            },
            {
                'name': 'Букет гвоздик "Праздничный"',
                'slug': 'buket-gvozdik-prazdnichnyy',
                'description': 'Яркий праздничный букет из гвоздик. Идеален для торжественных моментов.',
                'price': Decimal('30.00'),
                'is_available': True,
                'categories': ['gvozdiki'],
                'attributes': ['krasnye', '17', 'monobukety', 's-gvozdikoi', '50-sm']
            },
            {
                'name': 'Смешанный букет "Гармония"',
                'slug': 'smeshannyy-buket-garmoniya',
                'description': 'Гармоничный букет из различных цветов. Создает неповторимую композицию.',
                'price': Decimal('50.00'),
                'is_available': True,
                'categories': ['smeshannye-bukety'],
                'attributes': ['miks', '21', 'sovremennaya-floristika', 's-rozoi', '60-sm']
            },
            {
                'name': 'Букет ирисов "Весенний"',
                'slug': 'buket-irisov-vesenniy',
                'description': 'Нежный весенний букет из ирисов. Символ надежды и веры.',
                'price': Decimal('42.00'),
                'is_available': True,
                'categories': ['irisy'],
                'attributes': ['sinie', '11', 'monobukety', 's-zelenyu', '55-sm']
            },
            {
                'name': 'Букет альстромерий "Тропический"',
                'slug': 'buket-alstromeriy-tropicheskiy',
                'description': 'Яркий тропический букет из альстромерий. Приносит тепло и радость.',
                'price': Decimal('48.00'),
                'is_available': True,
                'categories': ['alstromerii'],
                'attributes': ['raduzhnye', '19', 'sovremennaya-floristika', 's-alstromeriei', '65-sm']
            },
            {
                'name': 'Букет антуриумов "Современный"',
                'slug': 'buket-anturiumov-sovremennyy',
                'description': 'Современный букет из антуриумов. Стильный и элегантный подарок.',
                'price': Decimal('75.00'),
                'is_available': True,
                'categories': ['anturiumy'],
                'attributes': ['krasnye', '5', 'sovremennaya-floristika', 's-zelenyu', '70-sm']
            }
        ]
        
        for product_data in products_data:
            # Получаем категории
            categories = Category.objects.filter(slug__in=product_data['categories'])
            
            # Создаем продукт
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults={
                    'name': product_data['name'],
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'is_available': product_data['is_available']
                }
            )
            
            if created:
                # Добавляем категории
                product.categories.set(categories)
                
                # Получаем и добавляем атрибуты
                attributes = Attribute.objects.filter(slug__in=product_data['attributes'])
                for attr in attributes:
                    product.add_attribute(attr)
                
                self.stdout.write(f'Создан продукт: {product.name}')

    def create_reviews(self):
        """Создает тестовые отзывы"""
        from datetime import datetime, timedelta
        import random
        
        reviews_data = [
            {
                'company': 'Анна Петрова',
                'text': 'Потрясающий букет! Цветы свежие, красиво упакованы. Доставили вовремя. Очень довольна!',
                'stars': 5,
                'answer': 'Спасибо за ваш отзыв! Мы рады, что вам понравился наш сервис.',
                'date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'icon_url': 'https://example.com/avatar1.jpg'
            },
            {
                'company': 'Михаил Иванов',
                'text': 'Хороший сервис, качественные цветы. Рекомендую!',
                'stars': 4,
                'answer': 'Благодарим за отзыв! Будем рады видеть вас снова.',
                'date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'icon_url': 'https://example.com/avatar2.jpg'
            },
            {
                'company': 'Елена Смирнова',
                'text': 'Заказывала букет для мамы на день рождения. Она была в восторге! Спасибо за прекрасную работу.',
                'stars': 5,
                'answer': 'Очень приятно слышать! Мы всегда стараемся сделать наши букеты особенными.',
                'date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'icon_url': 'https://example.com/avatar3.jpg'
            },
            {
                'company': 'Дмитрий Козлов',
                'text': 'Отличное качество цветов и быстрая доставка. Буду заказывать еще!',
                'stars': 5,
                'answer': 'Спасибо за доверие! Ждем ваших новых заказов.',
                'date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'icon_url': 'https://example.com/avatar4.jpg'
            },
            {
                'company': 'Ольга Волкова',
                'text': 'Красивый букет, но доставка была немного задержана. В целом довольна.',
                'stars': 4,
                'answer': 'Спасибо за отзыв! Мы работаем над улучшением логистики.',
                'date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'icon_url': 'https://example.com/avatar5.jpg'
            }
        ]
        
        for review_data in reviews_data:
            review, created = Review.objects.get_or_create(
                company=review_data['company'],
                date=review_data['date'],
                text=review_data['text'],
                defaults=review_data
            )
            if created:
                self.stdout.write(f'Создан отзыв от: {review.company}')
