# Python modules
from typing import Any, Optional

# Django Modules
from django.contrib.auth.password_validation import validate_password

# Django REST Framework
from rest_framework.serializers import (
    Serializer, 
    CharField, 
    EmailField, 
    IntegerField, 
    ListField,
    ModelSerializer,
    )
from rest_framework.exceptions import ValidationError

# Project modules
from apps.auths.models import CustomUser, Profile


# User Login
class UserLoginResponseSerializer(Serializer):
    """
    Serializer for user login response.
    """

    id = IntegerField()
    full_name = CharField()
    email = EmailField()
    access = CharField()
    refresh = CharField()
    school_name = CharField(source='school.name', read_only=True)
    

    class Meta:
        """Customization of the Serializer metadata."""

        fields = (
            "id",
            "full_name",
            "email",
            "access",
            "refresh",
            'school_name', 
        )


class UserLoginErrorsSerializer(Serializer):
    """
    Serializer for user login errors.
    """

    email = ListField(
        child=CharField(),
        required=False,
    )
    password = ListField(
        child=CharField(),
        required=False,
    )

    class Meta:
        """Customization of the Serializer metadata."""

        fields = (
            "email",
            "password",
        )


class UserLoginSerializer(Serializer):
    """
    Serializer for user login.
    """

    email = EmailField(
        required=True,
        max_length=CustomUser.EMAIL_MAX_LENGTH,
    )
    password = CharField(
        required=True,
        max_length=CustomUser.PASSWORD_MAX_LENGTH,
    )

    class Meta:
        """Customization of the Serializer metadata."""

        fields = (
            "email",
            "password",
        )

    def validate_email(self, value: str) -> str:
        """Validates the email field."""
        return value.lower()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validates the input data."""
        email: str = attrs["email"]
        password: str = attrs["password"]

        user: Optional[CustomUser] = CustomUser.objects.filter(email=email).first()

        if not user:
            raise ValidationError(
                detail={
                    "email": [f"User with email '{email}' does not exist."]
                }
            )

        if not user.check_password(raw_password=password):
            raise ValidationError(
                detail={
                    "password": ["Incorrect password."]
                }
            )

        attrs["user"] = user    

        return super().validate(attrs)
    

# User Registration
class RegistrationErrorsSerializer(Serializer):
    """
        Serializer for user login errors.
        """

    email = ListField(
        child=CharField(),
        required=False,
    )
    password = ListField(
        child=CharField(),
        required=False,
    )

    class Meta:
        """Customization of the Serializer metadata."""

        fields = (
            "email",
            "password",
        )


    password = CharField(
        required=True,
        write_only=True,
        min_length=CustomUser.PASSWORD_MIN_LENGTH,
        validators=[validate_password]
    )
    email = EmailField(
        required=True,
        max_length=CustomUser.EMAIL_MAX_LENGTH,
    )
    username = CharField(
        required=True,
        max_length=CustomUser.USERNAME_MAX_LENGTH,
    )
    full_name = CharField(
        required=True,
        max_length=CustomUser.FULL_NAME_MAX_LENGTH,
    )
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'full_name',
            'username',
            'email',
            'password'
        ]


class RegistrationSerializer(Serializer):

    password = CharField(
        required=True,
        write_only=True,
        min_length=CustomUser.PASSWORD_MIN_LENGTH,
        validators=[validate_password]
    )
    email = EmailField(
        required=True,
        max_length=CustomUser.EMAIL_MAX_LENGTH,
    )
    username = CharField(
        required=True,
        max_length=CustomUser.USERNAME_MAX_LENGTH,
    )
    full_name = CharField(
        required=True,
        max_length=CustomUser.FULL_NAME_MAX_LENGTH,
    )
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'full_name',
            'username',
            'email',
            'password'
        ]

    def create(self, validated_data: dict[str, Any]) -> CustomUser:
        return CustomUser.objects.create_user(**validated_data)


class HTTP405MethodNotAllowedSerializer(Serializer):
    """
    Serializer for HTTP 405 Method Not Allowed response.
    """

    detail = CharField()

    class Meta:
        """Customization of the Serializer metadata."""

        fields = (
            "detail",
        )


# User Profile 
class ProfileSerializer(ModelSerializer):
    # Добавляем поле школы из связанной модели User
    school = IntegerField(source='user.school.id', read_only=True)
    school_name = CharField(source='user.school.name', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'display_name',
            'bio',
            'location', 
            'interests',
            'is_verified',
            'avatar',
            'gender',
            'updated_at',
            'school',      # ID школы
            'school_name'  # Название школы
        ]
        read_only_fields = ['id', 'user', 'updated_at', 'school_name']


class UserWithProfileSerializer(ModelSerializer):
    """Serializer for user model with nested profile"""
    profile: ProfileSerializer = ProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'phone_number',
            'city',
            'country',
            'birthdate',
            'is_active',
            'is_staff',
            'date_joined',
            'last_login',
            'created_at',
            'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'date_joined', 'last_login']


class ProfileUpdateSerializer(ModelSerializer):
    # Поле для смены школы (передаем только ID)
    school_id = IntegerField(write_only=True, required=False)

    class Meta:
        model = Profile
        fields = [
            'display_name',
            'bio',
            'location',
            'interests', 
            'avatar',
            'gender',
            'school_id'
        ]

    def update(self, instance, validated_data):
        # Извлекаем school_id для обновления модели User
        school_id = validated_data.pop('school_id', None)
        if school_id:
            user = instance.user
            user.school_id = school_id
            user.save(update_fields=['school'])
        
        return super().update(instance, validated_data)


class UserProfileSerializer(ModelSerializer):
    # Поля из модели CustomUser (через source)
    school_id = IntegerField(source='user.school.id', read_only=True)
    school_name = CharField(source='user.school.name', read_only=True)
    email = EmailField(source='user.email', read_only=True)
    full_name = CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'display_name',
            'bio',
            'location', 
            'interests',
            'avatar',
            'gender',
            'school_id',
            'school_name',
            'email',
            'full_name'
        ]


class ProfileUpdateErrorsSerializer(Serializer):
    """
        Serializer for user login errors.
        """

    email = ListField(
        child=CharField(),
        required=False,
    )
    password = ListField(
        child=CharField(),
        required=False,
    )


  

