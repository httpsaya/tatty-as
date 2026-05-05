# DRF Modules
from rest_framework.serializers import ModelSerializer, CharField

# Project Modules
from .models import Canteen, FoodCategory, Dish, DailyMenu


class CanteenSerializer(ModelSerializer):
    school_name = CharField(
        source='school.name', 
        read_only=True
    )

    class Meta:
        model = Canteen  
        fields = (
            "id",
            "school",
            "school_name",
            "name",
            "is_open",
        )


class FoodCategorySerializer(ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = (
            'id',
            'name',
        )


class DishSerializer(ModelSerializer):

    class Meta:
        model = Dish
        fields = (
            'id',
            'category',
            'name',
            'description',
            'price',
            'calories',
            'image',
        )


class DailyMenuSerializer(ModelSerializer):

    class Meta:
        model = DailyMenu
        fields = (
            'id',
            'canteen',
            'date',
            'dishes',
        )