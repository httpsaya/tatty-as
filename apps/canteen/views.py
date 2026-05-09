# Python Modules
from typing import Any

# Django Modules 
from django.utils import timezone

# DRF Modules
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
)

# Project Modules
from .serializers import (
    CanteenSerializer, 
    FoodCategorySerializer, 
    DailyMenuSerializer, 
    DishSerializer
)
from .models import Canteen, Dish, DailyMenu, FoodCategory, DishReaction, ReactionType


class CanteenViewSet(ViewSet):
    """Canteen Endpoints"""

    def get_queryset(self):
        return Canteen.objects.all()

    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    

    def destroy(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        try:
            canteen: Canteen = self.get_queryset().get(id=kwargs['pk'])
        except Canteen.DoesNotExist:
            return DRFResponse(
                data={
                    'detail': f"Post with that id={kwargs['pk']} does not exists"
                },
                status=HTTP_404_NOT_FOUND
            )
        
        canteen.delete()

        return DRFResponse(
            status=HTTP_204_NO_CONTENT
        )


    def list(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        
        """Get list of canteens with filtering"""

        queryset = self.get_queryset()
        
        ordering = request.query_params.get('-created_at')
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))

        serializer: CanteenSerializer = CanteenSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK
        )
    
    
    def create(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """ Creating POST request"""

        serializer: CanteenSerializer = CanteenSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return DRFResponse(
                data=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )
    

    def retrieve(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Get single canteen details"""
        try:
            canteen = self.get_queryset().get(id=kwargs['pk'])
        except Canteen.DoesNotExist:
            return DRFResponse(
                data={'detail': "Canteen not found"},
                status=HTTP_404_NOT_FOUND
            )

        serializer = CanteenSerializer(canteen, context={'request': request})
        return DRFResponse(data=serializer.data, status=HTTP_200_OK)


class DishViewSet(ViewSet):
    
    def get_queryset(self):
        return Dish.objects.all()

    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    

    def destroy(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        try:
            dish: Dish = self.get_queryset().get(id=kwargs['pk'])
        except Dish.DoesNotExist:
            return DRFResponse(
                data={
                    'detail': f"Dish with that id={kwargs['pk']} does not exists"
                },
                status=HTTP_404_NOT_FOUND
            )
        
        dish.delete()

        return DRFResponse(
            status=HTTP_204_NO_CONTENT
        )


    def list(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        
        """Get list of canteens with filtering"""

        queryset = self.get_queryset()
        
        ordering = request.query_params.get('-created_at')
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))

        serializer: DishSerializer = DishSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK
        )
    
    
    def create(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """ Creating POST request"""

        serializer: DishSerializer = DishSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return DRFResponse(
                data=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.save(author=request.user)

        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )


class DailyMenuViewSet(ViewSet):
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return DailyMenu.objects.none()
        
        print(f"[DEBUG] user={user}, school={getattr(user, 'school', None)}, is_superuser={user.is_superuser}")
        
        print(f"[DEBUG] All menus count: {DailyMenu.objects.count()}")
        
        if hasattr(user, 'school') and user.school:
            qs = DailyMenu.objects.filter(canteen__school=user.school)
            print(f"[DEBUG] Filtered by school menus count: {qs.count()}")
            return qs
        if user.is_superuser:
            return DailyMenu.objects.all()
        
        return DailyMenu.objects.none()
    
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    

    def destroy(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        try:
            daily_menu: DailyMenu = self.get_queryset().get(id=kwargs['pk'])
        except DailyMenu.DoesNotExist:
            return DRFResponse(
                data={
                    'detail': f"Daily Menu with that id={kwargs['pk']} does not exists"
                },
                status=HTTP_404_NOT_FOUND
            )
        
        daily_menu.delete()

        return DRFResponse(
            status=HTTP_204_NO_CONTENT
        )


    def list(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        
        """Get list of canteens with filtering"""

        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)
        
        # Используем __in, чтобы захватить обе даты
        queryset = self.get_queryset().filter(date__in=[today, tomorrow])

        
        ordering = request.query_params.get('-created_at')
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))

        serializer: DailyMenuSerializer = DailyMenuSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK
        )
    
    
    def create(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """ Creating POST request"""

        serializer: DailyMenuSerializer = DailyMenuSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return DRFResponse(
                data=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )


class DishReactionViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(
        self, 
        request: DRFRequest, 
        *args: tuple[Any, ...], 
        **kwargs: dict[str, Any],
        ) -> DRFResponse:

        """Получить все реакции на блюдо"""
        dish_id = request.query_params.get('dish_id')
        if not dish_id:
            return DRFResponse({'detail': 'dish_id required'}, status=HTTP_400_BAD_REQUEST)

        reactions = DishReaction.objects.filter(dish_id=dish_id).select_related('reaction_type')
        
        # Считаем по типам
        counts = {}
        for r in reactions:
            emoji = r.reaction_type.emoji
            counts[emoji] = counts.get(emoji, 0) + 1

        # Реакция текущего юзера
        my_reaction = DishReaction.objects.filter(
            dish_id=dish_id, user=request.user
        ).select_related('reaction_type').first()

        return DRFResponse({
            'counts': counts,
            'my_reaction': my_reaction.reaction_type.emoji if my_reaction else None,
        })


    def create(
        self, 
        request: DRFRequest, 
        *args: tuple[Any, ...], 
        **kwargs: dict[str, Any],
        ) -> DRFResponse:
        """Поставить или убрать реакцию"""
        dish_id = request.data.get('dish_id')
        emoji   = request.data.get('emoji')

        if not dish_id or not emoji:
            return DRFResponse({'detail': 'dish_id and emoji required'}, status=HTTP_400_BAD_REQUEST)

        try:
            dish          = Dish.objects.get(id=dish_id)
            reaction_type = ReactionType.objects.get(emoji=emoji)
        except Dish.DoesNotExist:
            return DRFResponse({'detail': 'Dish not found'}, status=HTTP_404_NOT_FOUND)
        except ReactionType.DoesNotExist:
            return DRFResponse({'detail': f'ReactionType with emoji {emoji} not found'}, status=HTTP_404_NOT_FOUND)

        existing = DishReaction.objects.filter(user=request.user, dish=dish).first()

        if existing:
            if existing.reaction_type == reaction_type:
                # Та же реакция — убираем
                existing.delete()
                my_reaction = None
            else:
                # Другая реакция — меняем
                existing.reaction_type = reaction_type
                existing.save()
                my_reaction = emoji
        else:
            DishReaction.objects.create(user=request.user, dish=dish, reaction_type=reaction_type)
            my_reaction = emoji

        # Возвращаем актуальные счётчики
        reactions = DishReaction.objects.filter(dish=dish).select_related('reaction_type')
        counts = {}
        for r in reactions:
            e = r.reaction_type.emoji
            counts[e] = counts.get(e, 0) + 1

        return DRFResponse({'counts': counts, 'my_reaction': my_reaction})