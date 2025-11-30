from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Category, Product, ProductKey, CustomUser


# === КАСТОМНЫЙ ПОЛЬЗОВАТЕЛЬ ===
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('date_joined',)
    fieldsets = (
        ('Основная информация', {'fields': ('username', 'email', 'password')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Дополнительно', {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


# === КАТЕГОРИИ ===
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# === ТОВАРЫ ===
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    ordering = ('name',)


# === КЛЮЧИ / АККАУНТЫ ===
@admin.register(ProductKey)
class ProductKeyAdmin(admin.ModelAdmin):
    list_display = ('product',)
    search_fields = ('product__name',)
