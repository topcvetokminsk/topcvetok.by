from django.urls import include, path
from rest_framework.routers import DefaultRouter

from topcvetok import views

# Роутер для админ-панели (требует авторизации)
admin_router = DefaultRouter(trailing_slash=False)
admin_router.register(r"attribute-types", views.AttributeTypeViewSet, basename="admin-attribute-types")
admin_router.register(r"attributes", views.AttributeViewSet, basename="admin-attributes")
admin_router.register(r"product-attributes", views.ProductAttributeViewSet, basename="admin-product-attributes")
admin_router.register(r"services", views.ServiceViewSet, basename="admin-services")
admin_router.register(r"payment-methods", views.PaymentMethodViewSet, basename="admin-payment-methods")
admin_router.register(r"delivery-methods", views.DeliveryMethodViewSet, basename="admin-delivery-methods")
admin_router.register(r"orders", views.OrderViewSet, basename="admin-orders")
admin_router.register(r"reviews", views.ReviewViewSet, basename="admin-reviews")

# Роутер для публичного API (без авторизации)
public_router = DefaultRouter(trailing_slash=False)
public_router.register(r"products", views.ProductViewSet, basename="products")
public_router.register(r"attribute-types", views.AttributeTypeViewSet, basename="attribute-types")
public_router.register(r"attributes", views.AttributeViewSet, basename="attributes")
public_router.register(r"services", views.PublicServiceViewSet, basename="public-services")
public_router.register(r"payment-methods", views.PublicPaymentMethodViewSet, basename="public-payment-methods")
public_router.register(r"delivery-methods", views.PublicDeliveryMethodViewSet, basename="public-delivery-methods")
public_router.register(r"cart", views.CartViewSet, basename="cart")

urlpatterns = [
    # Авторизация
    path("login/", views.Login.as_view()),
    path("logout/", views.Logout.as_view()),
    
    # Заявки
    path('request-note/', views.RequestNote.as_view(), name='request-note'),
    
    # Фильтры
    path("filter-options/", views.FilterOptionsView.as_view(), name="filter-options"),
    path("enums/", views.EnumsView.as_view(), name="enums"),
    
    # Цены
    path("calculate-price/", views.CalculatePriceView.as_view(), name="calculate-price"),
    path("calculate-delivery-price/", views.CalculateDeliveryPriceView.as_view(), name="calculate-delivery-price"),
    
    # Заказы
    path("orders/create/", views.OrderCreateView.as_view(), name="order-create"),
    
    
    # Админ API
    path("admin/", include(admin_router.urls)),
    
    # Публичный API
    path("", include(public_router.urls)),
]
