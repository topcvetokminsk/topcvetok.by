from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from topcvetok.managers import AccountManager
from topcvetok.utils import generate_uuid, LowercaseEmailField
from topcvetok.validators import validate_login, validate_name, validate_phone
from topcvetok.enums import DeliveryType, AttributeFilterType, ReviewRating

from storages.backends.ftp import FTPStorage
from django.conf import settings


fs = FTPStorage(location=settings.FTP_STORAGE_LOCATION)
print(settings.FTP_STORAGE_LOCATION)


class Account(AbstractUser):
    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = []
    username = None

    id = models.CharField(
        default=generate_uuid, primary_key=True, editable=False, max_length=40, verbose_name="GUID аккаунта"
    )
    first_name = models.CharField(max_length=50, verbose_name="Имя", help_text="Имя", validators=[validate_name])
    last_name = models.CharField(max_length=50, verbose_name="Фамилия", help_text="Фамилия", validators=[validate_name])
    middleName = models.CharField(
        verbose_name="Отчество",
        help_text="Отчество",
        max_length=50,
        blank=True,
        null=True,
        validators=[validate_name]
    )
    login = models.CharField(
        verbose_name="Логин",
        max_length=30,
        db_index=True,
        unique=True,
        error_messages={"unique": "Значение логина должно быть уникальным."},
        validators=[validate_login]
    )
    email = LowercaseEmailField(
        verbose_name="Email",
        unique=True,
        error_messages={"unique": "Значение почты должно быть уникальным."},
    )
    phone = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        verbose_name="Телефон",
        validators=[validate_phone]
    )

    objects = AccountManager()

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middleName}"

    @property
    def access_token(self) -> str:
        return str(RefreshToken.for_user(self).access_token)

    @property
    def refresh_token(self) -> str:
        return str(RefreshToken.for_user(self))

    def __str__(self):
        return self.login

    def __repr__(self):
        return f"{self.__class__.__name__} (ID: {self.pk})"

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"
        ordering = ("login",)


class Banner(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id баннера",
        help_text="id баннера"
    )
    title = models.TextField(verbose_name="Заголовок")
    link = models.TextField(blank=True, null=True, verbose_name="Адрес")
    text = models.TextField(verbose_name="Описание")
    photo = models.ImageField(
        storage=fs,
        upload_to="media/banners/",
        help_text="Фото",
        verbose_name="Фото",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"


class Video(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id видео",
        help_text="id видео"
    )
    slug = models.TextField(blank=True, null=True, verbose_name="Адрес")
    video = models.FileField(
        storage=fs,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'mkv'])],
        upload_to="media/videos/",
        help_text="Видео",
        verbose_name="Видео",
        blank=True,
        null=True
    )
    frameBackground = models.ImageField(
        storage=fs,
        upload_to="media/frame_backgrounds/",
        blank=True,
        null=True,
        verbose_name="Для фронта бэкграунд"
    )
    
    def __str__(self):
        return self.slug or f"Video {self.id}"
    
    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видосы"


