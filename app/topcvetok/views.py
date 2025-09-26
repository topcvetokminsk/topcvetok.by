from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_datetime
from rest_framework import filters, status, viewsets, parsers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from topcvetok import serializers as auth_serializers
from topcvetok import models
from topcvetok.filters import ProductFilter, AttributeFilter, ServiceFilter, CategoryFilter
from topcvetok.enums import DeliveryType, AttributeFilterType, ReviewRating


@extend_schema_view(
    post=extend_schema(
        summary="Войти в систему",
        description="Авторизует пользователя в системе с помощью логина и пароля. "
                   "Возвращает JWT токены для доступа к защищенным API endpoints.",
        tags=["Авторизация"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "login": {"type": "string", "description": "Логин пользователя"},
                    "password": {"type": "string", "description": "Пароль пользователя"}
                },
                "required": ["login", "password"]
            }
        },
        responses={
            200: {
                "description": "Успешная авторизация",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "refresh": {"type": "string", "description": "Refresh токен"},
                            "access": {"type": "string", "description": "Access токен"}
                        }
                    }
                }
            },
            401: {
                "description": "Ошибка авторизации",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "description": "Описание ошибки"}
                        }
                    }
                }
            }
        }
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
        summary="Выйти из системы",
        description="Завершает сессию пользователя, добавляя refresh токен в черный список. "
                   "Требует авторизации.",
        tags=["Авторизация"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string", "description": "Refresh токен для добавления в черный список"}
                },
                "required": ["refresh"]
            }
        },
        responses={
            205: {
                "description": "Успешный выход из системы"
            },
            400: {
                "description": "Ошибка при выходе из системы"
            }
        }
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
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список атрибутов",
        description="Возвращает список всех активных атрибутов товаров. "
                   "Включает цвета, количества, типы букетов, составы, вариации и ценовые диапазоны.",
        tags=["Атрибуты"],
    ),
    retrieve=extend_schema(
        summary="Получить атрибут по ID",
        description="Возвращает детальную информацию о конкретном атрибуте товара.",
        tags=["Атрибуты"],
    ),
    create=extend_schema(
        summary="Создать новый атрибут",
        description="Создает новый атрибут товара (цвет, количество, тип и т.д.). Требует права администратора.",
        tags=["Атрибуты"],
    ),
    update=extend_schema(
        summary="Обновить атрибут",
        description="Полностью обновляет информацию об атрибуте. Требует права администратора.",
        tags=["Атрибуты"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить атрибут",
        description="Частично обновляет информацию об атрибуте. Требует права администратора.",
        tags=["Атрибуты"],
    ),
    destroy=extend_schema(
        summary="Удалить атрибут",
        description="Удаляет атрибут товара. Требует права администратора.",
        tags=["Атрибуты"],
    ),
)
class AttributeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с атрибутами"""
    queryset = models.Attribute.objects.all()
    serializer_class = auth_serializers.AttributeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttributeFilter
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список категорий",
        description="Возвращает список всех активных категорий товаров. "
                   "Включает иерархическую структуру с родительскими и дочерними категориями.",
        tags=["Категории"],
    ),
    retrieve=extend_schema(
        summary="Получить категорию по ID",
        description="Возвращает детальную информацию о конкретной категории, "
                   "включая её иерархию и связанные товары.",
        tags=["Категории"],
    ),
    create=extend_schema(
        summary="Создать новую категорию",
        description="Создает новую категорию товаров. Требует права администратора.",
        tags=["Категории"],
    ),
    update=extend_schema(
        summary="Обновить категорию",
        description="Полностью обновляет информацию о категории. Требует права администратора.",
        tags=["Категории"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить категорию",
        description="Частично обновляет информацию о категории. Требует права администратора.",
        tags=["Категории"],
    ),
    destroy=extend_schema(
        summary="Удалить категорию",
        description="Удаляет категорию товаров. Требует права администратора.",
        tags=["Категории"],
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с категориями"""
    queryset = models.Category.objects.all()
    serializer_class = auth_serializers.CategorySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = CategoryFilter
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    parser_classes = (parsers.MultiPartParser, JSONParser)
    
    def get_queryset(self):
        """Оптимизированный queryset для категорий"""
        return models.Category.objects.select_related('parent').prefetch_related(
            'children', 'products'
        ).filter(is_active=True)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny,)

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список атрибутов продуктов",
        description="Возвращает список всех связей между продуктами и их атрибутами. "
                   "Показывает какие атрибуты доступны для каждого товара.",
        tags=["Продукты"],
    ),
    retrieve=extend_schema(
        summary="Получить атрибут продукта по ID",
        description="Возвращает детальную информацию о связи продукта с атрибутом.",
        tags=["Продукты"],
    ),
    create=extend_schema(
        summary="Добавить атрибут к продукту",
        description="Создает связь между продуктом и атрибутом. Требует права администратора.",
        tags=["Продукты"],
    ),
    update=extend_schema(
        summary="Обновить атрибут продукта",
        description="Обновляет связь между продуктом и атрибутом. Требует права администратора.",
        tags=["Продукты"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить атрибут продукта",
        description="Частично обновляет связь между продуктом и атрибутом. Требует права администратора.",
        tags=["Продукты"],
    ),
    destroy=extend_schema(
        summary="Удалить атрибут у продукта",
        description="Удаляет связь между продуктом и атрибутом. Требует права администратора.",
        tags=["Продукты"],
    ),
)
class ProductAttributeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с атрибутами продуктов"""
    queryset = models.ProductAttribute.objects.all()
    serializer_class = auth_serializers.ProductAttributeSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список товаров",
        description="Возвращает список всех доступных товаров (цветов, букетов). "
                   "Поддерживает фильтрацию по категориям, атрибутам, цене и поиск по названию.",
        tags=["Товары"],
    ),
    retrieve=extend_schema(
        summary="Получить товар по ID",
        description="Возвращает детальную информацию о конкретном товаре, включая все его атрибуты.",
        tags=["Товары"],
    ),
    create=extend_schema(
        summary="Создать новый товар",
        description="Создает новый товар в каталоге. Требует права администратора.",
        tags=["Товары"],
    ),
    update=extend_schema(
        summary="Обновить товар",
        description="Полностью обновляет информацию о товаре. Требует права администратора.",
        tags=["Товары"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить товар",
        description="Частично обновляет информацию о товаре. Требует права администратора.",
        tags=["Товары"],
    ),
    destroy=extend_schema(
        summary="Удалить товар",
        description="Удаляет товар из каталога. Требует права администратора.",
        tags=["Товары"],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с продуктами"""
    queryset = models.Product.objects.all()
    serializer_class = auth_serializers.ProductSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = ProductFilter
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']
    parser_classes = (parsers.MultiPartParser, JSONParser)
    
    def get_queryset(self):
        """Оптимизированный queryset с prefetch_related"""
        return models.Product.objects.select_related().prefetch_related(
            'categories',
            'product_attributes__attribute'
        ).filter(is_available=True)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список услуг",
        description="Возвращает список всех доступных услуг (доставка, упаковка, оформление и т.д.). "
                   "Поддерживает фильтрацию по типу, цене и поиск по названию.",
        tags=["Услуги"],
    ),
    retrieve=extend_schema(
        summary="Получить услугу по ID",
        description="Возвращает детальную информацию о конкретной услуге.",
        tags=["Услуги"],
    ),
    create=extend_schema(
        summary="Создать новую услугу",
        description="Создает новую услугу в каталоге. Требует права администратора.",
        tags=["Услуги"],
    ),
    update=extend_schema(
        summary="Обновить услугу",
        description="Полностью обновляет информацию об услуге. Требует права администратора.",
        tags=["Услуги"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить услугу",
        description="Частично обновляет информацию об услуге. Требует права администратора.",
        tags=["Услуги"],
    ),
    destroy=extend_schema(
        summary="Удалить услугу",
        description="Удаляет услугу из каталога. Требует права администратора.",
        tags=["Услуги"],
    ),
)
class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с услугами"""
    queryset = models.Service.objects.all()
    serializer_class = auth_serializers.ServiceSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_class = ServiceFilter
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список способов оплаты",
        description="Возвращает список всех доступных способов оплаты (наличные, карта, перевод и т.д.).",
        tags=["Оплата"],
    ),
    retrieve=extend_schema(
        summary="Получить способ оплаты по ID",
        description="Возвращает детальную информацию о конкретном способе оплаты.",
        tags=["Оплата"],
    ),
    create=extend_schema(
        summary="Создать новый способ оплаты",
        description="Создает новый способ оплаты. Требует права администратора.",
        tags=["Оплата"],
    ),
    update=extend_schema(
        summary="Обновить способ оплаты",
        description="Полностью обновляет информацию о способе оплаты. Требует права администратора.",
        tags=["Оплата"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить способ оплаты",
        description="Частично обновляет информацию о способе оплаты. Требует права администратора.",
        tags=["Оплата"],
    ),
    destroy=extend_schema(
        summary="Удалить способ оплаты",
        description="Удаляет способ оплаты. Требует права администратора.",
        tags=["Оплата"],
    ),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet для работы со способами оплаты"""
    queryset = models.PaymentMethod.objects.all()
    serializer_class = auth_serializers.PaymentMethodSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список способов доставки",
        description="Возвращает список всех доступных способов доставки (по Минску, по Беларуси, самовывоз). "
                   "Включает информацию о ценах, времени работы и условиях доставки.",
        tags=["Доставка"],
    ),
    retrieve=extend_schema(
        summary="Получить способ доставки по ID",
        description="Возвращает детальную информацию о конкретном способе доставки, "
                   "включая расчет стоимости и условия.",
        tags=["Доставка"],
    ),
    create=extend_schema(
        summary="Создать новый способ доставки",
        description="Создает новый способ доставки с настройками ценообразования. Требует права администратора.",
        tags=["Доставка"],
    ),
    update=extend_schema(
        summary="Обновить способ доставки",
        description="Полностью обновляет информацию о способе доставки. Требует права администратора.",
        tags=["Доставка"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить способ доставки",
        description="Частично обновляет информацию о способе доставки. Требует права администратора.",
        tags=["Доставка"],
    ),
    destroy=extend_schema(
        summary="Удалить способ доставки",
        description="Удаляет способ доставки. Требует права администратора.",
        tags=["Доставка"],
    ),
)
class DeliveryMethodViewSet(viewsets.ModelViewSet):
    """ViewSet для работы со способами доставки"""
    queryset = models.DeliveryMethod.objects.all()
    serializer_class = auth_serializers.DeliveryMethodSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список заказов",
        description="Возвращает список всех заказов. Доступно только администраторам.",
        tags=["Заказы"],
    ),
    retrieve=extend_schema(
        summary="Получить заказ по ID",
        description="Возвращает детальную информацию о конкретном заказе. Доступно только администраторам.",
        tags=["Заказы"],
    ),
    create=extend_schema(
        summary="Создать новый заказ",
        description="Создает новый заказ с выбранными товарами, атрибутами и настройками доставки. "
                   "Доступно всем пользователям (включая неавторизованных). "
                   "Автоматически рассчитывает стоимость с учетом выбранных атрибутов товаров.",
        tags=["Заказы"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string", "description": "ID товара"},
                                "quantity": {"type": "integer", "description": "Количество"},
                                "attribute_ids": {"type": "array", "items": {"type": "string"}, "description": "ID выбранных атрибутов"}
                            }
                        }
                    },
                    "delivery_address": {"type": "string", "description": "Адрес доставки"},
                    "delivery_method": {"type": "string", "description": "ID способа доставки"},
                    "payment_method": {"type": "string", "description": "ID способа оплаты"},
                    "customer_name": {"type": "string", "description": "Имя клиента"},
                    "customer_phone": {"type": "string", "description": "Телефон клиента"},
                    "personal_data_consent": {"type": "boolean", "description": "Согласие на обработку данных"}
                }
            }
        }
    ),
    update=extend_schema(
        summary="Обновить заказ",
        description="Полностью обновляет информацию о заказе. Доступно только администраторам.",
        tags=["Заказы"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить заказ",
        description="Частично обновляет информацию о заказе (статус, примечания и т.д.). Доступно только администраторам.",
        tags=["Заказы"],
    ),
    destroy=extend_schema(
        summary="Удалить заказ",
        description="Удаляет заказ. Доступно только администраторам.",
        tags=["Заказы"],
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с заказами"""
    queryset = models.Order.objects.all()
    serializer_class = auth_serializers.OrderSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        """Оптимизированный queryset для заказов"""
        return models.Order.objects.select_related(
            'delivery_method', 'payment_method', 'service'
        ).prefetch_related(
            'items__product',
            'items__attributes',
            'items__service'
        ).order_by('-created_at')
    
    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = (AllowAny, )

        return super(self.__class__, self).get_permissions()
    
    def get_serializer_class(self):
        """Возвращает правильный сериализатор в зависимости от действия"""
        if self.action == "create":
            return auth_serializers.OrderCreateSerializer
        return auth_serializers.OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Создает новый заказ с товарами"""
        serializer = self.get_serializer(data=request.data)
        
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
    list=extend_schema(
        summary="Получить список отзывов",
        description="Возвращает список всех отзывов о товарах и услугах. "
                   "Показывает только одобренные отзывы для публичного просмотра.",
        tags=["Отзывы"],
    ),
    retrieve=extend_schema(
        summary="Получить отзыв по ID",
        description="Возвращает детальную информацию о конкретном отзыве.",
        tags=["Отзывы"],
    ),
    create=extend_schema(
        summary="Создать новый отзыв",
        description="Создает новый отзыв о товаре или услуге. Требует права администратора.",
        tags=["Отзывы"],
    ),
    update=extend_schema(
        summary="Обновить отзыв",
        description="Полностью обновляет информацию об отзыве. Требует права администратора.",
        tags=["Отзывы"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить отзыв",
        description="Частично обновляет информацию об отзыве (статус одобрения, текст и т.д.). Требует права администратора.",
        tags=["Отзывы"],
    ),
    destroy=extend_schema(
        summary="Удалить отзыв",
        description="Удаляет отзыв. Требует права администратора.",
        tags=["Отзывы"],
    ),
)
class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с отзывами"""
    queryset = models.Review.objects.all()
    serializer_class = auth_serializers.ReviewSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny,)

        return super(self.__class__, self).get_permissions()




@extend_schema_view(
    post=extend_schema(
        summary="Рассчитать цену товара",
        description="Рассчитывает итоговую цену товара с учетом выбранных атрибутов. "
                   "Показывает базовую цену, модификаторы от атрибутов и итоговую стоимость. "
                   "Полезно для предварительного расчета стоимости заказа.",
        tags=["Товары"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "ID товара для расчета цены"},
                    "attribute_ids": {"type": "array", "items": {"type": "string"}, "description": "ID выбранных атрибутов"}
                },
                "required": ["product_id"]
            }
        },
        responses={
            200: {
                "description": "Успешный расчет цены",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "base_price": {"type": "number", "description": "Базовая цена товара"},
                            "final_price": {"type": "number", "description": "Итоговая цена с атрибутами"},
                            "modifiers": {"type": "array", "items": {"type": "number"}, "description": "Модификаторы от атрибутов"},
                            "total_modifier": {"type": "number", "description": "Общий модификатор"}
                        }
                    }
                }
            }
        }
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
        summary="Рассчитать стоимость доставки",
        description="Рассчитывает стоимость доставки на основе выбранного способа доставки, "
                   "суммы заказа и времени доставки. Учитывает праздничные дни, "
                   "время работы и специальные условия для разных типов доставки.",
        tags=["Доставка"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "delivery_method_id": {"type": "string", "description": "ID способа доставки"},
                    "order_amount": {"type": "number", "description": "Сумма заказа в BYN"},
                    "delivery_time": {"type": "string", "format": "date-time", "description": "Время доставки (ISO 8601)"}
                },
                "required": ["delivery_method_id"]
            }
        },
        responses={
            200: {
                "description": "Успешный расчет стоимости доставки",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "delivery_method_id": {"type": "string"},
                            "delivery_method_name": {"type": "string"},
                            "delivery_type": {"type": "string"},
                            "order_amount": {"type": "number"},
                            "delivery_price": {"type": "number", "description": "Стоимость доставки"},
                            "delivery_info": {"type": "object", "description": "Детальная информация о доставке"},
                            "delivery_time": {"type": "string"}
                        }
                    }
                }
            }
        }
    ),
)
class CalculateDeliveryPriceView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
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
        summary="Получить справочники",
        description="Возвращает все доступные справочники (енумы) для фронтенда. "
                   "Включает типы доставки, статусы заказов, типы фильтров атрибутов и рейтинги отзывов.",
        tags=["Справочники"],
        responses={
            200: {
                "description": "Успешное получение справочников",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "delivery_types": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string", "description": "Значение енума"},
                                        "label": {"type": "string", "description": "Отображаемое название"}
                                    }
                                },
                                "description": "Типы доставки (Минск, Беларусь, самовывоз)"
                            },
                            "attribute_filter_types": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                        "label": {"type": "string"}
                                    }
                                },
                                "description": "Типы фильтров атрибутов (checkbox, select, range и т.д.)"
                            },
                            "review_ratings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "integer"},
                                        "label": {"type": "string"}
                                    }
                                },
                                "description": "Рейтинги отзывов (1-5 звезд)"
                            }
                        }
                    }
                }
            }
        }
    ),
)
@extend_schema_view(
    list=extend_schema(
        summary="Получить список баннеров",
        description="Возвращает список всех активных баннеров для отображения на сайте. "
                   "Включает изображения, заголовки, описания и ссылки.",
        tags=["Контент"],
    ),
    retrieve=extend_schema(
        summary="Получить баннер по ID",
        description="Возвращает детальную информацию о конкретном баннере.",
        tags=["Контент"],
    ),
    create=extend_schema(
        summary="Создать новый баннер",
        description="Создает новый баннер для отображения на сайте. Требует права администратора.",
        tags=["Контент"],
    ),
    update=extend_schema(
        summary="Обновить баннер",
        description="Полностью обновляет информацию о баннере. Требует права администратора.",
        tags=["Контент"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить баннер",
        description="Частично обновляет информацию о баннере. Требует права администратора.",
        tags=["Контент"],
    ),
    destroy=extend_schema(
        summary="Удалить баннер",
        description="Удаляет баннер. Требует права администратора.",
        tags=["Контент"],
    ),
)
class BannerViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с баннерами"""
    queryset = models.Banner.objects.all()
    serializer_class = auth_serializers.BannerSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (parsers.MultiPartParser, JSONParser)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny,)

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список видео",
        description="Возвращает список всех активных видео для отображения на сайте. "
                   "Включает видеофайлы, превью, заголовки и описания.",
        tags=["Контент"],
    ),
    retrieve=extend_schema(
        summary="Получить видео по ID",
        description="Возвращает детальную информацию о конкретном видео.",
        tags=["Контент"],
    ),
    create=extend_schema(
        summary="Создать новое видео",
        description="Создает новое видео для отображения на сайте. Требует права администратора.",
        tags=["Контент"],
    ),
    update=extend_schema(
        summary="Обновить видео",
        description="Полностью обновляет информацию о видео. Требует права администратора.",
        tags=["Контент"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить видео",
        description="Частично обновляет информацию о видео. Требует права администратора.",
        tags=["Контент"],
    ),
    destroy=extend_schema(
        summary="Удалить видео",
        description="Удаляет видео. Требует права администратора.",
        tags=["Контент"],
    ),
)
class VideoViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с видео"""
    queryset = models.Video.objects.all()
    serializer_class = auth_serializers.VideoSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (parsers.MultiPartParser, JSONParser)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny,)

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список контактов",
        description="Возвращает список всех контактных данных компании. "
                   "Включает адреса, телефоны, email, время работы и другую контактную информацию.",
        tags=["Контакты"],
    ),
    retrieve=extend_schema(
        summary="Получить контакт по ID",
        description="Возвращает детальную информацию о конкретном контакте.",
        tags=["Контакты"],
    ),
    create=extend_schema(
        summary="Создать новый контакт",
        description="Создает новую контактную информацию. Требует права администратора.",
        tags=["Контакты"],
    ),
    update=extend_schema(
        summary="Обновить контакт",
        description="Полностью обновляет контактную информацию. Требует права администратора.",
        tags=["Контакты"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить контакт",
        description="Частично обновляет контактную информацию. Требует права администратора.",
        tags=["Контакты"],
    ),
    destroy=extend_schema(
        summary="Удалить контакт",
        description="Удаляет контактную информацию. Требует права администратора.",
        tags=["Контакты"],
    ),
)
class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с контактами"""
    queryset = models.Contact.objects.all()
    serializer_class = auth_serializers.ContactSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = (AllowAny,)

        return super(self.__class__, self).get_permissions()


@extend_schema_view(
    get=extend_schema(
        summary="Получить справочники",
        description="Возвращает все доступные справочники (енумы) для фронтенда. "
                   "Включает типы доставки, статусы заказов, типы фильтров атрибутов и рейтинги отзывов.",
        tags=["Справочники"],
        responses={
            200: {
                "description": "Успешное получение справочников",
                "content": {
                    "application/json": {
                        "type": "object",
                        "properties": {
                            "delivery_types": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string", "description": "Значение енума"},
                                        "label": {"type": "string", "description": "Отображаемое название"}
                                    }
                                },
                                "description": "Типы доставки (Минск, Беларусь, самовывоз)"
                            },
                            "attribute_filter_types": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                        "label": {"type": "string"}
                                    }
                                },
                                "description": "Типы фильтров атрибутов (checkbox, select, range и т.д.)"
                            },
                            "review_ratings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "integer"},
                                        "label": {"type": "string"}
                                    }
                                },
                                "description": "Рейтинги отзывов (1-5 звезд)"
                            }
                        }
                    }
                }
            }
        }
    ),
)
class EnumsView(APIView):
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
