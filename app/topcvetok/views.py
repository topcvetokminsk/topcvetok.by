from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_datetime
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from topcvetok import serializers as auth_serializers
from topcvetok import models
from topcvetok.filters import ProductFilter, AttributeFilter, AttributeTypeFilter, ServiceFilter
from topcvetok.enums import DeliveryType, AttributeFilterType, ReviewRating


# Авторизация
@extend_schema_view(
    post=extend_schema(
        description="Авторизоваться с помощью логина и пароля.",
        tags=["Авторизация"],
        summary="Авторизоваться с помощью логина и пароля.",
    ),
)
class Login(APIView):
    permission_classes = (AllowAny,)
    serializer_class = auth_serializers.LoginSerializer

    def post(self, request):
        data = request.data
        login = data.get("login")
        password = data.get("password")

        if not login:
            raise ValidationError("Введите логин", code=status.HTTP_400_BAD_REQUEST)

        if not password:
            raise ValidationError("Введите пароль", code=status.HTTP_400_BAD_REQUEST)

        user = authenticate(login=login, password=password)
        if not user:
            raise ValidationError("Такого пользователя не существует.", code=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        description="Выйти из системы.",
        tags=["Авторизация"],
        summary="Выйти из системы.",
    ),
)
class Logout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Админ API
class AttributeTypeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с типами атрибутов"""
    queryset = models.AttributeType.objects.all()
    serializer_class = auth_serializers.AttributeTypeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeTypeFilter


class AttributeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с атрибутами"""
    queryset = models.Attribute.objects.all()
    serializer_class = auth_serializers.AttributeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeFilter


class ProductAttributeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с атрибутами продуктов"""
    queryset = models.ProductAttribute.objects.all()
    serializer_class = auth_serializers.ProductAttributeSerializer
    permission_classes = (IsAuthenticated,)


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с услугами"""
    queryset = models.Service.objects.all()
    serializer_class = auth_serializers.ServiceSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = ServiceFilter


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet для работы со способами оплаты"""
    queryset = models.PaymentMethod.objects.all()
    serializer_class = auth_serializers.PaymentMethodSerializer
    permission_classes = (IsAuthenticated,)


class DeliveryMethodViewSet(viewsets.ModelViewSet):
    """ViewSet для работы со способами доставки"""
    queryset = models.DeliveryMethod.objects.all()
    serializer_class = auth_serializers.DeliveryMethodSerializer
    permission_classes = (IsAuthenticated,)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с заказами"""
    queryset = models.Order.objects.all()
    serializer_class = auth_serializers.OrderSerializer
    permission_classes = (IsAuthenticated,)


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с отзывами"""
    queryset = models.Review.objects.filter(is_approved=True)
    serializer_class = auth_serializers.ReviewSerializer
    permission_classes = (AllowAny,)


# Публичный API
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с продуктами"""
    queryset = models.Product.objects.filter(is_available=True).prefetch_related(
        'categories', 'product_attributes__attribute__attribute_type'
    )
    serializer_class = auth_serializers.ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = ProductFilter
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']


class AttributeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с типами атрибутов"""
    queryset = models.AttributeType.objects.filter(is_active=True, is_filterable=True).prefetch_related('values')
    serializer_class = auth_serializers.AttributeTypeSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeTypeFilter


class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с атрибутами"""
    queryset = models.Attribute.objects.filter(is_active=True).select_related('attribute_type')
    serializer_class = auth_serializers.AttributeSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeFilter


class PublicServiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Service.objects.filter(is_available=True)
    serializer_class = auth_serializers.ServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = ServiceFilter


class PublicPaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.PaymentMethod.objects.filter(is_active=True)
    serializer_class = auth_serializers.PaymentMethodSerializer


class PublicDeliveryMethodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.DeliveryMethod.objects.filter(is_active=True)
    serializer_class = auth_serializers.DeliveryMethodSerializer


