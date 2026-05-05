# Python modules
from typing import Any
import time
import asyncio

# Django modules
from django.db.models import QuerySet, Model
from django.http.response import StreamingHttpResponse

# Django REST Framework
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK, 
    HTTP_400_BAD_REQUEST, 
    HTTP_405_METHOD_NOT_ALLOWED, 
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    )
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse

# Project modules
from apps.auths.models import CustomUser, Profile
from apps.auths.serializers import (
    UserLoginSerializer, 
    UserLoginResponseSerializer, 
    UserLoginErrorsSerializer, 
    HTTP405MethodNotAllowedSerializer,
    RegistrationSerializer,
    UserWithProfileSerializer,
    RegistrationErrorsSerializer,
    ProfileUpdateSerializer,
    ProfileSerializer,
    ProfileUpdateErrorsSerializer,
    )
from apps.abstracts.decorators import validate_serializer_data


class CustomUserViewSet(ViewSet):
    """
    ViewSet for handling CustomUser-related endpoints.
    """

    permission_classes = (IsAuthenticated,)

    @action(
        methods=("POST",),
        detail=False,
        url_path="login",
        url_name="login",
        permission_classes=(AllowAny,)
    )
    @validate_serializer_data(serializer_class=UserLoginSerializer)
    def login(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any]
    ) -> DRFResponse:

        serializer: UserLoginSerializer = kwargs["serializer"]

        user: CustomUser = serializer.validated_data.pop("user")

        # Generate JWT tokens
        refresh_token: RefreshToken = RefreshToken.for_user(user)
        access_token: str = str(refresh_token.access_token)

        return DRFResponse(
            data={
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "access": access_token,
                "refresh": str(refresh_token),
            },
            status=HTTP_200_OK
        )


    @action(
        methods=("GET",),
        detail=False,
        url_name="personal_info",
        url_path="personal_info",
        permission_classes=(IsAuthenticated,)
    )
    def fetch_personal_info(
        self, 
        request: DRFRequest, 
        *args: tuple[Any, ...], 
        **kwargs: dict[str, Any]
    ) -> DRFResponse:
        

        user: CustomUser = request.user 

        return DRFResponse(
            data={
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            },
            status=HTTP_200_OK
        )
    

    @extend_schema(
        summary="User Registration",
        request=RegistrationSerializer,
        responses={
            HTTP_201_CREATED: OpenApiResponse(
                description="User successfully registered.",
                response=UserWithProfileSerializer,
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid registration data.",
                response=RegistrationErrorsSerializer,
            ),
        }
    )
    @action(
        methods=('POST',),
        detail=False,
        url_path='register',
        url_name='register',
        permission_classes=(AllowAny,)
    )
    def register(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        serializer: RegistrationSerializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: CustomUser = serializer.save()

        refresh_token: RefreshToken = RefreshToken.for_user(user)
        access_token: str = str(refresh_token.access_token)

        return DRFResponse(
            data={
                'id': user.id,
                'email': user.email,
                'access': access_token,
                'refresh': str(refresh_token),
            },
            status=HTTP_200_OK
        )


    @extend_schema(
        summary="Retrieve or update user profile",
        request=ProfileUpdateSerializer,  # its used only for patch
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Profile retrieved (GET) or updated (PATCH) successfully.",
                response=ProfileSerializer,
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid data for updating profile (PATCH).",
                response=ProfileUpdateErrorsSerializer,
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication required.",
            ),
        }
    )
    @action(
        methods=('GET', 'PATCH'),
        detail=False,
        url_path='profile',
        url_name='profile',
        permission_classes=(IsAuthenticated,),
    )
    def profile(
            self,
            request: DRFRequest,
            *args: tuple[Any, ...],
            **kwargs: dict[str, Any],
    ) -> DRFResponse:
        user: CustomUser = request.user
        profile, created = Profile.objects.get_or_create(user=user)

        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK
            )

        elif request.method == 'PATCH':
            data = request.data.copy()


            if 'interests' in data:
                if isinstance(data['interests'], str):
                    import json
                    try:
                        data['interests'] = json.loads(data['interests'])
                    except json.JSONDecodeError:
                        data['interests'] = []
                elif not isinstance(data['interests'], list):
                    data['interests'] = []


            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
                profile.save(update_fields=['avatar'])

            serializer = ProfileUpdateSerializer(
                instance=profile,
                data=data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            profile.refresh_from_db()
            return DRFResponse(ProfileSerializer(profile).data, status=HTTP_200_OK)

    # def get_chat_messages(self, request: DRFRequest, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> DRFResponse:
        
    #     chat_id: int | None  = int(request.data.get("chat_id"))
    #     last_message_id: int | None = int(request.data.get("last_message_id"))

    #     messages: QuerySet[Model] = Model.objects.filter(chat_id=chat_id)
    #     if last_message_id:
    #         messages = Model.objects.filter(id__gt=last_message_id)

    #     response_msgs: list[dict] = []

    #     message: Model
    #     for message in messages:
    #         response_msgs.append({
    #             "id": message.id,
    #             "msg": message.text
    #         })


    #     return DRFResponse(
    #         data={"messages": response_msgs},
    #         status=HTTP_200_OK
    #     )

   