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
    # Добавляем название категории, чтобы фронтенд мог группировать блюда
    category_name = CharField(source='category.name', read_only=True)

    class Meta:
        model = Dish
        fields = (
            'id',
            'category',
            'category_name', # Это поле критично для группировки в App.js
            'name',
            'description',
            'price',
            'calories',
            'image',
        )


# class DailyMenuSerializer(ModelSerializer):
#     # Добавляем вложенный сериализатор, чтобы получить объекты блюд, а не их ID
#     dishes = DishSerializer(many=True, read_only=True)
    
#     # Достаем название столовой (опционально, для отладки)
#     canteen_name = CharField(source='canteen.name', read_only=True)

#     class Meta:
#         model = DailyMenu
#         fields = (
#             'id',
#             'canteen',
#             'canteen_name',
#             'date',
#             'dishes', # Теперь здесь будут объекты
#         )


class DailyMenuSerializer(ModelSerializer):
    # Для отображения на фронте (read_only=True)
    dishes_details = DishSerializer(source='dishes', many=True, read_only=True)
    
    class Meta:
        model = DailyMenu
        fields = (
            'id', 
            'canteen', 
            'date', 
            'dishes',         # Сюда фронтенд будет слать список ID [1, 2, 3]
            'dishes_details', # А отсюда забирать полные объекты
        )
        extra_kwargs = {
            'dishes': {'write_only': True} # Мы только пишем ID, но не читаем их в этом поле
        }