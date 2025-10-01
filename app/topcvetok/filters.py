import django_filters
from django.db.models import Q
from . import models
from .constants import SIZE_INDICATORS


class ProductFilter(django_filters.FilterSet):
    """Фильтр для продуктов с поддержкой атрибутов"""
    
    # Базовые фильтры
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = django_filters.CharFilter(method='filter_by_category')
    categories = django_filters.CharFilter(method='filter_by_categories')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    is_popular = django_filters.BooleanFilter(field_name='is_popular')
    
    # Фильтры по атрибутам
    color = django_filters.CharFilter(method='filter_by_color')
    quantity = django_filters.CharFilter(method='filter_by_quantity')
    price_range = django_filters.CharFilter(method='filter_by_price_range')
    variation = django_filters.CharFilter(method='filter_by_variation')
    
    # Множественные фильтры по атрибутам
    attributes = django_filters.CharFilter(method='filter_by_attributes')
    
    # Фильтр для основных товаров (без вариаций)
    main_products_only = django_filters.BooleanFilter(method='filter_main_products_only')
    
    class Meta:
        model = models.Product
        fields = ['name', 'categories', 'price_min', 'price_max', 'is_available', 'is_popular', 'color', 'quantity', 'variation', 'price_range', 'attributes']
    
    def filter_by_color(self, queryset, name, value):
        """Фильтр по цвету"""
        if not value:
            return queryset
        
        color_values = models.Attribute.objects.filter(
            Q(name__iexact='цвет') | Q(name__iexact='color')
        ).filter(
            Q(value__icontains=value)
        )
        
        if color_values.exists():
            return queryset.filter(product_attributes__attribute__in=color_values)
        return queryset.none()
    
    def filter_by_quantity(self, queryset, name, value):
        """Фильтр по количеству"""
        if not value:
            return queryset
        
        quantity_values = models.Attribute.objects.filter(
            Q(name__iexact='количество') | Q(name__iexact='quantity')
        ).filter(
            Q(value__icontains=value)
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
    
    # Удалено: иерархии категорий больше нет
    
    def filter_by_categories(self, queryset, name, value):
        """Фильтр по нескольким категориям (через запятую)"""
        if not value:
            return queryset
        
        category_slugs = [slug.strip() for slug in value.split(',')]
        return queryset.filter(categories__slug__in=category_slugs).distinct()
    
    def filter_by_attributes(self, queryset, name, value):
        """Универсальный фильтр по атрибутам
        
        Параметры:
        - value: строка вида "красный,5" или "красный|5" (поиск по value или slug)
        - разделители: запятая (И) или вертикальная черта (ИЛИ)
        """
        if not value:
            return queryset
        
        # Определяем тип логики (И или ИЛИ)
        if '|' in value:
            # ИЛИ - любой из атрибутов
            conditions = Q()
            for attr_value in value.split('|'):
                attr_values = models.Attribute.objects.filter(
                    Q(value__icontains=attr_value.strip())
                )
                if attr_values.exists():
                    conditions |= Q(product_attributes__attribute__in=attr_values)
            return queryset.filter(conditions)
        else:
            # И - все атрибуты должны совпадать
            for attr_value in value.split(','):
                attr_values = models.Attribute.objects.filter(
                    Q(value__icontains=attr_value.strip())
                )
                if attr_values.exists():
                    queryset = queryset.filter(product_attributes__attribute__in=attr_values)
                else:
                    return queryset.none()
            return queryset

    def filter_by_variation(self, queryset, name, value):
        """Фильтр по вариациям (например: длина стебля 40 см, 50 см и т.д.)"""
        if not value:
            return queryset
        variation_values = models.Attribute.objects.filter(
            Q(name__iexact='вариация') | Q(name__iexact='variation')
        ).filter(
            Q(value__icontains=value)
        )
        if variation_values.exists():
            return queryset.filter(product_attributes__attribute__in=variation_values)
        return queryset.none()

    def filter_main_products_only(self, queryset, name, value):
        """Фильтр для показа только основных товаров (без вариаций)"""
        if value:
            # Исключаем товары с размерами в названии
            for size in SIZE_INDICATORS:
                queryset = queryset.exclude(name__icontains=size)
            
            # Также исключаем товары, которые являются вариациями и имеют размер в названии
            queryset = queryset.exclude(
                name__icontains='см',
                product_attributes__attribute__name__in=['variation', 'вариация']
            ).distinct()
        return queryset


class AttributeFilter(django_filters.FilterSet):
    """Фильтр для атрибутов"""
    
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    value = django_filters.CharFilter(field_name='value', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = models.Attribute
        fields = ['name', 'value', 'is_active']


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
                Q(price__isnull=True) | Q(price=0)
            )
        else:
            # Только платные услуги
            return queryset.filter(
                Q(price__isnull=False) & ~Q(price=0)
            )


class CategoryFilter(django_filters.FilterSet):
    """Фильтр для категорий"""
    
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = models.Category
        fields = ['name', 'is_active']


"""
Примечание: ранее присутствовали фильтры для заказов и отзывов, но они не
используются во вьюхах и ссылались на поля, отсутствующие в моделях. Чтобы
избежать ошибок, они удалены. При необходимости добавим согласованные
реализации.
"""
