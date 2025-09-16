import os
import uuid

from django.db import models
from django.core.mail import EmailMessage


class LowercaseEmailField(models.EmailField):
    """
    Override EmailField to convert emails to lowercase before saving.
    """

    def to_python(self, value):
        """
        Convert email to lowercase.
        """
        value = super().to_python(value)
        # Value can be None so check that it's a string before lowercasing.
        if isinstance(value, str):
            return value.lower()

        return value


def generate_uuid() -> str:
    return uuid.uuid4().hex


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            data['email_subject'],
            data['email_body'],
            os.environ.get("SMTP_FROM_EMAIL", "test@gmail.com"),
            [data['to_email']],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=True)
