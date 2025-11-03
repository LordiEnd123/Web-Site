from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),
    path('catalog/', views.catalog, name='catalog'),
]
