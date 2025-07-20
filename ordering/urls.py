from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddressViewSet, OrderViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet
router = DefaultRouter()
router.register(r'addresses', AddressViewSet,basename='address')
router.register(r'carts', CartViewSet,basename='cart')
router.register(r'orders/(?P<user_id>[^/.]+)', OrderViewSet, basename='orders')


urlpatterns = [
    path('', include(router.urls)),
]
