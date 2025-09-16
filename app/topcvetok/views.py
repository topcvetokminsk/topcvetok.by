from datetime import datetime
import os

from django.conf import settings
from django.contrib.auth import authenticate
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets, parsers
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from topcvetok import serializers as auth_serializers
from topcvetok import models
from topcvetok.permissions import CustomDjangoModelPermission
from topcvetok.filters import ProductFilter, AttributeFilter, AttributeTypeFilter, ServiceFilter


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
        tokens = OutstandingToken.objects.filter(user_id=request.user.id)

        for token in tokens:
            t, _ = BlacklistedToken.objects.get_or_create(token=token)

        return Response(status=status.HTTP_205_RESET_CONTENT)


class FlowerTypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.FlowerType.objects.all()
    serializer_class = auth_serializers.FlowerTypeSerializer


class AttributeTypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.AttributeType.objects.all()
    serializer_class = auth_serializers.AttributeTypeSerializer


class AttributeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Attribute.objects.all()
    serializer_class = auth_serializers.AttributeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['attribute_type', 'is_active', 'is_filterable']


class AttributeValueViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.AttributeValue.objects.all()
    serializer_class = auth_serializers.AttributeValueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['value', 'display_name']
    filterset_fields = ['attribute', 'is_active']


class ProductAttributeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ProductAttribute.objects.all()
    serializer_class = auth_serializers.ProductAttributeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['attribute', 'attribute_value', 'flower', 'bouquet', 'service']


class SupplierViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Supplier.objects.all()
    serializer_class = auth_serializers.SupplierSerializer


class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Warehouse.objects.all()
    serializer_class = auth_serializers.WarehouseSerializer


class FlowerViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Flower.objects.all()
    serializer_class = auth_serializers.FlowerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'origin_country']
    filterset_fields = ['flower_type', 'is_available', 'season']


class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Service.objects.all()
    serializer_class = auth_serializers.ServiceSerializer


class BouquetViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Bouquet.objects.all()
    serializer_class = auth_serializers.BouquetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'occasion']
    filterset_fields = ['is_available', 'occasion']


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Customer.objects.all()
    serializer_class = auth_serializers.CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'phone', 'email']


class OrderStatusViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.OrderStatus.objects.all()
    serializer_class = auth_serializers.OrderStatusSerializer


class OrderStatusViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.OrderStatus.objects.all()
    serializer_class = auth_serializers.OrderStatusSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.PaymentMethod.objects.all()
    serializer_class = auth_serializers.PaymentMethodSerializer


class DeliveryMethodViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.DeliveryMethod.objects.all()
    serializer_class = auth_serializers.DeliveryMethodSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Order.objects.all()
    serializer_class = auth_serializers.OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'customer_phone', 'delivery_address', 'order_number']
    filterset_fields = ['status', 'payment_status', 'created_at']


class OrderTrackingViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.OrderTracking.objects.all()
    serializer_class = auth_serializers.OrderTrackingSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Review.objects.all()
    serializer_class = auth_serializers.ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer__full_name', 'comment']
    filterset_fields = ['rating', 'is_approved']


# API для клиентов (без авторизации)
class PublicFlowerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Flower.objects.filter(is_available=True)
    serializer_class = auth_serializers.FlowerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'origin_country']
    filterset_fields = ['flower_type', 'is_in_stock', 'origin_country', 'season']
    ordering_fields = ['name', 'price', 'created_at']


class PublicBouquetViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Bouquet.objects.filter(is_available=True)
    serializer_class = auth_serializers.BouquetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'occasion']
    filterset_fields = ['is_in_stock', 'occasion']


class PublicServiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Service.objects.filter(is_available=True)
    serializer_class = auth_serializers.ServiceSerializer


class PublicPaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.PaymentMethod.objects.filter(is_active=True)
    serializer_class = auth_serializers.PaymentMethodSerializer


class PublicDeliveryMethodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.DeliveryMethod.objects.filter(is_active=True)
    serializer_class = auth_serializers.DeliveryMethodSerializer


class PublicFlowerColorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.FlowerColor.objects.all()
    serializer_class = auth_serializers.FlowerColorSerializer


class PublicFlowerCompositionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.FlowerComposition.objects.all()
    serializer_class = auth_serializers.FlowerCompositionSerializer


class PublicFlowerTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.FlowerType.objects.all()
    serializer_class = auth_serializers.FlowerTypeSerializer


class PublicAttributeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.AttributeType.objects.filter(is_filterable=True)
    serializer_class = auth_serializers.AttributeTypeSerializer


class PublicAttributeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Attribute.objects.filter(is_active=True, is_filterable=True)
    serializer_class = auth_serializers.AttributeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['attribute_type']


class PublicAttributeValueViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.AttributeValue.objects.filter(is_active=True)
    serializer_class = auth_serializers.AttributeValueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['value', 'display_name']
    filterset_fields = ['attribute']


