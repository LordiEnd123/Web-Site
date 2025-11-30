from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Product, Category, CustomUser
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileForm, PasswordChangeCustomForm
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash

from .forms import ProfileForm, PasswordChangeCustomForm

# === Главная страница ===
def home(request):
    products = Product.objects.filter(is_available=True)[:6]  # популярные товары
    categories = Category.objects.all()
    return render(request, 'store/index.html', {
        'products': products,
        'categories': categories
    })


# === Каталог ===
def catalog(request):
    # Базовый запрос: только доступные товары
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    # ---------- фильтр по категории ----------
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # ---------- фильтр по цене ----------
    price_min = request.GET.get("min_price")
    price_max = request.GET.get("max_price")

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    # ---------- сортировка ----------
    sort = request.GET.get("sort")
    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "new":
        products = products.order_by("-created_at")
    # если sort пустой или что-то другое — оставляем порядок по умолчанию

    # ВАЖНО: передаём request в контекст, чтобы шаблон мог вернуть значения в инпуты
    return render(request, "store/catalog.html", {
        "products": products,
        "categories": categories,
        "request": request,
    })

# === Регистрация ===
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # до подтверждения почты не даём логиниться
            user.is_active = False
            user.save()

            # генерим ссылку для подтверждения
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verify_url = request.build_absolute_uri(
                reverse("verify_email", kwargs={"uidb64": uid, "token": token})
            )

            subject = "Подтверждение регистрации на Digital Nexus"
            message = render_to_string(
                "store/email_verification.html",
                {"user": user, "verify_url": verify_url},
            )

            email = EmailMessage(subject, message, to=[user.email])
            email.send(fail_silently=True)

            return render(
                request,
                "store/registration_pending.html",
                {"email": user.email},
            )
    else:
        form = RegisterForm()

    return render(request, "store/register.html", {"form": form})

# === Вход ===
from django.contrib.auth import authenticate

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})


# === Выход ===
def logout_view(request):
    logout(request)
    return redirect('index')


# === Профиль ===
@login_required
def profile_view(request):
    user = request.user

    if request.method == "POST":
        # имена полей такие же, как в шаблоне profile.html
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.city = request.POST.get("city", user.city)

        avatar = request.FILES.get("avatar")
        if avatar:
            user.avatar = avatar

        user.save()
        messages.success(request, "Профиль обновлён ✅")
        return redirect("profile")

    return render(request, "store/profile.html", {"user": user})

from django.shortcuts import get_object_or_404

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "store/product_detail.html", {"product": product})


from django.shortcuts import get_object_or_404

# ----------------- КОРЗИНА -----------------

def cart_view(request):
    cart = request.session.get("cart", {})
    products = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        products.append({
            "product": product,
            "quantity": quantity,
            "subtotal": product.price * quantity,
        })
        total_price += product.price * quantity

    return render(request, "store/cart.html", {
        "products": products,
        "total_price": total_price,
    })


def cart_add(request, product_id):
    cart = request.session.get("cart", {})
    product = get_object_or_404(Product, id=product_id)

    current_qty = cart.get(str(product_id), 0)
    available = product.available_keys_count()

    if current_qty < available:
        cart[str(product_id)] = current_qty + 1
        request.session["cart"] = cart
    else:
        messages.error(request, "Недостаточно ключей в наличии ❗")

    return redirect("cart")



def cart_remove(request, product_id):
    cart = request.session.get("cart", {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session["cart"] = cart
    return redirect("cart")

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Почта успешно подтверждена, вы вошли в аккаунт.")
        return redirect("index")
    else:
        messages.error(request, "Ссылка подтверждения недействительна или устарела.")
        return redirect("login")

@login_required
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль успешно изменён ✅")
            return redirect("profile")
    else:
        form = PasswordChangeCustomForm(user=request.user)

    return render(request, "store/password_change.html", {"form": form})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
@login_required
def upload_avatar(request):
    if request.method == "POST" and request.FILES.get("avatar"):
        user = request.user
        user.avatar = request.FILES["avatar"]
        user.save()
        return JsonResponse({"status": "ok", "url": user.avatar.url})

    return JsonResponse({"status": "error"}, status=400)


@login_required
def checkout(request):
    cart = request.session.get("cart", {})
    bought_keys = []

    for product_id, qty in cart.items():
        product = get_object_or_404(Product, id=product_id)

        for _ in range(qty):
            key = product.get_free_key()
            if not key:
                messages.error(request, f"Не хватает ключей для {product.name}")
                return redirect("cart")

            # помечаем ключ как использованный
            key.is_active = False
            key.save()

            # сохраняем продукт и сам код ключа
            bought_keys.append((product, key.key_value))

    # очищаем корзину
    request.session["cart"] = {}

    return render(request, "store/checkout_success.html", {
        "bought_keys": bought_keys,
    })
