import django_filters
from django.db.models import Q
from . import models


class ProductFilter(django_filters.FilterSet):
    """Фильтр для продуктов с поддержкой атрибутов"""
    
    # Базовые фильтры
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = django_filters.CharFilter(method='filter_by_category')
    categories = django_filters.CharFilter(method='filter_by_categories')
    price_min = django_filters.NumberFilter(method='filter_price_min')
    price_max = django_filters.NumberFilter(method='filter_price_max')
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

    # Флаг: учитывать совпадения только у родительских товаров (под ProductVariant переосмыслен)
    parent_matches_only = django_filters.BooleanFilter(method='filter_parent_matches_only')
    
    class Meta:
        model = models.Product
        fields = ['name', 'categories', 'price_min', 'price_max', 'is_available', 'is_popular', 'color', 'quantity', 'variation', 'price_range', 'attributes', 'parent_matches_only']

    def _is_parent_matches_only(self):
        value = self.data.get('parent_matches_only')
        if value in [True, 'true', 'True', '1', 1, 'yes', 'on']:
            return True
        return False
    
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
            if self._is_parent_matches_only():
                return queryset.filter(
                    product_attributes__attribute__in=color_values
                ).distinct()
            else:
                return queryset.filter(
                    Q(product_attributes__attribute__in=color_values) |
                    Q(variants__variant_attributes__attribute__in=color_values)
                ).distinct()
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
            if self._is_parent_matches_only():
                return queryset.filter(
                    product_attributes__attribute__in=quantity_values
                ).distinct()
            else:
                return queryset.filter(
                    Q(product_attributes__attribute__in=quantity_values) |
                    Q(variants__variant_attributes__attribute__in=quantity_values)
                ).distinct()
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
                if self._is_parent_matches_only():
                    return queryset.filter(
                        price__gte=min_price,
                        price__lte=max_price
                    ).distinct()
                else:
                    return queryset.filter(
                        Q(price__gte=min_price, price__lte=max_price) |
                        Q(variants__price__gte=min_price, variants__price__lte=max_price)
                    ).distinct()
            elif value.endswith('+'):
                min_price = float(value[:-1].strip())
                if self._is_parent_matches_only():
                    return queryset.filter(
                        price__gte=min_price
                    ).distinct()
                else:
                    return queryset.filter(
                        Q(price__gte=min_price) |
                        Q(variants__price__gte=min_price)
                    ).distinct()
            else:
                # Точное значение
                exact_price = float(value.strip())
                if self._is_parent_matches_only():
                    return queryset.filter(
                        price=exact_price
                    ).distinct()
                else:
                    return queryset.filter(
                        Q(price=exact_price) |
                        Q(variants__price=exact_price)
                    ).distinct()
        except (ValueError, AttributeError):
            return queryset.none()
    
    def filter_by_category(self, queryset, name, value):
        """Фильтр по категории (по slug)"""
        if not value:
            return queryset
        
        if self._is_parent_matches_only():
            return queryset.filter(
                categories__slug=value
            ).distinct()
        else:
            return queryset.filter(
                Q(categories__slug=value)
            ).distinct()
    
    # Удалено: иерархии категорий больше нет
    
    def filter_by_categories(self, queryset, name, value):
        """Фильтр по нескольким категориям (через запятую)"""
        if not value:
            return queryset
        
        category_slugs = [slug.strip() for slug in value.split(',')]
        if self._is_parent_matches_only():
            return queryset.filter(
                categories__slug__in=category_slugs
            ).distinct()
        else:
            return queryset.filter(
                Q(categories__slug__in=category_slugs)
            ).distinct()
    
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
                    if self._is_parent_matches_only():
                        conditions |= Q(product_attributes__attribute__in=attr_values)
                    else:
                        conditions |= Q(product_attributes__attribute__in=attr_values) | Q(variants__variant_attributes__attribute__in=attr_values)
            return queryset.filter(conditions).distinct()
        else:
            # И - все атрибуты должны совпадать
            for attr_value in value.split(','):
                attr_values = models.Attribute.objects.filter(
                    Q(value__icontains=attr_value.strip())
                )
                if attr_values.exists():
                    if self._is_parent_matches_only():
                        queryset = queryset.filter(
                            product_attributes__attribute__in=attr_values
                        )
                    else:
                        queryset = queryset.filter(
                            Q(product_attributes__attribute__in=attr_values) |
                            Q(variants__variant_attributes__attribute__in=attr_values)
                        )
                else:
                    return queryset.none()
            return queryset.distinct()

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
            if self._is_parent_matches_only():
                return queryset.filter(
                    product_attributes__attribute__in=variation_values
                ).distinct()
            else:
                return queryset.filter(
                    Q(product_attributes__attribute__in=variation_values) |
                    Q(variants__variant_attributes__attribute__in=variation_values)
                ).distinct()
        return queryset.none()

    def filter_main_products_only(self, queryset, name, value):
        """Фильтр для показа только основных товаров (без вариаций) через parent IS NULL"""
        if value:
            return queryset.distinct()
        return queryset

    def filter_price_min(self, queryset, name, value):
        if value is None:
            return queryset
        if self._is_parent_matches_only():
            return queryset.filter(price__gte=value).distinct()
        return queryset.filter(Q(price__gte=value) | Q(variants__price__gte=value)).distinct()

    def filter_price_max(self, queryset, name, value):
        if value is None:
            return queryset
        if self._is_parent_matches_only():
            return queryset.filter(price__lte=value).distinct()
        return queryset.filter(Q(price__lte=value) | Q(variants__price__lte=value)).distinct()

    def filter_parent_matches_only(self, queryset, name, value):
        # Ничего не делаем здесь. Ограничение по parent применяется в других методах и в qs
        return queryset

    @property
    def qs(self):
        qs = super().qs
        if self._is_parent_matches_only():
            return qs.distinct()
        return qs


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