# API для корзины (без авторизации, использует сессии)
class CartViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = auth_serializers.CartSerializer

    def get_queryset(self):
        # Получаем корзину по сессии
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        # Создаем или получаем клиента по сессии
        customer, created = models.Customer.objects.get_or_create(
            phone=f"session_{session_key}",
            defaults={'full_name': 'Гость'}
        )
        
        cart, created = models.Cart.objects.get_or_create(customer=customer)
        return models.Cart.objects.filter(id=cart.id)

    def create(self, request, *args, **kwargs):
        # Добавление товара в корзину
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        customer, created = models.Customer.objects.get_or_create(
            phone=f"session_{session_key}",
            defaults={'full_name': 'Гость'}
        )
        
        cart, created = models.Cart.objects.get_or_create(customer=customer)
        
        # Получаем данные товара
        flower_id = request.data.get('flower_id')
        bouquet_id = request.data.get('bouquet_id')
        service_id = request.data.get('service_id')
        quantity = request.data.get('quantity', 1)
        
        # Проверяем, что указан только один тип товара
        item_types = [flower_id, bouquet_id, service_id]
        if sum(1 for x in item_types if x) != 1:
            return Response(
                {"error": "Необходимо указать ровно один тип товара"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем позицию корзины
        cart_item = models.CartItem.objects.create(
            cart=cart,
            flower_id=flower_id,
            bouquet_id=bouquet_id,
            service_id=service_id,
            quantity=quantity
        )
        
        serializer = auth_serializers.CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        description="Отправить заявку на обратный звонок.",
        tags=["Заявки"],
        summary="Отправить заявку на обратный звонок.",
    ),
)
class RequestNote(APIView):
    permission_classes = (AllowAny,)
    serializer_class = auth_serializers.RequestNoteSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Здесь можно добавить логику сохранения заявки
            # и отправки уведомления администраторам
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ViewSets для работы с продуктами и атрибутами
@extend_schema_view(
    list=extend_schema(
        description="Получить список продуктов с возможностью фильтрации по атрибутам.",
        tags=["Продукты"],
        summary="Список продуктов",
    ),
    retrieve=extend_schema(
        description="Получить детальную информацию о продукте.",
        tags=["Продукты"],
        summary="Детали продукта",
    ),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с продуктами"""
    queryset = models.Product.objects.filter(is_available=True).prefetch_related(
        'categories',
        'product_attributes__attribute__attribute_type'
    )
    serializer_class = auth_serializers.ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']


@extend_schema_view(
    list=extend_schema(
        description="Получить список типов атрибутов для фильтрации.",
        tags=["Атрибуты"],
        summary="Список типов атрибутов",
    ),
)
class AttributeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с типами атрибутов"""
    queryset = models.AttributeType.objects.filter(is_active=True, is_filterable=True).prefetch_related('values')
    serializer_class = auth_serializers.AttributeTypeSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeTypeFilter


@extend_schema_view(
    list=extend_schema(
        description="Получить список значений атрибутов для фильтрации.",
        tags=["Атрибуты"],
        summary="Список значений атрибутов",
    ),
)
class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с атрибутами"""
    queryset = models.Attribute.objects.filter(is_active=True).select_related('attribute_type')
    serializer_class = auth_serializers.AttributeValueSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeFilter


@extend_schema_view(
    get=extend_schema(
        description="Получить доступные фильтры для продуктов.",
        tags=["Фильтры"],
        summary="Доступные фильтры",
    ),
)
class FilterOptionsView(APIView):
    """API для получения доступных опций фильтрации"""
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Возвращает все доступные опции для фильтрации"""
        # Получаем все активные типы атрибутов с их значениями
        attribute_types = models.AttributeType.objects.filter(
            is_active=True, 
            is_filterable=True
        ).prefetch_related('values').order_by('display_order')
        
        filters_data = {}
        
        for attr_type in attribute_types:
            values = attr_type.values.filter(is_active=True).order_by('display_order')
            filters_data[attr_type.slug] = {
                'name': attr_type.name,
                'slug': attr_type.slug,
                'filter_type': attr_type.filter_type,
                'values': [
                    {
                        'id': value.id,
                        'value': value.value,
                        'display_name': value.display_name,
                        'hex_code': value.hex_code,
                        'min_value': value.min_value,
                        'max_value': value.max_value,
                    }
                    for value in values
                ]
            }
        
        return Response(filters_data)


@extend_schema_view(
    post=extend_schema(
        description="Рассчитать цену продукта с учетом выбранных атрибутов.",
        tags=["Цены"],
        summary="Расчет цены с атрибутами",
    ),
)
class CalculatePriceView(APIView):
    """API для расчета цены продукта с учетом атрибутов"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Рассчитывает цену продукта с учетом выбранных атрибутов"""
        product_id = request.data.get('product_id')
        attribute_value_ids = request.data.get('attribute_values', [])
        
        if not product_id:
            return Response({'error': 'product_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = models.Product.objects.get(id=product_id, is_available=True)
        except models.Product.DoesNotExist:
            return Response({'error': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Получаем объекты AttributeValue
        attribute_values = models.AttributeValue.objects.filter(
            id__in=attribute_value_ids,
            is_active=True
        )
        
        # Рассчитываем цену
        calculated_price = product.get_price_with_attributes(attribute_values)
        base_price = product.price
        
        # Получаем детали модификаторов
        modifiers = []
        for attr_value in attribute_values:
            if attr_value.price_modifier != 0:
                modifiers.append({
                    'attribute_name': attr_value.display_name,
                    'modifier': attr_value.price_modifier
                })
        
        return Response({
            'product_id': product_id,
            'base_price': float(base_price),
            'calculated_price': float(calculated_price),
            'modifiers': modifiers,
            'total_modifier': float(calculated_price - base_price)
        })


@extend_schema_view(
    post=extend_schema(
        description="Создать новый заказ с обязательным согласием на обработку персональных данных.",
        tags=["Заказы"],
        summary="Создание заказа",
    ),
)
class OrderCreateView(APIView):
    """API для создания заказов с проверкой согласия"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Создает новый заказ"""
        serializer = auth_serializers.OrderCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Добавляем IP адрес клиента
            order = serializer.save(
                ip_address=self.get_client_ip(request)
            )
            
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