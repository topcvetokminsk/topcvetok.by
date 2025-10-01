from rest_framework import serializers
from django.core.cache import cache
from topcvetok import models
from topcvetok.constants import SIZE_INDICATORS


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
    )

    class Meta:
        model = models.Account
        fields = ["login", "password"]


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Banner
        fields = "__all__"


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Video
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = "__all__"


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attribute
        fields = "__all__"


class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer(read_only=True)
    
    class Meta:
        model = models.ProductAttribute
        fields = ["id", "attribute"]


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов с атрибутами"""
    # Основная категория (для обратной совместимости)
    # Все категории
    categories = serializers.SerializerMethodField()
    
    attributes = ProductAttributeSerializer(source='product_attributes', many=True, read_only=True)
    
    # Группированные атрибуты для удобства фронтенда
    #attributes_by_type = serializers.SerializerMethodField()
    
    # Поля для определения типа товара
    is_main_product = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()
    #available_sizes = serializers.SerializerMethodField()
    
    def get_is_main_product(self, obj):
        """Определяет, является ли товар основным (не вариацией)"""
        # Товар считается основным, если у него есть атрибут 'variation' с размерами
        has_variation_attr = obj.product_attributes.filter(
            attribute__name__in=['variation', 'вариация']
        ).exists()
        
        # Или если в названии нет размера (для товаров без атрибутов)
        has_size_in_name = any(size in obj.name for size in SIZE_INDICATORS)
        
        return has_variation_attr or not has_size_in_name
    
    def get_variations(self, obj):
        """Возвращает вариации этого товара в требуемом формате"""
        if not self.get_is_main_product(obj):
            return []
        
        # Ищем товары с тем же базовым названием, но с размерами
        base_name = self.get_base_name(obj)
        variations = models.Product.objects.filter(
            name__startswith=base_name
        ).exclude(id=obj.id).exclude(name=base_name)

        def extract_variation_value(product):
            # Пытаемся взять значение из атрибута 'variation'/'вариация'
            var_attr = product.product_attributes.select_related('attribute').filter(
                attribute__name__in=['variation', 'вариация']
            ).first()
            if var_attr and var_attr.attribute:
                return var_attr.attribute.name, var_attr.attribute.value
            # Фолбэк: вытаскиваем размер из имени
            for size in SIZE_INDICATORS:
                if size in product.name:
                    return 'variation', size
            return 'variation', ''

        result = []
        for v in variations:
            var_name, var_value = extract_variation_value(v)
            result.append({
                'id': v.id,
                'name': var_name,
                'value': var_value,
                'price': float(v.price),
                'promotional_price': float(v.promotional_price) if v.promotional_price else 0.0,
            })
        return result
    
#    def get_available_sizes(self, obj):
#        """Возвращает доступные размеры для основного товара"""
#        if not self.get_is_main_product(obj):
#            return []
        
#        # Получаем размеры из атрибутов
#        sizes = []
#        for attr in obj.product_attributes.filter(attribute__name__in=['variation', 'вариация']):
#            sizes.append(attr.attribute.value)
        
        # Если атрибутов нет, ищем размеры в вариациях
#        if not sizes:
#            base_name = self.get_base_name(obj)
#            variations = models.Product.objects.filter(
#                name__startswith=base_name
#            ).exclude(id=obj.id).exclude(name=base_name)
            
#            for variation in variations:
#                # Извлекаем размер из названия
#                for size in SIZE_INDICATORS:#
#                    if size in variation.name:
#                        sizes.append(size)
#                        break
        
#        return sorted(list(set(sizes)))

    def get_base_name(self, obj):
        """Возвращает базовое название товара без размера"""
        name = obj.name
        # Убираем размеры из названия
        size_indicators = ['40 см', '50 см', '60 см', '70 см', '80 см', '90 см', '100 см']
        for size in size_indicators:
            name = name.replace(f' - {size}', '').replace(f' {size}', '')
        return name.strip()
    
    def get_attributes_by_type(self, obj):
        """Группирует атрибуты по типам для удобства фильтрации"""
        attributes_by_type = {}
        
        for attr in obj.product_attributes.select_related('attribute').all():
            # Группируем по name (типу атрибута: цвет, количество, тип и т.д.)
            attr_type_name = attr.attribute.name
            if attr_type_name not in attributes_by_type:
                attributes_by_type[attr_type_name] = {
                    'type_name': attr_type_name,
                    'values': []
                }
            
            attributes_by_type[attr_type_name]['values'].append({
                'id': attr.attribute.id,
                'value': attr.attribute.value,
            })
        
        return attributes_by_type
    
    def get_categories(self, obj):
        """Возвращает все категории продукта"""
        categories = obj.get_all_categories()
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
            }
            for cat in categories
        ]
    
    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'slug', 'categories', 'price', 'promotional_price',
            'photo', 'is_available', 'is_popular',
            'meta_title', 'meta_description', 'created_at', 'updated_at', 
            'attributes', 'is_main_product',
            'variations'
        ]


class ServiceSerializer(serializers.ModelSerializer):
    is_free = serializers.ReadOnlyField()
    display_price = serializers.ReadOnlyField()
    
    class Meta:
        model = models.Service
        fields = "__all__"


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaymentMethod
        fields = "__all__"


class DeliveryMethodSerializer(serializers.ModelSerializer):
    delivery_type_display = serializers.CharField(source='get_delivery_type_display', read_only=True)
    delivery_info = serializers.SerializerMethodField()
    
    def get_delivery_info(self, obj):
        return obj.get_delivery_info()
    
    class Meta:
        model = models.DeliveryMethod
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    delivery_method = DeliveryMethodSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    final_amount = serializers.ReadOnlyField()
    has_valid_consent = serializers.ReadOnlyField()
    can_modify_consent = serializers.SerializerMethodField()
    consent_info = serializers.SerializerMethodField()
    
    def get_can_modify_consent(self, obj):
        """Возвращает, можно ли изменить согласие"""
        return obj.can_modify_consent()
    
    def get_consent_info(self, obj):
        """Возвращает информацию о согласии"""
        return obj.get_consent_info()
    
    class Meta:
        model = models.Order
        fields = "__all__"


class OrderItemCreateSerializer(serializers.Serializer):
    """Сериализатор для товара в заказе"""
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    attribute_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    
    def validate_product_id(self, value):
        """Проверяем, что продукт существует и доступен"""
        try:
            product = models.Product.objects.get(id=value, is_available=True)
            return value
        except models.Product.DoesNotExist:
            raise serializers.ValidationError("Продукт не найден или недоступен")
    
    def validate_attribute_ids(self, value):
        """Проверяем, что атрибуты существуют"""
        if value:
            existing_attrs = models.Attribute.objects.filter(
                id__in=value, is_active=True
            ).values_list('id', flat=True)
            
            if len(existing_attrs) != len(value):
                raise serializers.ValidationError("Некоторые атрибуты не найдены")
        
        return value


class OrderCreateSerializer(serializers.Serializer):
    """Сериализатор для создания заказа с товарами"""
    # Информация о доставке
    delivery_address = serializers.CharField()
    delivery_date = serializers.DateTimeField(required=False, allow_null=True)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)
    delivery_method = serializers.CharField()
    
    # Информация об оплате
    payment_method = serializers.CharField()
    
    # Информация о клиенте
    customer_name = serializers.CharField()
    customer_phone = serializers.CharField()
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    
    # Дополнительная информация
    notes = serializers.CharField(required=False, allow_blank=True)
    service = serializers.CharField(required=False, allow_blank=True)
    
    # Согласие на обработку персональных данных
    personal_data_consent = serializers.BooleanField()
    
    # Товары в заказе
    items = OrderItemCreateSerializer(many=True)
    
    def validate_personal_data_consent(self, value):
        """Валидация согласия на обработку персональных данных"""
        if not value:
            raise serializers.ValidationError(
                "Необходимо дать согласие на обработку персональных данных для создания заказа."
            )
        return value
    
    def validate_items(self, value):
        """Проверяем, что есть товары в заказе"""
        if not value:
            raise serializers.ValidationError("Заказ должен содержать хотя бы один товар")
        return value
    
    def validate_delivery_method(self, value):
        """Проверяем способ доставки"""
        try:
            delivery_method = models.DeliveryMethod.objects.get(id=value, is_active=True)
            return value
        except models.DeliveryMethod.DoesNotExist:
            raise serializers.ValidationError("Способ доставки не найден или недоступен")
    
    def validate_payment_method(self, value):
        """Проверяем способ оплаты"""
        try:
            payment_method = models.PaymentMethod.objects.get(id=value, is_active=True)
            return value
        except models.PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Способ оплаты не найден или недоступен")
    
    def validate_service(self, value):
        """Проверяем услугу (если указана)"""
        if value:
            try:
                service = models.Service.objects.get(id=value, is_available=True)
                return value
            except models.Service.DoesNotExist:
                raise serializers.ValidationError("Услуга не найдена или недоступна")
        return value




class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contact
        fields = "__all__"
