# Django Modules
from django.urls import path, include

# DRF Modules
from rest_framework.routers import DefaultRouter

# Project Modules
from .views import CustomUserViewSet


router: DefaultRouter = DefaultRouter (

)
router.register(
    prefix='users',
    basename='users',
    viewset=CustomUserViewSet
)

urlpatterns = [
    path('v1/', include(router.urls)),
]
