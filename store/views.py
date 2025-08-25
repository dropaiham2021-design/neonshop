# store/views.py
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F

# --- models (some may not exist; we degrade gracefully) ---
from .models import Product
try:
    from .models import Variant
except Exception:
    Variant = None  # session fallback will skip if missing

try:
    from .models import Cart, CartItem
except Exception:
    Cart = CartItem = None  # session cart fallback

# Optional coupon model (if you created it)
try:
    from .models import Coupon
except Exception:
    Coupon = None


# =========================================
# INVITES / AUTH
# =========================================


def invite(request, token):
    """Store the invite token and show signup."""
    request.session["invite_token"] = token
    messages.info(request, "Invite verified. Please create your account.")
    return render(request, "auth_signup.html", {"invite_token": token})

@csrf_protect
def signup_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()

        if not username or not password:
            messages.error(request, "Please enter a username and password.")
            return render(request, "auth_signup.html", {"prefill_username": username})

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "auth_signup.html", {"prefill_username": username})

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        messages.success(request, "Welcome! Your account was created.")
        return redirect("home")
    return render(request, "auth_signup.html")

@csrf_protect
def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in.")
            return redirect(request.GET.get("next") or "home")
        messages.error(request, "Invalid credentials or user inactive.")
    return render(request, "auth_login.html")

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("login")

def verify_email(request, token: str):
    """Minimal email verification stub."""
    request.session["email_verified"] = True
    messages.success(request, "Email verified.")
    return redirect("login")


# =========================================
# PAGES
# =========================================

def home(request):
    products = Product.objects.all().order_by("-id")
    return render(request, "home.html", {"products": products})

def product_detail(request, slug):
    p = get_object_or_404(Product, slug=slug)

    # Normalize colors (avoid mismatch)
    def normalize_color(c):
        return (c or "One").strip().lower()

    # --- Variants ---
    variants = list(p.variants.all().order_by('price_gross_cents', 'id'))
    colors = []
    vmap = {}

    for v in variants:
        raw_color = (v.attrs or {}).get('color') or 'One'
        color = normalize_color(raw_color)
        size = (v.attrs or {}).get('size') or ''

        if raw_color not in colors:  # keep original name for swatches
            colors.append(raw_color)

        vmap.setdefault(color, []).append({
            'id': v.id,
            'size': size,
            'price': getattr(v, 'price_gross_cents', 0) or 0,
            'stock': v.stock,
        })

    # --- Images ---
    imap = {}
    generic = []

    for img in p.images.all().order_by('sort_order', 'id'):
        payload = {'url': img.url, 'alt': img.alt or p.title}
        if img.color:
            imap.setdefault(normalize_color(img.color), []).append(payload)
        else:
            generic.append(payload)

    # Fallbacks
    for c in [normalize_color(c) for c in colors] or ['one']:
        if c not in imap:
            imap[c] = generic if generic else [{
                "url": "/static/img/placeholder.png",
                "alt": "No image available",
            }]

    return render(request, 'product_detail.html', {
        'p': p,
        'colors': colors or ['One'],     # original names for buttons
        'variant_map': vmap,             # normalized keys
        'images_map': imap,              # normalized keys
    })


# =========================================
# QR INVITES
# =========================================


from django.conf import settings
from django.shortcuts import render

def qr_invite(request, token):
    base = getattr(settings, "PUBLIC_BASE_URL", request.build_absolute_uri("/")).rstrip("/")
    target = f"{base}/invite/{token}"
    return render(request, "qr_invite.html", {"target_url": target})


# =========================================
# CART (DB cart if present, else session fallback)
# =========================================

# ---- helpers ----
def _has_db_cart():
    return all([Cart, CartItem, Variant])

def _get_cart_session_dict(request):
    """Session cart shape: {'1': qty, '7': qty, ...} (keys are variant IDs as str)."""
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    return cart

def _save_cart_session_dict(request, cart):
    request.session["cart"] = cart
    request.session.modified = True

def _get_cart(request):
    """Return a DB cart if models exist; else None (session mode)."""
    if not _has_db_cart():
        return None

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        # if your Cart model has a session_key field, use it; otherwise
        # just create a single cart per anonymous session by pk
        cid = request.session.get("cart_id")
        if cid:
            try:
                cart = Cart.objects.get(pk=cid)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session["cart_id"] = cart.pk
        else:
            cart = Cart.objects.create()
            request.session["cart_id"] = cart.pk
    return cart

def add_to_cart(request, variant_id: int):
    """Add one unit of the variant to cart."""
    if _has_db_cart():
        cart = _get_cart(request)
        v = get_object_or_404(Variant, pk=variant_id)
        item, created = CartItem.objects.get_or_create(cart=cart, variant=v, defaults={"quantity": 1})
        if not created:
            item.quantity += 1
            item.save()
    else:
        # session fallback
        cart = _get_cart_session_dict(request)
        key = str(variant_id)
        cart[key] = cart.get(key, 0) + 1
        _save_cart_session_dict(request, cart)

    messages.success(request, "Added to cart.")
    return redirect("cart")

def remove_from_cart(request, item_id: int):
    """Remove an item. In DB-mode item_id is CartItem PK; in session-mode it is variant_id."""
    if _has_db_cart():
        try:
            CartItem.objects.filter(pk=item_id).delete()
            messages.info(request, "Item removed.")
        except Exception:
            messages.error(request, "Could not remove item.")
    else:
        cart = _get_cart_session_dict(request)
        key = str(item_id)
        if key in cart:
            cart.pop(key)
            _save_cart_session_dict(request, cart)
            messages.info(request, "Item removed.")
    return redirect("cart")

