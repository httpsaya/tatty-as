# Django Modules
from django.urls import path, include

# DRF Modules
from rest_framework.routers import DefaultRouter

# Project Modules
from .views import CanteenViewSet, DishViewSet, DailyMenuViewSet, DishReactionViewSet

# your_app/urls.py
from django.urls import path
from . import views


router: DefaultRouter = DefaultRouter()

router.register(
    prefix='canteens',
    basename='canteens',
    viewset=CanteenViewSet
)
router.register(
    prefix='dishes',
    basename='dishes',
    viewset=DishViewSet
)
router.register(
    prefix='daylymenu',
    basename='daylymenu',
    viewset=DailyMenuViewSet
)
router.register(
    prefix='reactions', 
    basename='reactions', 
    viewset=DishReactionViewSet
)

urlpatterns = [
    path('', include(router.urls)),
]
