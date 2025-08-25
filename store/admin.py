# store/admin.py
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.utils.html import format_html

from .models import (
    Product, ProductImage, Variant,
    Heart, Cart, CartItem, Order, OrderItem, Payment,
    QRInvite, Coupon,
)

# If Product was registered elsewhere, unregister first to avoid AlreadyRegistered
try:
    admin.site.unregister(Product)
except NotRegistered:
    pass


# -------- Inlines --------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("url", "alt", "sort_order", "color")   # includes color
    ordering = ("sort_order", "id")


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ("price_gross_cents", "stock", "attrs")
    ordering = ("id",)


# -------- Product --------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline, VariantInline]


# -------- Coupons --------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code", "percent_off", "amount_off_cents",
        "active", "min_subtotal_cents", "valid_from", "valid_to",
    )
    list_filter = ("active",)
    search_fields = ("code",)


# -------- QR Invites --------
@admin.register(QRInvite)
class QRInviteAdmin(admin.ModelAdmin):
    list_display = ("token", "expires_at", "uses", "max_uses", "used_by", "invite_link")
    readonly_fields = ("token", "uses", "used_by", "used_at")

    def invite_link(self, obj):
        return format_html("<code>/invite/{}</code>", obj.token)


# -------- Misc models --------
admin.site.register(Heart)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
