from django.shortcuts import render
from .models import Product, Category


def home(request):
    products = Product.objects.filter(is_available=True)[:6]  # популярные товары
    categories = Category.objects.all()
    return render(request, 'store/index.html', {
        'products': products,
        'categories': categories
    })


def catalog(request):
    products = Product.objects.filter(is_available=True)
    return render(request, 'store/catalog.html', {'products': products})
