from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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
            from django.utils.text import slugify

            base_slug = slugify(self.name) or "city"
            slug = base_slug
            counter = 1

            # Пока есть такой slug у других городов — добавляем -1, -2, ...
            from store.models import City  # здесь можно избежать импорта, но так проще

            while City.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

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
        # Кол-во НЕпроданных ключей
        return self.keys.filter(is_sold=False).count()

    def get_free_key(self):
        # Берём первый свободный ключ
        return self.keys.filter(is_sold=False).first()


# ---------- КЛЮЧИ / АККАУНТЫ ----------
class ProductKey(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="keys",
        on_delete=models.CASCADE
    )
    key_value = models.CharField("Ключ", max_length=255, unique=True)
    is_active = models.BooleanField("Активен", default=True)
    is_sold = models.BooleanField("Продан", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} — {self.key_value}"


    def deactivate(self):
        self.is_active = False
        self.save()


# ---------- ПОЛЬЗОВАТЕЛЬ ----------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Телефон"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Город"
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    # --- новые поля ---
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Почта подтверждена"
    )
    pending_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Новая почта (ожидает подтверждения)"
    )

    def __str__(self):
        return self.username



class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новый"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_CANCELED, "Отменён"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма заказа",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус",
    )

    provider = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Платёжный провайдер",
    )
    provider_payment_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID платежа у провайдера",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    def __str__(self):
        return f"Заказ #{self.id} от {self.user}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    def subtotal(self):
        return self.price * self.quantity


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def recalc_product_counters(product):
    """
    Пересчитать склад и проданные для товара по его ключам.
    """
    stock = product.keys.filter(is_sold=False).count()
    sold = product.keys.filter(is_sold=True).count()

    product.stock = stock
    product.sold_count = sold
    product.save(update_fields=["stock", "sold_count"])


@receiver(post_save, sender=ProductKey)
def product_key_saved(sender, instance, **kwargs):
    recalc_product_counters(instance.product)


@receiver(post_delete, sender=ProductKey)
def product_key_deleted(sender, instance, **kwargs):
    recalc_product_counters(instance.product)
