import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.urls import reverse

User = get_user_model()

class QRInvite(models.Model):
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    used_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=1)
    uses = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.uses < self.max_uses and timezone.now() < self.expires_at

    def link(self, request=None):
        path = reverse("invite", args=[self.token])
        if not request:
            return path
        return request.build_absolute_uri(path)

    def __str__(self):
        return f"Invite {self.token[:8]}.. (valid={self.is_valid()})"

class Product(models.Model):
    DRAFT, ACTIVE, ARCHIVED = "draft", "active", "archived"
    STATUS_CHOICES = [(DRAFT, "Draft"), (ACTIVE, "Active"), (ARCHIVED, "Archived")]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def main_image(self):
        return self.images.order_by("sort_order").first()

    def hearts_count(self):
        return self.hearts.count()

    def __str__(self):
        return self.title

# store/models.py

class ProductImage(models.Model):
    product = models.ForeignKey('Product', related_name='images', on_delete=models.CASCADE)
    url = models.URLField()
    alt = models.CharField(max_length=200, blank=True)
    sort_order = models.IntegerField(default=0)
    # NEW:
    color = models.CharField(
        max_length=40, blank=True,
        help_text="Optional: tie this image to a color (e.g. 'Black'). Leave blank for generic images."
    )

# store/models.py

class Variant(models.Model):
    product = models.ForeignKey('Product', related_name='variants', on_delete=models.CASCADE)
    price_gross_cents = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    attrs = models.JSONField(default=dict, blank=True)  # {"color":"Black","size":"EU 43"}

    def __str__(self):
        s = (self.attrs or {}).get("size")
        c = (self.attrs or {}).get("color")
        label = " · ".join([x for x in (s, c) if x]) or "One"
        return f"{self.product.title} [{label}]"

    # (optional helpers)
    @property
    def size(self):
        return (self.attrs or {}).get("size")

    @property
    def color(self):
        return (self.attrs or {}).get("color")


class Heart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="hearts", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "variant")

class Order(models.Model):
    NEW, PAID, FAILED = "new", "paid", "failed"
    STATUS_CHOICES = [(NEW, "New"), (PAID, "Paid"), (FAILED, "Failed")]

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=NEW)

    # VAT / totals (in cents)
    vat_rate = models.FloatField(default=settings.GERMANY_STANDARD_VAT)
    net_total = models.PositiveIntegerField(default=0)
    vat_total = models.PositiveIntegerField(default=0)
    gross_total = models.PositiveIntegerField(default=0)

    # shipping placeholder (later)
    shipping_method = models.CharField(max_length=50, default="pickup-or-shipping-later")
    shipping_fee_cents = models.PositiveIntegerField(default=0)

    # address (minimal; expand later)
    full_name = models.CharField(max_length=120)
    address_line = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default=settings.HOME_COUNTRY)

    def __str__(self):
        return f"Order #{self.pk} {self.user} {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_title = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    attrs = models.JSONField(default=dict, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    price_gross_cents = models.PositiveIntegerField()
    price_net_cents = models.PositiveIntegerField()
    vat_amount_cents = models.PositiveIntegerField()

class Payment(models.Model):
    STRIPE, PAYPAL, COINBASE = "stripe", "paypal", "coinbase"
    PROVIDERS = [(STRIPE, "Stripe"), (PAYPAL, "PayPal"), (COINBASE, "Coinbase")]

    order = models.OneToOneField(Order, related_name="payment", on_delete=models.CASCADE)
    provider = models.CharField(max_length=10, choices=PROVIDERS)
    status = models.CharField(max_length=20, default="created")
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EUR")
    external_id = models.CharField(max_length=200, blank=True)  # checkout session id / paypal order id / coinbase charge id
    receipt_url = models.URLField(blank=True)
    raw = models.JSONField(default=dict, blank=True)

    def valid(self):
        now = timezone.now()
        return self.filter(active=True).filter(
            models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now),
            models.Q(valid_to__isnull=True)   | models.Q(valid_to__gte=now),
        )

class CouponQuerySet(models.QuerySet):
    def valid(self):
        now = timezone.now()
        return self.filter(active=True).filter(
            models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now),
            models.Q(valid_to__isnull=True)   | models.Q(valid_to__gte=now),
        )

class Coupon(models.Model):
    code = models.CharField(max_length=32, unique=True)
    percent_off = models.PositiveIntegerField(null=True, blank=True)     # e.g. 10 for 10%
    amount_off_cents = models.PositiveIntegerField(null=True, blank=True) # e.g. 500 = €5.00
    min_subtotal_cents = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to   = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)


    objects = CouponQuerySet.as_manager()

    def __str__(self):
        return self.code

    def clean(self):
        # Ensure only one discount type is set
        from django.core.exceptions import ValidationError
        if self.percent_off and self.amount_off_cents:
            raise ValidationError("Set either percent_off OR amount_off_cents, not both.")

    def discount_amount(self, subtotal_cents: int) -> int:
        if subtotal_cents < self.min_subtotal_cents:
            return 0
        if self.amount_off_cents:
            return min(self.amount_off_cents, subtotal_cents)
        if self.percent_off:
            return int(subtotal_cents * (self.percent_off / 100.0))
        return 0