# Python Modules
from typing import Any

# DRF Modules
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
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
from .models import Canteen, Dish, DailyMenu, FoodCategory


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
        serializer.save(author=request.user)

        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )
    

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
        return DailyMenu.objects.all()

    
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

        queryset = self.get_queryset()
        
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
        serializer.save(author=request.user)

        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )
