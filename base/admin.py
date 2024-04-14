from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CurrencyConversionRate,
    OwnedStock,
    Stock,
    Transaction,
    Transfer,
    User,
)

# Register your models here.


class CustomUserAdmin(UserAdmin):
    # Define the fields to be displayed in the change list
    list_display = ("username", "email", "cash", "tz", "hc", "is_staff", "is_active")

    # Define the fields to be used in the search bar
    search_fields = ("username", "email", "tz", "hc")

    # Customize other admin options as needed
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("email", "cash", "tz", "hc")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register([Transaction, OwnedStock, Stock, Transfer, CurrencyConversionRate])
