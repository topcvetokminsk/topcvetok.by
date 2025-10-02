from rest_framework import serializers
from django.db.models import Q
import re
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
    categories = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    is_main_product = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()
    
    def get_is_main_product(self, obj):
        """Теперь все записи в этом сериализаторе — корневые товары."""
        return True
    
    def get_variations(self, obj):
        """Возвращает вариации через self-FK.

        Для основного товара (parent is None) — его дети.
        Для варианта — его братья (другие дети того же родителя).
        """
        qs = obj.variants.filter(is_available=True)

        def extract_variation_value(variant):
            # 1) Ищем атрибут вариации у варианта
            var_attr = variant.variant_attributes.select_related('attribute').filter(
                Q(attribute__name__iexact='variation') | Q(attribute__name__iexact='вариация')
            ).first()
            if var_attr and var_attr.attribute:
                return var_attr.attribute.name, var_attr.attribute.value
            # 2) Фолбэк: у родителя могли остаться атрибуты вариаций
            parent_var = obj.product_attributes.select_related('attribute').filter(
                Q(attribute__name__iexact='variation') | Q(attribute__name__iexact='вариация')
            ).first()
            if parent_var and parent_var.attribute:
                return parent_var.attribute.name, parent_var.attribute.value
            # 3) Фолбэк по названию
            match = re.search(r"-\s*(\d+\s*(см|мм))", obj.name, re.IGNORECASE)
            if match:
                return 'Вариация', match.group(1)
            return 'variation', ''

        result = []
        for v in qs:
            var_name, var_value = extract_variation_value(v)
            result.append({
                'id': v.id,
                'name': var_name,
                'value': var_value,
                'price': float(v.promotional_price if v.promotional_price is not None else v.price),
                'promotional_price': float(v.promotional_price) if v.promotional_price else 0.0,
            })
        return result

    def get_attributes(self, obj):
        """Возвращает атрибуты продукта без вариативных значений (не дублируем variations)."""
        qs = obj.product_attributes.select_related('attribute').exclude(
            attribute__name__iexact='variation'
        ).exclude(
            attribute__name__iexact='вариация'
        )
        return ProductAttributeSerializer(qs, many=True, context=self.context).data
    
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

    # Больше не требуется логика с base_name/эвристиками по имени
    
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
        """Возвращает категории продукта (вариации их не имеют)."""
        categories_qs = obj.get_all_categories()
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
            }
            for cat in categories_qs
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
    """Сериализатор позиции заказа"""
    product_id = serializers.CharField()
    variant_id = serializers.CharField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    attribute_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

    def validate_product_id(self, value):
        try:
            models.Product.objects.get(id=value, is_available=True)
            return value
        except models.Product.DoesNotExist:
            raise serializers.ValidationError("Продукт не найден или недоступен")

    def validate_variant_id(self, value):
        if value in (None, ""):
            return value
        try:
            models.ProductVariant.objects.get(id=value, is_available=True)
            return value
        except models.ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Вариация не найдена или недоступна")

    def validate_attribute_ids(self, value):
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
