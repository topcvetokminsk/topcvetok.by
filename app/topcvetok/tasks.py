from datetime import datetime
from django.utils.timezone import make_aware

from project.celery import app


@app.task(ignore_results=True)
def clear_expired_tokens():
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

    now = make_aware(datetime.now())

    BlacklistedToken.objects.filter(token__expires_at__lt=now).delete()
    OutstandingToken.objects.filter(expires_at__lt=now).delete()
