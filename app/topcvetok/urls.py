from django.urls import include, path
from rest_framework.routers import DefaultRouter

from topcvetok import views

router = DefaultRouter(trailing_slash=False)
router.register(r"attribute-types", views.AttributeTypeViewSet, basename="attribute-types")
router.register(r"attributes", views.AttributeViewSet, basename="attributes")
router.register(r"product-attributes", views.ProductAttributeViewSet, basename="product-attributes")
router.register(r"products", views.ProductViewSet, basename="products")
router.register(r"services", views.ServiceViewSet, basename="services")
router.register(r"payment-methods", views.PaymentMethodViewSet, basename="payment-methods")
router.register(r"delivery-methods", views.DeliveryMethodViewSet, basename="delivery-methods")
router.register(r"orders", views.OrderViewSet, basename="orders")
router.register(r"reviews", views.ReviewViewSet, basename="reviews")

urlpatterns = [
    # Авторизация
    path("login/", views.Login.as_view()),
    path("logout/", views.Logout.as_view()),
    
    # Фильтры
    path("filter-options/", views.FilterOptionsView.as_view(), name="filter-options"),
    path("enums/", views.EnumsView.as_view(), name="enums"),
    
    # Цены
    path("calculate-price/", views.CalculatePriceView.as_view(), name="calculate-price"),
    path("calculate-delivery-price/", views.CalculateDeliveryPriceView.as_view(), name="calculate-delivery-price"),
    
    path("", include(router.urls)),
]
