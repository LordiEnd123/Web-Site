from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser

# ---------- ГОРОДА ----------
class City(models.Model):
    name = models.CharField("Город", max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ---------- КАТЕГОРИИ ----------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ---------- ТОВАРЫ ----------
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    product_code = models.CharField(max_length=50, unique=True, verbose_name="Код товара (SKU)")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Категория")
    name = models.CharField(max_length=150, verbose_name="Название товара")
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="Изображение")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    stock = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    is_available = models.BooleanField(default=True, verbose_name="Доступен для покупки")
    sold_count = models.PositiveIntegerField(default=0, verbose_name="Продано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.product_code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def available_keys_count(self):
        return self.keys.filter(is_active=True).count()

    def get_free_key(self):
        return self.keys.filter(is_active=False).first()


# ---------- КЛЮЧИ / АККАУНТЫ ----------
class ProductKey(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="keys", verbose_name="Товар")
    key_value = models.CharField(max_length=255, unique=True, verbose_name="Ключ / данные аккаунта")
    is_active = models.BooleanField(default=True, verbose_name="Активен (не продан)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Ключ / Аккаунт"
        verbose_name_plural = "Ключи / Аккаунты"
        ordering = ["-created_at"]

    def __str__(self):
        status = "yes" if self.is_active else "no"
        return f"{status} {self.product.name} — {self.key_value[:20]}"

    def deactivate(self):
        self.is_active = False
        self.save()


# ---------- ПОЛЬЗОВАТЕЛЬ ----------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,              # ← чтобы можно было хранить NULL
        verbose_name="Телефон"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,              # ← тоже допускаем NULL
        verbose_name="Город"
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    def __str__(self):
        return self.username


