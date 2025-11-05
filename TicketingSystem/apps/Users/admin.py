from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Order


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with role-based management.
    """
    list_display = ['email', 'username', 'user_type', 'is_active', 'is_staff', 'created_at']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'username')}),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
        ('User Type', {
            'fields': ('user_type', 'is_staff', 'is_superuser'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    def save_model(self, request, obj, form, change):
        """
        Ensure user_type and is_staff/is_superuser are in sync.
        """
        if obj.user_type == 'admin':
            obj.is_staff = True
        elif obj.user_type == 'agent':
            obj.is_staff = True
        super().save_model(request, obj, form, change)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_number', 'user', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'order_number', 'user__email', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