def _apply_coupon_if_any(request, cents_subtotal):
    """
    Returns (discount_cents, applied_coupon_or_None).
    Works if you have a Coupon model with:
      - objects.valid() queryset method and
      - discount_amount(subtotal_cents) -> cents
    Otherwise, it safely applies nothing.
    """
    code = (request.session.get("coupon_code") or "").strip()
    if not code or not Coupon:
        return 0, None
    try:
        qs = getattr(Coupon.objects, "valid", lambda: Coupon.objects).callable if hasattr(Coupon.objects, "valid") else Coupon.objects
    except Exception:
        qs = Coupon.objects

    try:
        # prefer a .valid() queryset if you built it; else plain get()
        try:
            valid_qs = Coupon.objects.valid()
        except Exception:
            valid_qs = Coupon.objects.all()
        coupon = valid_qs.get(code__iexact=code)
        if hasattr(coupon, "discount_amount"):
            return coupon.discount_amount(cents_subtotal), coupon
        # simple fallback: 10% off if percent_off exists
        if hasattr(coupon, "percent_off") and coupon.percent_off:
            return int(cents_subtotal * (coupon.percent_off / 100.0)), coupon
        if hasattr(coupon, "amount_off_cents") and coupon.amount_off_cents:
            return min(coupon.amount_off_cents, cents_subtotal), coupon
        return 0, coupon
    except Exception:
        # invalid/expired -> drop it
        request.session.pop("coupon_code", None)
        return 0, None

def apply_coupon(request):
    """POST endpoint to apply a promo code (stored in session)."""
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        if not code:
            messages.error(request, "Enter a promo code.")
        else:
            request.session["coupon_code"] = code
            request.session.modified = True
            # We validate in cart_view so bad codes clean themselves up
            messages.success(request, "Promo code applied.")
    return redirect("cart")

def cart_view(request):
    """
    Build a cart context that the template expects:
      items: each has .variant (with .product), .quantity, .unit (€, float), .line (€, float)
      net, vat, gross (floats in €)
      discount (float €) + applied_coupon (optional)
    """
    items = []
    cents_subtotal = 0

    if _has_db_cart():
        cart = _get_cart(request)
        db_items = (CartItem.objects
                    .filter(cart=cart)
                    .select_related("variant", "variant__product"))
        for it in db_items:
            unit_cents = getattr(it.variant, "price_gross_cents", 0) or 0
            line_cents = unit_cents * it.quantity
            it.unit = unit_cents / 100.0
            it.line = line_cents / 100.0
            items.append(it)
            cents_subtotal += line_cents
    else:
        # session fallback
        sess = _get_cart_session_dict(request)
        ids = [int(k) for k in sess.keys()] if sess else []
        var_qs = Variant.objects.select_related("product").filter(id__in=ids) if Variant and ids else []
        variants_by_id = {v.id: v for v in var_qs}
        for sid, qty in (sess or {}).items():
            vid = int(sid)
            v = variants_by_id.get(vid)
            if not v:
                continue
            unit_cents = getattr(v, "price_gross_cents", 0) or 0
            line_cents = unit_cents * qty
            # lightweight item mimic
            class _I:
                pass
            it = _I()
            it.variant = v
            it.quantity = qty
            it.unit = unit_cents / 100.0
            it.line = line_cents / 100.0
            # add a pseudo id so "remove" link can work (uses variant_id in session mode)
            it.id = vid
            items.append(it)
            cents_subtotal += line_cents

    # promo code
    discount_cents, applied_coupon = _apply_coupon_if_any(request, cents_subtotal)
    cents_after_discount = max(0, cents_subtotal - discount_cents)

    # VAT maths
    vat_rate = float(getattr(settings, "GERMANY_STANDARD_VAT", 0.19))
    prices_include_vat = bool(getattr(settings, "PRICES_INCLUDE_VAT", True))

    if prices_include_vat:
        gross = cents_after_discount / 100.0
        net = gross / (1 + vat_rate) if (1 + vat_rate) else gross
        vat = gross - net
    else:
        net = cents_after_discount / 100.0
        vat = net * vat_rate
        gross = net + vat

    ctx = {
        "items": items,
        "net": net,
        "vat": vat,
        "gross": gross,
        "vat_rate": vat_rate * 100.0,  # percent for display
        "discount": (discount_cents / 100.0) if discount_cents else 0.0,
        "applied_coupon": applied_coupon,
    }
    return render(request, "cart.html", ctx)


# =========================================
# CHECKOUT / PAYMENTS (placeholders)
# =========================================

def checkout_view(request):
    try:
        return render(request, "checkout.html")
    except Exception:
        return HttpResponse("Checkout coming soon.", content_type="text/plain")

@csrf_exempt
def stripe_create_checkout(request):
    return JsonResponse({"ok": False, "error": "Stripe not wired yet"}, status=400)

def stripe_success(request):
    messages.success(request, "Stripe success (placeholder).")
    return redirect("home")

def stripe_cancel(request):
    messages.info(request, "Stripe canceled.")
    return redirect("checkout")

@csrf_exempt
def paypal_create_order(request):
    return JsonResponse({"ok": False, "error": "PayPal not wired yet"}, status=400)

@csrf_exempt
def paypal_capture_order(request, order_id: str):
    return JsonResponse({"ok": False, "error": f"PayPal capture not wired for {order_id}"}, status=400)

@csrf_exempt
def coinbase_create_charge(request):
    return JsonResponse({"ok": False, "error": "Coinbase not wired yet"}, status=400)

def order_success(request, order_id: int):
    return HttpResponse(f"Order {order_id} placed. (placeholder)", content_type="text/plain")

def remove_coupon(request):
    request.session.pop("coupon_code", None)
    request.session.modified = True
    messages.info(request, "Promo code removed.")
    return redirect("cart")
