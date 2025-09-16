from rest_framework import serializers
from topcvetok import models


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


class AttributeTypeSerializer(serializers.ModelSerializer):
    values_count = serializers.SerializerMethodField()
    
    def get_values_count(self, obj):
        return obj.values.filter(is_active=True).count()

    class Meta:
        model = models.AttributeType
        fields = "__all__"


class AttributeSerializer(serializers.ModelSerializer):
    attribute_type_name = serializers.CharField(source='attribute_type.name', read_only=True)
    attribute_type_slug = serializers.CharField(source='attribute_type.slug', read_only=True)
    
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
    primary_category = serializers.SerializerMethodField()
    primary_category_name = serializers.SerializerMethodField()
    primary_category_slug = serializers.SerializerMethodField()
    
    # Все категории
    categories = serializers.SerializerMethodField()
    
    attributes = ProductAttributeSerializer(source='product_attributes', many=True, read_only=True)
    
    # Группированные атрибуты для удобства фронтенда
    attributes_by_type = serializers.SerializerMethodField()
    
    
    def get_attributes_by_type(self, obj):
        """Группирует атрибуты по типам для удобства фильтрации"""
        attributes_by_type = {}
        
        for attr in obj.product_attributes.select_related('attribute__attribute_type').all():
            attr_type_slug = attr.attribute.attribute_type.slug
            if attr_type_slug not in attributes_by_type:
                attributes_by_type[attr_type_slug] = {
                    'type_name': attr.attribute.attribute_type.name,
                    'type_slug': attr_type_slug,
                    'values': []
                }
            
            attributes_by_type[attr_type_slug]['values'].append({
                'id': attr.attribute.id,
                'display_name': attr.attribute.display_name,
                'hex_code': attr.attribute.hex_code,
                'price_modifier': float(attr.attribute.price_modifier),
            })
        
        return attributes_by_type
    
    def get_primary_category(self, obj):
        """Возвращает основную категорию продукта"""
        primary = obj.get_primary_category()
        return primary.id if primary else None
    
    def get_primary_category_name(self, obj):
        """Возвращает название основной категории"""
        primary = obj.get_primary_category()
        return primary.name if primary else None
    
    def get_primary_category_slug(self, obj):
        """Возвращает slug основной категории"""
        primary = obj.get_primary_category()
        return primary.slug if primary else None
    
    def get_categories(self, obj):
        """Возвращает все категории продукта"""
        categories = obj.get_all_categories()
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'level': cat.level,
                'full_path': cat.get_full_path(),
                'full_slug': cat.get_full_slug()
            }
            for cat in categories
        ]
    
    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'slug', 'categories', 'primary_category', 
            'primary_category_name', 'primary_category_slug', 'price', 'promotional_price',
            'photo', 'is_available', 'meta_title', 'meta_description',
            'created_at', 'updated_at', 'attributes', 'attributes_by_type'
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


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказов с обязательным согласием"""
    
    def validate_personal_data_consent(self, value):
        """Валидация согласия на обработку персональных данных"""
        if not value:
            raise serializers.ValidationError(
                "Необходимо дать согласие на обработку персональных данных для создания заказа."
            )
        return value
    
    def validate(self, attrs):
        """Общая валидация заказа"""
        # Проверяем, что согласие дано
        if not attrs.get('personal_data_consent'):
            raise serializers.ValidationError({
                'personal_data_consent': 'Необходимо дать согласие на обработку персональных данных.'
            })
        
        return attrs
    
    class Meta:
        model = models.Order
        fields = [
            'delivery_address', 'delivery_date', 'delivery_notes',
            'delivery_method', 'payment_method', 'service',
            'customer_name', 'customer_phone', 'customer_email',
            'notes', 'personal_data_consent'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в корзине"""
    product = ProductSerializer(read_only=True)
    attributes = AttributeSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    price_with_attributes = serializers.ReadOnlyField()
    
    class Meta:
        model = models.CartItem
        fields = [
            'id', 'product', 'quantity', 'attributes', 
            'total_price', 'price_with_attributes', 'created_at', 'updated_at'
        ]


class CartAddItemSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в корзину"""
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1, default=1)
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


class CartUpdateItemSerializer(serializers.Serializer):
    """Сериализатор для обновления товара в корзине"""
    quantity = serializers.IntegerField(min_value=1)
    attribute_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


class CartCheckoutSerializer(serializers.Serializer):
    """Сериализатор для оформления заказа из корзины"""
    delivery_address = serializers.CharField()
    delivery_method = serializers.CharField()
    payment_method = serializers.CharField()
    service = serializers.CharField()
    customer_name = serializers.CharField()
    customer_phone = serializers.CharField()
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    personal_data_consent = serializers.BooleanField()
    
    def validate_personal_data_consent(self, value):
        """Валидация согласия на обработку персональных данных"""
        if not value:
            raise serializers.ValidationError(
                "Необходимо дать согласие на обработку персональных данных для создания заказа."
            )
        return value
    
    def validate(self, attrs):
        """Общая валидация заказа"""
        # Проверяем, что согласие дано
        if not attrs.get('personal_data_consent'):
            raise serializers.ValidationError({
                'personal_data_consent': 'Необходимо дать согласие на обработку персональных данных.'
            })
        
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = models.Cart
        fields = [
            'id', 'session_key', 'total_items', 'total_amount', 
            'items', 'created_at', 'updated_at'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contact
        fields = "__all__"
