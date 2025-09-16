
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from topcvetok import serializers as auth_serializers
from topcvetok import models
from topcvetok.filters import ProductFilter, AttributeFilter, AttributeTypeFilter, ServiceFilter


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
        tokens = OutstandingToken.objects.filter(user_id=request.user.id)

        for token in tokens:
            t, _ = BlacklistedToken.objects.get_or_create(token=token)

        return Response(status=status.HTTP_205_RESET_CONTENT)


# Админ ViewSet'ы (требуют авторизации)
class AttributeTypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.AttributeType.objects.all()
    serializer_class = auth_serializers.AttributeTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active', 'is_filterable']


class AttributeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Attribute.objects.all()
    serializer_class = auth_serializers.AttributeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['display_name']
    filterset_fields = ['attribute_type', 'is_active', 'is_filterable']


class ProductAttributeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ProductAttribute.objects.all()
    serializer_class = auth_serializers.ProductAttributeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['attribute', 'product']


class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Service.objects.all()
    serializer_class = auth_serializers.ServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_available', 'is_active']


class PaymentMethodViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.PaymentMethod.objects.all()
    serializer_class = auth_serializers.PaymentMethodSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']


class DeliveryMethodViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.DeliveryMethod.objects.all()
    serializer_class = auth_serializers.DeliveryMethodSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.Order.objects.all()
    serializer_class = auth_serializers.OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'customer_phone', 'delivery_address', 'order_number']
    filterset_fields = ['payment_method', 'delivery_method', 'service']


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.Review.objects.all()
    serializer_class = auth_serializers.ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'comment']
    filterset_fields = ['rating', 'is_approved']


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с продуктами"""
    queryset = models.Product.objects.filter(is_available=True).prefetch_related(
        'categories',
        'product_attributes__attribute__attribute_type'
    )
    serializer_class = auth_serializers.ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = ProductFilter
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']




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


# Корзина
class CartViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с корзиной"""
    queryset = models.Cart.objects.all()
    serializer_class = auth_serializers.CartSerializer
    permission_classes = (AllowAny,)
    
    def get_queryset(self):
        """Фильтрует корзины по session_key"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        return models.Cart.objects.filter(session_key=session_key)
    
    def get_object(self):
        """Получает или создает корзину для текущей сессии"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = models.Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'ip_address': self.get_client_ip()}
        )
        
        if created:
            cart.ip_address = self.get_client_ip()
            cart.save()
        
        return cart
    
    def get_client_ip(self):
        """Получает IP адрес клиента"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


@extend_schema_view(
    post=extend_schema(
        description="Добавить товар в корзину.",
        tags=["Корзина"],
        summary="Добавить товар",
    ),
)
class CartAddItemView(APIView):
    """API для добавления товара в корзину"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Добавляет товар в корзину"""
        serializer = auth_serializers.CartAddItemSerializer(data=request.data)
        
        if serializer.is_valid():
            # Получаем или создаем корзину
            cart = self.get_or_create_cart()
            
            # Получаем продукт и атрибуты
            product = models.Product.objects.get(id=serializer.validated_data['product_id'])
            attributes = None
            
            if serializer.validated_data.get('attribute_ids'):
                attributes = models.Attribute.objects.filter(
                    id__in=serializer.validated_data['attribute_ids']
                )
            
            # Добавляем товар в корзину
            cart_item = cart.add_item(
                product=product,
                quantity=serializer.validated_data['quantity'],
                attributes=attributes
            )
            
            return Response(
                auth_serializers.CartItemSerializer(cart_item).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_or_create_cart(self):
        """Получает или создает корзину для текущей сессии"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = models.Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'ip_address': self.get_client_ip()}
        )
        
        if created:
            cart.ip_address = self.get_client_ip()
            cart.save()
        
        return cart
    
    def get_client_ip(self):
        """Получает IP адрес клиента"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


@extend_schema_view(
    put=extend_schema(
        description="Обновить товар в корзине.",
        tags=["Корзина"],
        summary="Обновить товар",
    ),
    delete=extend_schema(
        description="Удалить товар из корзины.",
        tags=["Корзина"],
        summary="Удалить товар",
    ),
)
class CartItemView(APIView):
    """API для работы с товарами в корзине"""
    permission_classes = (AllowAny,)
    
    def put(self, request, item_id):
        """Обновляет товар в корзине"""
        try:
            cart_item = models.CartItem.objects.get(
                id=item_id,
                cart__session_key=self.get_session_key()
            )
        except models.CartItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = auth_serializers.CartUpdateItemSerializer(data=request.data)
        
        if serializer.is_valid():
            cart_item.quantity = serializer.validated_data['quantity']
            
            if 'attribute_ids' in serializer.validated_data:
                attributes = models.Attribute.objects.filter(
                    id__in=serializer.validated_data['attribute_ids']
                )
                cart_item.attributes.set(attributes)
            
            cart_item.save()
            
            return Response(auth_serializers.CartItemSerializer(cart_item).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, item_id):
        """Удаляет товар из корзины"""
        try:
            cart_item = models.CartItem.objects.get(
                id=item_id,
                cart__session_key=self.get_session_key()
            )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.CartItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_session_key(self):
        """Получает ключ сессии"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        return session_key


@extend_schema_view(
    post=extend_schema(
        description="Очистить корзину.",
        tags=["Корзина"],
        summary="Очистить корзину",
    ),
)
class CartClearView(APIView):
    """API для очистки корзины"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Очищает корзину"""
        cart = self.get_or_create_cart()
        cart.clear()
        
        return Response(
            {'message': 'Корзина очищена'},
            status=status.HTTP_200_OK
        )
    
    def get_or_create_cart(self):
        """Получает или создает корзину для текущей сессии"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = models.Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'ip_address': self.get_client_ip()}
        )
        
        if created:
            cart.ip_address = self.get_client_ip()
            cart.save()
        
        return cart
    
    def get_client_ip(self):
        """Получает IP адрес клиента"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


@extend_schema_view(
    post=extend_schema(
        description="Оформить заказ из корзины.",
        tags=["Корзина"],
        summary="Оформить заказ",
    ),
)
class CartCheckoutView(APIView):
    """API для оформления заказа из корзины"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Оформляет заказ из корзины"""
        # Получаем корзину
        cart = self.get_or_create_cart()
        
        if not cart.items.exists():
            return Response(
                {'error': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Валидируем данные заказа
        serializer = auth_serializers.CartCheckoutSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Преобразуем корзину в заказ
                order = cart.to_order(serializer.validated_data)
                
                return Response(
                    auth_serializers.OrderSerializer(order).data,
                    status=status.HTTP_201_CREATED
                )
                
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_or_create_cart(self):
        """Получает или создает корзину для текущей сессии"""
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = models.Cart.objects.get_or_create(
            session_key=session_key,
            defaults={'ip_address': self.get_client_ip()}
        )
        
        if created:
            cart.ip_address = self.get_client_ip()
            cart.save()
        
        return cart
    
    def get_client_ip(self):
        """Получает IP адрес клиента"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


# Заказы
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


# Дополнительные API
@extend_schema_view(
    post=extend_schema(
        description="Рассчитать цену продукта с учетом выбранных атрибутов.",
        tags=["Цены"],
        summary="Расчет цены",
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
        
        # Получаем объекты Attribute
        attributes = models.Attribute.objects.filter(
            id__in=attribute_value_ids,
            is_active=True
        )
        
        # Рассчитываем цену с учетом атрибутов
        calculated_price = product.get_price_with_attributes(attributes)
        base_price = product.price
        
        # Получаем детали модификаторов
        modifiers = []
        for attribute in attributes:
            if attribute.price_modifier != 0:
                modifiers.append({
                    'attribute_name': attribute.display_name,
                    'modifier': float(attribute.price_modifier)
                })
        
        return Response({
            'product_id': product_id,
            'base_price': float(base_price),
            'calculated_price': float(calculated_price),
            'modifiers': modifiers,
            'total_modifier': float(calculated_price - base_price)
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
            is_active=True, 
            is_filterable=True
        ).prefetch_related('values')
        
        # Получаем категории
        categories = models.Category.objects.filter(is_active=True)
        
        # Получаем ценовые диапазоны
        products = models.Product.objects.filter(is_available=True)
        if products.exists():
            min_price = products.aggregate(min_price=models.Min('price'))['min_price']
            max_price = products.aggregate(max_price=models.Max('price'))['max_price']
        else:
            min_price = max_price = 0
        
        return Response({
            'attribute_types': auth_serializers.AttributeTypeSerializer(attribute_types, many=True).data,
            'categories': auth_serializers.CategorySerializer(categories, many=True).data,
            'price_range': {
                'min': float(min_price) if min_price else 0,
                'max': float(max_price) if max_price else 0
            }
        })

