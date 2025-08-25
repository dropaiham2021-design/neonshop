from django.core import signing, mail
from django.conf import settings
from django.urls import reverse

def make_activation_token(user_id: int) -> str:
    return signing.dumps({"uid": user_id}, salt="email-verify")

def parse_activation_token(token: str) -> int | None:
    try:
        data = signing.loads(token, salt="email-verify", max_age=60*60*24)
        return int(data["uid"])
    except Exception:
        return None

def send_activation_email(request, user):
    token = make_activation_token(user.id)
    url = request.build_absolute_uri(reverse("verify_email", args=[token]))
    body = f"Welcome to the private shop!\nVerify your email:\n{url}"
    mail.send_mail("Verify your email", body, settings.DEFAULT_FROM_EMAIL, [user.email])
