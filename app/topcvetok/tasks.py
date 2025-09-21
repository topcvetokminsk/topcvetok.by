import os
import logging

from datetime import datetime
from django.utils.timezone import make_aware

from project.celery import app
from yandex_reviews_parser.utils import YandexParser

logger = logging.getLogger(__name__)


@app.task(ignore_results=True)
def clear_expired_tokens():
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

    now = make_aware(datetime.now())

    BlacklistedToken.objects.filter(token__expires_at__lt=now).delete()
    OutstandingToken.objects.filter(expires_at__lt=now).delete()


@app.task(ignore_results=False)
def download_company_review():
    from topcvetok.models import Review

    company_id = int(os.environ.get("COMPANY_ID"))
    company_name = os.environ.get("COMPANY_NAME")
    domain_name = os.environ.get("DOMAIN_NAME")
    chrome_version = int(os.environ.get("CHROME_VERSION", "108"))

    def save_review_callback(review_data):
        """Callback функция для сохранения каждого отзыва"""
        try:
            print(f"Обрабатываем отзыв: {review_data['name']}")
            
            # Проверяем обязательные поля
            if not review_data.get('name') or not review_data.get('text') or not review_data.get('date'):
                print(f"Пропускаем отзыв из-за отсутствия обязательных полей: {review_data}")
                return False
            
            review_date = datetime.fromtimestamp(review_data['date'])
            aware_date = make_aware(review_date)
            
            print(f"Создаем/обновляем отзыв для: {review_data['name']}, дата: {aware_date}")

            obj, created = Review.objects.update_or_create(
                company=review_data['name'],
                date=aware_date,
                text=review_data['text'],
                defaults={
                    'stars': review_data['stars'],
                    'answer': review_data.get('answer'),
                    'icon_url': review_data.get('icon_href'),
                }
            )
            
            if created:
                print(f"Создан новый отзыв: {obj}")
            else:
                print(f"Обновлен существующий отзыв: {obj}")
            
            return True
        except Exception as e:
            print(f"Ошибка при сохранении отзыва: {e}")
            return False

    parser = YandexParser(company_id=company_id, domain_name=domain_name, company_name=company_name)
    data = parser.parse(type_parse='reviews_incremental', chrome_version=chrome_version, callback=save_review_callback)

    if 'error' in data:
        print(f"Ошибка парсинга: {data['error']}")
        return {'error': data['error']}
    
    processed_count = data.get('processed_count', 0)
    print(f"Обработано отзывов: {processed_count}")
    return {'processed_count': processed_count, 'success': True}