class Category(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id категории",
        help_text="id категории"
    )
    name = models.TextField(verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительская категория",
        help_text="Выберите родительскую категорию для создания подкатегории"
    )
    slug = models.TextField(blank=True, null=True, verbose_name="Ссылка")
    keyword = models.TextField(blank=True, null=True, verbose_name="Ключевые слова")
    icon = models.ImageField(
        storage=fs,
        upload_to="media/categories/icons",
        help_text="Иконка",
        verbose_name="Иконка",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    @property
    def is_root(self):
        """Проверяет, является ли категория корневой (без родителя)"""
        return self.parent is None

    @property
    def level(self):
        """Возвращает уровень вложенности категории"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level

    def get_ancestors(self):
        """Возвращает всех предков категории"""
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors

    def get_descendants(self):
        """Возвращает всех потомков категории"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_full_path(self):
        """Возвращает полный путь к категории (например: "Цветы > Розы > Красные розы")"""
        path = [self.name]
        for ancestor in reversed(self.get_ancestors()):
            path.insert(0, ancestor.name)
        return " > ".join(path)

    def get_full_slug(self):
        """Возвращает полный slug категории (например: "cveti/rozi/krasnye-rozi")"""
        slugs = [self.slug]
        for ancestor in reversed(self.get_ancestors()):
            slugs.insert(0, ancestor.slug)
        return "/".join(slugs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        unique_together = ('parent', 'slug')


class AttributeType(models.Model):
    """Тип атрибута (например: Цвет, Количество, Ценовой диапазон)"""
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    name = models.CharField(max_length=100, verbose_name="Название типа атрибута")
    slug = models.TextField(blank=True, null=True, verbose_name="URL-адрес")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_filterable = models.BooleanField(default=True, verbose_name="Доступен для фильтрации")
    filter_type = models.CharField(
        max_length=20,
        choices=AttributeFilterType.choices,
        default=AttributeFilterType.CHECKBOX,
        verbose_name="Тип фильтра"
    )


    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Тип атрибута"
        verbose_name_plural = "Типы атрибутов"


class Attribute(models.Model):
    """Значение атрибута (например: Красный, 5 штук, 1000-2000 руб)"""
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    attribute_type = models.ForeignKey(AttributeType, on_delete=models.CASCADE, related_name='values', verbose_name="Тип атрибута")
    slug = models.TextField(blank=True, null=True, verbose_name="URL-адрес")
    display_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Отображаемое название")
    hex_code = models.CharField(max_length=7, blank=True, null=True, verbose_name="HEX код (для цветов)")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Модификатор цены", help_text="Дополнительная стоимость (положительная) или скидка (отрицательная)")
    
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.display_name or self.value
    
    class Meta:
        verbose_name = "Значение атрибута"
        verbose_name_plural = "Значения атрибутов"


class ProductAttribute(models.Model):
    """Связь продукта с атрибутами"""
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_attributes', verbose_name="Продукт")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name="Значение атрибута")
    
    class Meta:
        verbose_name = "Атрибут товара"
        verbose_name_plural = "Атрибуты товаров"
        unique_together = ('product', 'attribute')


class Product(models.Model):
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    slug = models.TextField(blank=True, null=True, verbose_name="URL-адрес")
    categories = models.ManyToManyField(Category, related_name='products', verbose_name="Категории")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена BYN")
    promotional_price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2, verbose_name="Цена BYN акционная")
    photo = models.ImageField(
        storage=fs,
        upload_to="media/flowers/",
        help_text="Фото",
        verbose_name="Фото",
        blank=True,
        null=True
    )
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    
    # SEO поля
    meta_title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Meta Title")
    meta_description = models.TextField(blank=True, null=True, verbose_name="Meta Description")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_all_attributes(self):
        """Получить все атрибуты продукта"""
        return self.product_attributes.select_related('attribute__attribute_type').all()
    
    def add_attribute(self, attribute):
        """Добавить атрибут к товару"""
        ProductAttribute.objects.get_or_create(
            product=self,
            attribute=attribute
        )
    
    def remove_attribute(self, attribute):
        """Удалить атрибут у товара"""
        ProductAttribute.objects.filter(
            product=self,
            attribute=attribute
        ).delete()
    
    def get_attributes_by_type(self, attribute_type_slug):
        """Получить атрибуты определенного типа"""
        return self.product_attributes.filter(
            attribute__attribute_type__slug=attribute_type_slug
        ).select_related('attribute__attribute_type')
    
    def get_attribute_values_by_type(self, attribute_type_slug):
        """Получить значения атрибутов определенного типа"""
        return Attribute.objects.filter(
            attribute_type__slug=attribute_type_slug,
            productattribute__product=self
        ).distinct()
    
    def has_attribute_value(self, attribute):
        """Проверить, есть ли у продукта определенное значение атрибута"""
        return self.product_attributes.filter(attribute=attribute).exists()
    
    def get_primary_category(self):
        """Получить основную категорию (первую в списке)"""
        return self.categories.first()
    
    def get_all_categories(self):
        """Получить все категории продукта"""
        return self.categories.all()
    
    def get_categories_hierarchy(self):
        """Получить иерархию всех категорий продукта"""
        all_categories = []
        for category in self.categories.all():
            # Добавляем саму категорию и всех её предков
            all_categories.extend(category.get_ancestors())
            all_categories.append(category)
        return list(set(all_categories))  # Убираем дубликаты
    
    def get_price_with_attributes(self, selected_attributes):
        """Рассчитать цену продукта с учетом выбранных атрибутов"""
        base_price = self.price
        
        # Если есть акционная цена, используем её как базовую
        if self.promotional_price is not None:
            base_price = self.promotional_price
        
        # Добавляем модификаторы от выбранных атрибутов
        total_modifier = 0
        for attribute in selected_attributes:
            total_modifier += attribute.price_modifier
        
        return base_price + total_modifier
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"


class PaymentMethod(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id способа оплаты",
        help_text="id способа оплаты"
    )
    name = models.CharField(max_length=100, verbose_name="Название способа оплаты")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"


class DeliveryMethod(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id способа доставки",
        help_text="id способа доставки"
    )
    name = models.CharField(max_length=100, verbose_name="Название способа доставки")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    
    # Тип доставки
    delivery_type = models.CharField(
        max_length=20, 
        choices=DeliveryType.choices, 
        default=DeliveryType.MINSK,
        verbose_name="Тип доставки"
    )
    
    # Базовая стоимость (для самовывоза или фиксированная)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Базовая стоимость",
        help_text="Для самовывоза или фиксированная стоимость"
    )
    
    # Условия бесплатной доставки
    free_delivery_min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Минимальная сумма для бесплатной доставки",
        help_text="Сумма заказа для бесплатной доставки (например, 250)"
    )
    
    # Время работы
    working_hours_start = models.TimeField(
        default="08:00",
        verbose_name="Начало рабочего времени",
        help_text="Время начала бесплатной доставки"
    )
    working_hours_end = models.TimeField(
        default="22:00", 
        verbose_name="Конец рабочего времени",
        help_text="Время окончания бесплатной доставки"
    )
    
    # Стоимость для заказов ниже минимальной суммы
    low_amount_delivery_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=12, 
        verbose_name="Стоимость доставки для малых заказов",
        help_text="Доставка при заказе ниже минимальной суммы в рабочее время"
    )
    low_amount_early_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=24, 
        verbose_name="Ранняя доставка для малых заказов"
    )
    low_amount_late_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=24, 
        verbose_name="Поздняя доставка для малых заказов"
    )
    late_delivery_min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Минимальная сумма для поздней доставки",
        help_text="Минимальная сумма заказа для поздней доставки (например, 170)"
    )
    
    # Адрес для самовывоза
    pickup_address = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Адрес самовывоза"
    )
    pickup_hours = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Часы работы самовывоза"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_delivery_price(self, order_amount, delivery_time=None, is_holiday=False):
        """Рассчитывает стоимость доставки на основе условий"""
        # Самовывоз всегда бесплатный
        if self.delivery_type == DeliveryType.PICKUP:
            return 0
        
        # Определяем время доставки
        if delivery_time:
            delivery_hour = delivery_time.hour
            
            # Ранняя доставка (до рабочего времени)
            if delivery_hour < self.working_hours_start.hour:
                if order_amount >= (self.free_delivery_min_amount or 0):
                    return self.early_delivery_price
                else:
                    return self.low_amount_early_price
            
            # Поздняя доставка (после рабочего времени)
            elif delivery_hour >= self.working_hours_end.hour:
                if order_amount >= (self.free_delivery_min_amount or 0):
                    return self.late_delivery_price
                else:
                    # Проверяем минимальную сумму для поздней доставки
                    if (self.late_delivery_min_amount and 
                        order_amount >= self.late_delivery_min_amount):
                        return self.low_amount_late_price
                    else:
                        return self.low_amount_late_price
            
            # Рабочее время
            else:
                if order_amount >= (self.free_delivery_min_amount or 0):
                    return 0  # Бесплатная доставка
                else:
                    return self.low_amount_delivery_price
        
        # Если время не указано, используем базовую логику
        if order_amount >= (self.free_delivery_min_amount or 0):
            return 0  # Бесплатная доставка
        else:
            return self.low_amount_delivery_price
    
    def get_delivery_info(self):
        """Возвращает информацию о доставке"""
        if self.delivery_type == DeliveryType.PICKUP:
            return {
                'type': self.delivery_type,
                'type_display': self.get_delivery_type_display(),
                'address': self.pickup_address,
                'hours': self.pickup_hours,
                'price': 0
            }
        else:
            return {
                'type': self.delivery_type,
                'type_display': self.get_delivery_type_display(),
                'working_hours': f"{self.working_hours_start} - {self.working_hours_end}",
                'free_delivery_min': float(self.free_delivery_min_amount) if self.free_delivery_min_amount else None,
                'prices': {
                    'low_amount': float(self.low_amount_delivery_price),
                    'low_amount_early': float(self.low_amount_early_price),
                    'low_amount_late': float(self.low_amount_late_price)
                }
            }
    
    def __str__(self):
        return f"{self.name} ({self.get_delivery_type_display()})"
    
    class Meta:
        verbose_name = "Способ доставки"
        verbose_name_plural = "Способы доставки"


