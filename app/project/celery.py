import os

from celery import Celery

from project import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)

app.conf.beat_schedule = {
    "clear-expired-tokens": {
        "task": "topcvetok.tasks.clear_expired_tokens",
        "schedule": 60,
    },
    "download-company-review": {
        "task": "topcvetok.tasks.download_company_review",
        "schedule": 60 * 60,
    },
}
