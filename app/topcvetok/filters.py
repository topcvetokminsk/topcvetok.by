import django_filters
from django.db.models import Q
from . import models


class ProductFilter(django_filters.FilterSet):
    """Фильтр для продуктов с поддержкой атрибутов"""
    
    # Базовые фильтры
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = django_filters.CharFilter(method='filter_by_category')
    category_parent = django_filters.CharFilter(method='filter_by_category_parent')
    categories = django_filters.CharFilter(method='filter_by_categories')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    
    # Фильтры по атрибутам
    color = django_filters.CharFilter(method='filter_by_color')
    quantity = django_filters.CharFilter(method='filter_by_quantity')
    price_range = django_filters.CharFilter(method='filter_by_price_range')
    
    # Множественные фильтры по атрибутам
    attributes = django_filters.CharFilter(method='filter_by_attributes')
    
    class Meta:
        model = models.Product
        fields = ['name', 'categories', 'price_min', 'price_max', 'is_available', 'color', 'quantity', 'price_range', 'attributes']
    
    def filter_by_color(self, queryset, name, value):
        """Фильтр по цвету"""
        if not value:
            return queryset
        
        # Поддерживаем как slug, так и display_name
        color_values = models.Attribute.objects.filter(
            attribute_type__slug='color'
        ).filter(
            Q(display_name__icontains=value)
        )
        
        if color_values.exists():
            return queryset.filter(product_attributes__attribute__in=color_values)
        return queryset.none()
    
    def filter_by_quantity(self, queryset, name, value):
        """Фильтр по количеству"""
        if not value:
            return queryset
        
        quantity_values = models.Attribute.objects.filter(
            attribute_type__slug='quantity',
            display_name__icontains=value
        )
        
        if quantity_values.exists():
            return queryset.filter(product_attributes__attribute__in=quantity_values)
        return queryset.none()
    
    def filter_by_price_range(self, queryset, name, value):
        """Фильтр по ценовому диапазону"""
        if not value:
            return queryset
        
        # Парсим диапазон цен из строки вида "100-500" или "100+"
        try:
            if '-' in value:
                min_price, max_price = value.split('-', 1)
                min_price = float(min_price.strip())
                max_price = float(max_price.strip())
                return queryset.filter(price__gte=min_price, price__lte=max_price)
            elif value.endswith('+'):
                min_price = float(value[:-1].strip())
                return queryset.filter(price__gte=min_price)
            else:
                # Точное значение
                exact_price = float(value.strip())
                return queryset.filter(price=exact_price)
        except (ValueError, AttributeError):
            return queryset.none()
    
    def filter_by_category(self, queryset, name, value):
        """Фильтр по категории (по slug)"""
        if not value:
            return queryset
        
        return queryset.filter(categories__slug=value).distinct()
    
    def filter_by_category_parent(self, queryset, name, value):
        """Фильтр по родительской категории"""
        if not value:
            return queryset
        
        return queryset.filter(categories__parent__slug=value).distinct()
    
    def filter_by_categories(self, queryset, name, value):
        """Фильтр по нескольким категориям (через запятую)"""
        if not value:
            return queryset
        
        category_slugs = [slug.strip() for slug in value.split(',')]
        return queryset.filter(categories__slug__in=category_slugs).distinct()
    
    def filter_by_attributes(self, queryset, name, value):
        """Универсальный фильтр по атрибутам
        
        Параметры:
        - value: строка вида "color:red,quantity:5" или "color:red|quantity:5"
        - разделители: запятая (И) или вертикальная черта (ИЛИ)
        """
        if not value:
            return queryset
        
        # Определяем тип логики (И или ИЛИ)
        if '|' in value:
            # ИЛИ - любой из атрибутов
            conditions = Q()
            for attr_pair in value.split('|'):
                if ':' in attr_pair:
                    attr_type, attr_value = attr_pair.split(':', 1)
                    attr_values = models.Attribute.objects.filter(
                        attribute_type__slug=attr_type,
                        display_name__icontains=attr_value
                    )
                    if attr_values.exists():
                        conditions |= Q(product_attributes__attribute__in=attr_values)
            return queryset.filter(conditions)
        else:
            # И - все атрибуты должны совпадать
            for attr_pair in value.split(','):
                if ':' in attr_pair:
                    attr_type, attr_value = attr_pair.split(':', 1)
                    attr_values = models.Attribute.objects.filter(
                        attribute_type__slug=attr_type,
                        display_name__icontains=attr_value
                    )
                    if attr_values.exists():
                        queryset = queryset.filter(product_attributes__attribute__in=attr_values)
                    else:
                        return queryset.none()
            return queryset


class AttributeFilter(django_filters.FilterSet):
    """Фильтр для атрибутов"""
    
    attribute_type = django_filters.CharFilter(field_name='attribute_type__slug')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = models.Attribute
        fields = ['attribute_type', 'is_active']


class AttributeTypeFilter(django_filters.FilterSet):
    """Фильтр для типов атрибутов"""
    
    is_filterable = django_filters.BooleanFilter(field_name='is_filterable')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = models.AttributeType
        fields = ['is_filterable', 'is_active']


class ServiceFilter(django_filters.FilterSet):
    """Фильтр для услуг"""
    
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    is_free = django_filters.BooleanFilter(method='filter_free_services')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    class Meta:
        model = models.Service
        fields = ['name', 'is_available', 'is_free', 'price_min', 'price_max']
    
    def filter_free_services(self, queryset, name, value):
        """Фильтр по бесплатным услугам"""
        if value is None:
            return queryset
        
        if value:
            # Только бесплатные услуги
            return queryset.filter(
                models.Q(price__isnull=True) | models.Q(price=0)
            )
        else:
            # Только платные услуги
            return queryset.filter(
                models.Q(price__isnull=False) & ~models.Q(price=0)
            )


class CategoryFilter(django_filters.FilterSet):
    """Фильтр для категорий"""
    
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    parent = django_filters.CharFilter(field_name='parent__slug')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = models.Category
        fields = ['name', 'parent', 'is_active']


class OrderFilter(django_filters.FilterSet):
    """Фильтр для заказов"""
    
    order_number = django_filters.CharFilter(field_name='order_number', lookup_expr='icontains')
    customer_name = django_filters.CharFilter(field_name='customer_name', lookup_expr='icontains')
    customer_phone = django_filters.CharFilter(field_name='customer_phone', lookup_expr='icontains')
    delivery_address = django_filters.CharFilter(field_name='delivery_address', lookup_expr='icontains')
    payment_method = django_filters.CharFilter(field_name='payment_method__id')
    delivery_method = django_filters.CharFilter(field_name='delivery_method__id')
    service = django_filters.CharFilter(field_name='service__id')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = models.Order
        fields = ['order_number', 'customer_name', 'customer_phone', 'delivery_address', 
                 'payment_method', 'delivery_method', 'service', 'created_at_after', 'created_at_before']


class ReviewFilter(django_filters.FilterSet):
    """Фильтр для отзывов"""
    
    customer_name = django_filters.CharFilter(field_name='customer_name', lookup_expr='icontains')
    rating = django_filters.NumberFilter(field_name='rating')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = models.Review
        fields = ['customer_name', 'rating', 'created_at_after', 'created_at_before']