class Service(models.Model):
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    name = models.CharField(max_length=255, verbose_name="Название услуги")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена BYN")
    
    is_available = models.BooleanField(default=True, verbose_name="Доступна")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_free(self):
        """Проверяет, является ли услуга бесплатной"""
        return self.price is None or self.price == 0
    
    @property
    def display_price(self):
        """Возвращает отображаемую цену"""
        if self.is_free:
            return "Бесплатно"
        return f"{self.price} BYN"
    
    def get_price_display(self):
        """Возвращает цену для отображения в админке"""
        return self.display_price
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Order(models.Model):
    id = models.CharField(default=generate_uuid, primary_key=True, editable=False, max_length=40)
    
    # Информация о доставке
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    delivery_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата доставки")
    delivery_notes = models.TextField(blank=True, null=True, verbose_name="Примечания к доставке")
    delivery_method = models.ForeignKey(DeliveryMethod, on_delete=models.SET_NULL, null=True, verbose_name="Способ доставки")
    
    # Информация об оплате
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, verbose_name="Способ оплаты")

    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, verbose_name="Услуга")

    # Информация о клиенте на момент заказа (для истории)
    customer_name = models.CharField(max_length=255, verbose_name="Имя клиента")
    customer_phone = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        verbose_name="Телефон клиента",
        validators=[validate_phone]
    )
    customer_email = models.EmailField(blank=True, null=True, verbose_name="Email клиента")
    
    # Дополнительная информация
    notes = models.TextField(blank=True, null=True, verbose_name="Примечания к заказу")
    
    # Служебные поля
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP адрес")

    # Согласие на обработку персональных данных
    personal_data_consent = models.BooleanField(default=False, verbose_name="Согласие на обработку персональных данных")
    consent_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата согласия")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая сумма")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def save(self, *args, **kwargs):
        # Если согласие дано и дата согласия не установлена, устанавливаем текущую дату
        if self.personal_data_consent and not self.consent_date:
            self.consent_date = timezone.now()
        
        # Если заказ уже существует, защищаем от изменения согласия
        if self.pk:
            try:
                old_order = Order.objects.get(pk=self.pk)
                # Если согласие уже было дано, не позволяем его отозвать
                if old_order.personal_data_consent and not self.personal_data_consent:
                    self.personal_data_consent = True
                    # Не изменяем дату согласия
                    self.consent_date = old_order.consent_date
            except Order.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Рассчитать общую сумму заказа"""
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = total - self.discount_amount
        self.save()
        return total

    @property
    def final_amount(self):
        """Итоговая сумма с учетом скидок"""
        return self.total_amount - self.discount_amount
    
    @property
    def has_valid_consent(self):
        """Проверяет, есть ли действующее согласие на обработку персональных данных"""
        return self.personal_data_consent and self.consent_date is not None
    
    def can_modify_consent(self):
        """Проверяет, можно ли изменить согласие (только для новых заказов)"""
        return not self.pk or not self.personal_data_consent
    
    def get_consent_info(self):
        """Возвращает информацию о согласии"""
        if self.has_valid_consent:
            return {
                'consent_given': True,
                'consent_date': self.consent_date,
                'can_modify': False
            }
        return {
            'consent_given': False,
            'consent_date': None,
            'can_modify': True
        }
    
    def __str__(self):
        return f"Заказ #{self.order_number} - {self.customer_name}"
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)


class OrderItem(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id заказа",
        help_text="id заказа"
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, default=None, null=True, blank=True, verbose_name="Услуга")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    
    # Атрибуты товара (если выбраны)
    attributes = models.ManyToManyField(Attribute, blank=True, verbose_name="Атрибуты")
    
    # Дополнительные поля для истории
    item_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название товара")
    item_description = models.TextField(blank=True, null=True, verbose_name="Описание товара")

    def __str__(self):
        if self.product:
            return f"{self.product.name} x{self.quantity}"
        elif self.service:
            return f"{self.service.name} x{self.quantity}"
        return f"ID заказа #{self.id}"
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"


class Review(models.Model):
    id = models.CharField(
        default=generate_uuid,
        primary_key=True,
        editable=False,
        max_length=40,
        verbose_name="id отзыва",
        help_text="id отзыва"
    )
    company = models.CharField(
        max_length=255,
        verbose_name="компания",
        help_text="компания"
    )
    text = models.TextField(
        verbose_name="заголовок",
        help_text="заголовок"
    )
    stars = models.PositiveSmallIntegerField(
        choices=ReviewRating.choices,
        verbose_name="оценка",
        help_text="оценка"
    )
    answer = models.TextField(
        null=True,
        blank=True,
        verbose_name="описание отзыва",
        help_text="описание отзыва"
    )
    date = models.DateTimeField(
        verbose_name="дата отзыва",
        help_text="дата отзыва"
    )
    icon_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="адрес иконки",
        help_text="адрес иконки"
    )

    def __str__(self):
        return f"{self.company} ({self.stars} stars)"

    class Meta:
        verbose_name = "Отзывы"
        verbose_name_plural = "Отзыв"
        unique_together = (('company', 'date', 'text'),)


class Contact(models.Model):
    id = models.CharField(
        default=generate_uuid, primary_key=True, editable=False, max_length=40, verbose_name="GUID контакта"
    )
    name = models.CharField(
        max_length=40,
        verbose_name="Название",
        help_text="Название"
    )
    address = models.TextField(
        verbose_name="Адрес",
        help_text="Адрес"
    )
    phone = models.CharField(
        verbose_name="Телефон",
        max_length=13,
        null=True,
        blank=True,
        validators=[validate_phone]
    )
    timeStart = models.TimeField(
        verbose_name="Время начала работы",
        help_text="Время начала работы"
    )
    timeEnd = models.TimeField(
        verbose_name="Время конца работы",
        help_text="Время конца работы"
    )
    email = LowercaseEmailField(
        verbose_name="Почта",
        error_messages={"unique": "Значение почты должно быть уникальным."},
    )
    instLink = models.CharField(
        verbose_name="Ссылка на inst",
        help_text="Ссылка на inst",
        max_length=128,
        blank=True,
        null=True
    )
    vkLink = models.CharField(
        verbose_name="Ссылка на vk",
        help_text="Ссылка на vk",
        max_length=128,
        blank=True,
        null=True
    )
    tgLink = models.CharField(
        verbose_name="Ссылка на tg",
        help_text="Ссылка на tg",
        max_length=128,
        blank=True,
        null=True
    )
    fbLink = models.CharField(
        verbose_name="Ссылка на fb",
        help_text="Ссылка на fb",
        max_length=128,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Контакты"
        verbose_name_plural = "Контакт"
