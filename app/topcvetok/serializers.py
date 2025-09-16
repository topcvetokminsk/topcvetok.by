from django.core.validators import RegexValidator
from rest_framework import serializers
from topcvetok import models

from topcvetok.constants import PHONE_REGEX, NAME_SERVICE_REGEX


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
    )

    class Meta:
        model = models.Account
        fields = ["login", "password"]


class FlowerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FlowerType
        fields = "__all__"


class AttributeTypeSerializer(serializers.ModelSerializer):
    values_count = serializers.SerializerMethodField()
    
    class Meta:
        model = models.AttributeType
        fields = "__all__"
    
    def get_values_count(self, obj):
        return obj.values.filter(is_active=True).count()


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_type_name = serializers.CharField(source='attribute_type.name', read_only=True)
    attribute_type_slug = serializers.CharField(source='attribute_type.slug', read_only=True)
    
    class Meta:
        model = models.AttributeValue
        fields = "__all__"


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)
    attribute_type = AttributeTypeSerializer(read_only=True)
    
    class Meta:
        model = models.Attribute
        fields = "__all__"


class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute_value = AttributeValueSerializer(read_only=True)
    
    class Meta:
        model = models.ProductAttribute
        fields = ["id", "attribute_value"]


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
    
    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'slug', 'categories', 'primary_category', 
            'primary_category_name', 'primary_category_slug', 'price', 'promotional_price',
            'photo', 'is_available', 'meta_title', 'meta_description',
            'created_at', 'updated_at', 'attributes', 'attributes_by_type'
        ]
    
    def get_attributes_by_type(self, obj):
        """Группирует атрибуты по типам для удобства фильтрации"""
        attributes_by_type = {}
        
        for attr in obj.product_attributes.select_related('attribute_value__attribute_type').all():
            attr_type_slug = attr.attribute_value.attribute_type.slug
            if attr_type_slug not in attributes_by_type:
                attributes_by_type[attr_type_slug] = {
                    'type_name': attr.attribute_value.attribute_type.name,
                    'type_slug': attr_type_slug,
                    'values': []
                }
            
            attributes_by_type[attr_type_slug]['values'].append({
                'id': attr.attribute_value.id,
                'value': attr.attribute_value.value,
                'display_name': attr.attribute_value.display_name,
                'hex_code': attr.attribute_value.hex_code,
                'min_value': attr.attribute_value.min_value,
                'max_value': attr.attribute_value.max_value,
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


class FlowerSerializer(serializers.ModelSerializer):
    is_in_stock = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    flower_type = FlowerTypeSerializer(read_only=True)
    attributes = ProductAttributeSerializer(source='productattribute_set', many=True, read_only=True)
    
    class Meta:
        model = models.Flower
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    is_free = serializers.ReadOnlyField()
    display_price = serializers.ReadOnlyField()
    
    class Meta:
        model = models.Service
        fields = "__all__"


class BouquetFlowerSerializer(serializers.ModelSerializer):
    flower = FlowerSerializer(read_only=True)
    
    class Meta:
        model = models.BouquetFlower
        fields = ["flower", "quantity"]


class BouquetSerializer(serializers.ModelSerializer):
    flowers = BouquetFlowerSerializer(source='bouquetflower_set', many=True, read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    attributes = ProductAttributeSerializer(source='productattribute_set', many=True, read_only=True)
    
    class Meta:
        model = models.Bouquet
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = "__all__"


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderStatus
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
    flower = FlowerSerializer(read_only=True)
    bouquet = BouquetSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = models.OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = CustomerSerializer(read_only=True)
    status = OrderStatusSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    delivery_method = DeliveryMethodSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    final_amount = serializers.ReadOnlyField()
    has_valid_consent = serializers.ReadOnlyField()
    can_modify_consent = serializers.SerializerMethodField()
    consent_info = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Order
        fields = "__all__"
    
    def get_can_modify_consent(self, obj):
        """Возвращает, можно ли изменить согласие"""
        return obj.can_modify_consent()
    
    def get_consent_info(self, obj):
        """Возвращает информацию о согласии"""
        return obj.get_consent_info()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказов с обязательным согласием"""
    
    class Meta:
        model = models.Order
        fields = [
            'delivery_address', 'delivery_date', 'delivery_notes',
            'delivery_method', 'payment_method', 'service',
            'customer_name', 'customer_phone', 'customer_email',
            'notes', 'personal_data_consent'
        ]
    
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


class OrderTrackingSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = models.OrderTracking
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = models.Review
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    flower = FlowerSerializer(read_only=True)
    bouquet = BouquetSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = models.CartItem
        fields = "__all__"
    
    def get_price(self, obj):
        return obj.get_price()
    
    def get_total_price(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    customer = CustomerSerializer(read_only=True)
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Cart
        fields = "__all__"
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    
    def get_total_amount(self, obj):
        return obj.get_total_amount()


class RequestNoteSerializer(serializers.Serializer):
    phone = serializers.CharField(
        max_length=16,
        validators=[
            RegexValidator(
                regex=PHONE_REGEX,
                message="Телефон должен быть в международном формате без дефисов и скобок, например +123456789."
            )
        ]
    )
    name = serializers.CharField(
        max_length=100,
        help_text="Имя клиента",
        validators=[
            RegexValidator(
                regex=NAME_SERVICE_REGEX,
                message="Имя может содержать только русские и английские буквы и пробелы."
            )
        ]
    )
    email = serializers.EmailField(
        max_length=200,
        help_text="Email",
        error_messages={'invalid': 'Некорректный email адрес'}
    )
