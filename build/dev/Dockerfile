FROM ultrafunk/undetected-chromedriver

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONWARNINGS="ignore:Unverified HTTPS request"

# Оптимизации для малого сервера
ENV PYTHONHASHSEED=random
ENV PYTHONIOENCODING=utf-8

COPY ./app /app
WORKDIR /app

# Установка только необходимых пакетов
RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    libc6-dev \
    zlib1g-dev \
    python3-wheel \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Установка зависимостей
RUN pip install --upgrade pipenv
RUN pipenv install --system --ignore-pipfile --dev

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
