from django.contrib import admin
from .models import Category, Product, ProductKey


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(ProductKey)
class ProductKeyAdmin(admin.ModelAdmin):
    list_display = ('product',)
    search_fields = ('product__name',)