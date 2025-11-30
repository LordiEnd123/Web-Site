from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),
    path('catalog/', views.catalog, name='catalog'),

    # Корзина
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    # Авторизация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Страница товара
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path("register/", views.register_view, name="register"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.password_change_view, name="password_change"),
    path("profile/upload-avatar/", views.upload_avatar, name="upload_avatar"),

    path("checkout/", views.checkout, name="checkout"),
]
