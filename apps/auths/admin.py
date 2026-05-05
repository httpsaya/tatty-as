# Django Modules
from django.contrib.admin import register, ModelAdmin

# Project Modules
from apps.auths.models import CustomUser, School


@register(CustomUser)
class UserAdminModel(ModelAdmin):
     """Admin model for CustomUser."""
     list_display = (
        "email",
        "full_name",
        'school',
        "is_active",
        "is_staff",
        "is_superuser",
    )
     search_fields = ("email", "full_name", 'school__name')
     list_filter = ("is_active", "is_staff", "is_superuser")
     ordering = ("email",)


@register(School)
class CompanyAdminModel(ModelAdmin):
     """Company model for CustomUser."""
     list_display=(
          "id",
          "name"
        )
     