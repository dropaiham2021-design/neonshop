# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # core pages
    path("", views.home, name="home"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),

    # invites / auth
    path("invite/<str:token>/", views.invite, name="invite"),
    path("auth/signup/", views.signup_view, name="signup"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/verify/<str:token>/", views.verify_email, name="verify_email"),

    # cart
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:variant_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),

    # checkout / payments (keep what you use)
    path("checkout/", views.checkout_view, name="checkout"),
    path("pay/stripe/create/", views.stripe_create_checkout, name="stripe_create_checkout"),
    path("pay/stripe/success/", views.stripe_success, name="stripe_success"),
    path("pay/stripe/cancel/", views.stripe_cancel, name="stripe_cancel"),
    path("pay/paypal/create/", views.paypal_create_order, name="paypal_create_order"),
    path("pay/paypal/capture/<str:order_id>/", views.paypal_capture_order, name="paypal_capture_order"),
    path("pay/coinbase/create/", views.coinbase_create_charge, name="coinbase_create_charge"),
    path("orders/success/<int:order_id>/", views.order_success, name="order_success"),
]
