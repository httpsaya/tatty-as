# Django Module
from django.contrib.admin import (
    display, 
    ModelAdmin, 
    register
    )

# Project Module
from .models import (
    Canteen, 
    FoodCategory, 
    Dish, 
    DailyMenu
    )


@register(Canteen)
class CanteenAdminModel(ModelAdmin):
    list_display = [
        'school',
        'name',
        'is_open',
        'id',
    ]


@register(FoodCategory)
class FoodCategoryAdminModel(ModelAdmin):
    list_display = [
        'name',
        'id',
    ]


@register(Dish)
class DishAdminModel(ModelAdmin):
    list_display = [
        'category',
        'id',
        'name',
        'description',
        'price',
        'calories',
        'image',
    ]


@register(DailyMenu)
class DailyMenuAdminModel(ModelAdmin):
    list_display = [
        'id',
        'canteen',
        'date',
        'get_dishes',
    ]
    @display(description='Dishes')
    def get_dishes(self, obj):
        
        return ", ".join([dish.name for dish in obj.dishes.all()])

   
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('dishes')