# Заказы
@extend_schema_view(
    post=extend_schema(
        description="Создать новый заказ с товарами.",
        tags=["Заказы"],
        summary="Создание заказа",
    ),
)
class OrderCreateView(APIView):
    """API для создания заказов с товарами"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Создает новый заказ с товарами"""
        serializer = auth_serializers.OrderCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Получаем данные заказа
            order_data = serializer.validated_data
            
            # Создаем заказ
            order = models.Order.objects.create(
                delivery_address=order_data['delivery_address'],
                delivery_date=order_data.get('delivery_date'),
                delivery_notes=order_data.get('delivery_notes', ''),
                delivery_method_id=order_data['delivery_method'],
                payment_method_id=order_data['payment_method'],
                service_id=order_data.get('service') if order_data.get('service') else None,
                customer_name=order_data['customer_name'],
                customer_phone=order_data['customer_phone'],
                customer_email=order_data.get('customer_email', ''),
                notes=order_data.get('notes', ''),
                personal_data_consent=order_data['personal_data_consent'],
                ip_address=self.get_client_ip(request)
            )
            
            # Добавляем товары в заказ
            total_amount = 0
            for item_data in order_data['items']:
                product = models.Product.objects.get(id=item_data['product_id'])
                
                # Рассчитываем цену с учетом атрибутов
                price = product.price
                if item_data.get('attribute_ids'):
                    attributes = models.Attribute.objects.filter(
                        id__in=item_data['attribute_ids']
                    )
                    price = product.get_price_with_attributes(attributes)
                
                # Создаем позицию заказа
                order_item = models.OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    price=price,
                    item_name=product.name,
                    item_description=product.description
                )
                
                # Добавляем атрибуты если есть
                if item_data.get('attribute_ids'):
                    order_item.attributes.set(attributes)
                
                total_amount += price * item_data['quantity']
            
            # Обновляем общую сумму заказа
            order.total_amount = total_amount
            order.save()
            
            return Response(
                auth_serializers.OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema_view(
    post=extend_schema(
        description="Рассчитать цену продукта с учетом выбранных атрибутов.",
        tags=["Продукты"],
        summary="Рассчитать цену",
    ),
)
class CalculatePriceView(APIView):
    """API для расчета цены продукта с атрибутами"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Рассчитывает цену продукта с учетом атрибутов"""
        product_id = request.data.get('product_id')
        attribute_ids = request.data.get('attribute_ids', [])
        
        if not product_id:
            return Response(
                {"error": "Не указан ID продукта"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = models.Product.objects.get(id=product_id, is_available=True)
        except models.Product.DoesNotExist:
            return Response(
                {"error": "Продукт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Получаем атрибуты если указаны
        attributes = []
        if attribute_ids:
            attributes = models.Attribute.objects.filter(
                id__in=attribute_ids, is_active=True
            )
        
        # Рассчитываем цену
        if attributes:
            final_price = product.get_price_with_attributes(attributes)
            modifiers = [float(attr.price_modifier) for attr in attributes]
        else:
            final_price = product.price
            modifiers = []
        
        return Response({
            'product_id': product.id,
            'base_price': float(product.price),
            'final_price': float(final_price),
            'modifiers': modifiers,
            'total_modifier': sum(modifiers)
        })


@extend_schema_view(
    post=extend_schema(
        description="Рассчитать стоимость доставки.",
        tags=["Доставка"],
        summary="Рассчитать стоимость доставки",
    ),
)
class CalculateDeliveryPriceView(APIView):
    """API для расчета стоимости доставки"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Рассчитывает стоимость доставки"""
        delivery_method_id = request.data.get('delivery_method_id')
        order_amount = request.data.get('order_amount', 0)
        delivery_time = request.data.get('delivery_time')  # ISO datetime string
        
        if not delivery_method_id:
            return Response(
                {"error": "Не указан ID способа доставки"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            delivery_method = models.DeliveryMethod.objects.get(
                id=delivery_method_id, is_active=True
            )
        except models.DeliveryMethod.DoesNotExist:
            return Response(
                {"error": "Способ доставки не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Парсим время доставки если указано
        delivery_datetime = None
        if delivery_time:
            delivery_datetime = parse_datetime(delivery_time)
        
        # Рассчитываем стоимость доставки
        delivery_price = delivery_method.calculate_delivery_price(
            order_amount=order_amount,
            delivery_time=delivery_datetime
        )
        
        return Response({
            'delivery_method_id': delivery_method.id,
            'delivery_method_name': delivery_method.name,
            'delivery_type': delivery_method.delivery_type,
            'order_amount': float(order_amount),
            'delivery_price': float(delivery_price),
            'delivery_info': delivery_method.get_delivery_info(),
            'delivery_time': delivery_time
        })


@extend_schema_view(
    get=extend_schema(
        description="Получить опции для фильтрации.",
        tags=["Фильтры"],
        summary="Опции фильтрации",
    ),
)
class FilterOptionsView(APIView):
    """API для получения опций фильтрации"""
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Возвращает опции для фильтрации"""
        # Получаем типы атрибутов для фильтрации
        attribute_types = models.AttributeType.objects.filter(
            is_active=True, is_filterable=True
        ).prefetch_related('attribute_set')
        
        filter_options = {}
        for attr_type in attribute_types:
            attributes = attr_type.attribute_set.filter(is_active=True)
            filter_options[attr_type.slug] = {
                'name': attr_type.name,
                'slug': attr_type.slug,
                'filter_type': attr_type.filter_type,
                'values': [
                    {
                        'id': attr.id,
                        'display_name': attr.display_name,
                        'hex_code': attr.hex_code,
                        'price_modifier': float(attr.price_modifier)
                    }
                    for attr in attributes
                ]
            }
        
        return Response(filter_options)


@extend_schema_view(
    get=extend_schema(
        description="Получить доступные енамы для фронтенда.",
        tags=["Справочники"],
        summary="Енамы",
    ),
)
class EnumsView(APIView):
    """API для получения енамов"""
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Возвращает все доступные енамы"""
        
        return Response({
            'delivery_types': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in DeliveryType.choices
            ],
            'attribute_filter_types': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in AttributeFilterType.choices
            ],
            'review_ratings': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in ReviewRating.choices
            ]
        })
