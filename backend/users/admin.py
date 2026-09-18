from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Company, SellerPrivileges, VerificationCode


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Entreprise & Rôles', {
            'fields': ('company', 'user_type', 'is_primary_admin', 'phone', 'phone_verified', 'email_verified', 'two_factor_enabled')
        }),
    )
    list_display = ('username', 'email', 'user_type', 'company', 'is_primary_admin', 'phone', 'two_factor_enabled', 'is_staff')
    list_filter = ('user_type', 'is_primary_admin', 'company', 'is_staff', 'two_factor_enabled')
    search_fields = ('username', 'email', 'phone')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_username', 'created_by', 'currency', 'is_active', 'created_at')
    list_filter = ('is_active', 'currency', 'created_at')
    search_fields = ('name', 'company_username', 'slug')


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('target', 'code_type', 'code', 'user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('code_type', 'is_used', 'created_at')
    search_fields = ('target', 'code')


admin.site.register(User, CustomUserAdmin)
admin.site.register(SellerPrivileges)