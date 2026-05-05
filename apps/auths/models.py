# Python modules
from typing import Any

# Django modules
from django.db.models import (
    EmailField,
    CharField,
    BooleanField,
    ForeignKey,
    SET_NULL,
    ManyToManyField,
    OneToOneField,
    TextField,
    CASCADE,
    JSONField,
    URLField,
    DateTimeField,
)
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Project modules
from apps.abstracts.models import AbstractBaseModel
from apps.auths.validators import (
    validate_email_domain,
    validate_email_payload_not_in_full_name,
)


class CustomUserManager(BaseUserManager):
    """Custom User Manager to make database requests."""

    def __obtain_user_instance(
        self,
        email: str,
        full_name: str,
        username: str,
        password: str,
        **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """Get user instance."""
        if not email:
            raise ValidationError(
                message="Email field is required", code="email_empty"
            )
        if not full_name:
            raise ValidationError(
                message="Full name name is required.", code="full_name_empty"
            )

        new_user: 'CustomUser' = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            password=password,
            username=username,
            **kwargs,
        )
        return new_user

    def create_user(
        self,
        email: str,
        full_name: str,
        username: str,
        password: str,
        **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """Create Custom user. TODO where is this used?"""
        new_user: 'CustomUser' = self.__obtain_user_instance(
            email=email,
            full_name=full_name,
            password=password,
            username=username,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user

    def create_superuser(
        self,
        email: str,
        full_name: str,
        username: str,
        password: str,
        **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """Create super user. Used by manage.py createsuperuser."""
        new_user: 'CustomUser' = self.__obtain_user_instance(
            email=email,
            full_name=full_name,
            password=password,
            username=username,
            is_staff=True,
            is_superuser=True,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user


class School(AbstractBaseModel):
    """Company model representing a company in the system."""

    name = CharField(
        max_length=150,
        unique=True,
        verbose_name="Company name",
        help_text="Name of the company",
    )
    def __str__(self):
        return self.name

    class Meta:
        """Meta options for Company model."""

        verbose_name = "School"
        verbose_name_plural = "Schools"
        ordering = ["-created_at"]


class CustomUser(AbstractBaseUser, PermissionsMixin, AbstractBaseModel):
    """
    Custom user model extending AbstractBaseModel.
    """
    EMAIL_MAX_LENGTH = 150
    FULL_NAME_MAX_LENGTH = 150
    PASSWORD_MAX_LENGTH = 254
    PASSWORD_MIN_LENGTH = 8
    USERNAME_MAX_LENGTH = 30

    email = EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        db_index=True,
        validators=[validate_email_domain],
        verbose_name="Email address",
        help_text="User's email address",
    )
    username = CharField(
        max_length=30, 
        unique=True, 
        db_index=True,
        verbose_name="Username"
    )
    full_name = CharField(
        max_length=FULL_NAME_MAX_LENGTH,
        verbose_name="Full name",
    )
    password = CharField(
        max_length=PASSWORD_MAX_LENGTH,
        validators=[validate_password],
        verbose_name="Password",
        help_text="User's hash representation of the password",
    )
    # True iff the user is part of the corporoom team, allowing them to access the admin panel
    is_staff = BooleanField(
        default=False,
        verbose_name="Staff status",
        help_text="True if the user is an admin and has an access to the admin panel",
    )
    # True iff the user can make requests to the backend (include in company)
    is_active = BooleanField(
        default=True,
        verbose_name="Active status",
        help_text="True if the user is active and has an access to request data",
    )
    school = ForeignKey(
        to=School,
        on_delete=SET_NULL,
        null=True,
        verbose_name="School",
        help_text="School the user belongs to",
    )
    schools = ManyToManyField(
        to=School,
        related_name="users",
        blank=True,
        verbose_name="Companies",
        help_text="Companies the user belongs to",
    )

    REQUIRED_FIELDS = ["full_name", "username"]
    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    class Meta:
        """Meta options for CustomUser model."""

        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"
        ordering = ["-created_at"]

    def clean(self) -> None:
        """Validate the model instance before saving."""
        validate_email_payload_not_in_full_name(
            email=self.email,
            full_name=self.full_name,
        )
        return super().clean()
    
    
class Profile(AbstractBaseModel):
    """Profile model with common fields"""
    MAX_LENGTH = 100
    GENDER_MAX_LENGTH = 10

    user = OneToOneField(
        to = CustomUser,
        on_delete = CASCADE, 
        related_name = 'profile'
    )
    display_name = CharField(
        max_length = MAX_LENGTH,
        blank = True
    )
    bio = TextField(
        blank = True
        )
    location = CharField(
        max_length = MAX_LENGTH,
        blank = True
    )
    interests = JSONField(
        default = list, 
        blank = True
    )
    is_verified = BooleanField(
        default = False
        )
    avatar = URLField(
        blank = True,
        null = True
    )
    gender = CharField(
        max_length = GENDER_MAX_LENGTH,
        blank = True,
        choices=[
            ('male','Male'),
            ('female','Female'),
            ('other','Other'),
        ],
        default = 'other'
    )
    updated_at = DateTimeField(
        auto_now = True
    )

    def __str__(self):
        return self.display_name or self.user.email
