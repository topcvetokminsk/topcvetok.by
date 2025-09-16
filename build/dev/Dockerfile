FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONWARNINGS="ignore:Unverified HTTPS request"

COPY ./app /app
WORKDIR /app

RUN apk add python3-dev musl-dev zlib-dev libc-dev gcc py3-wheel librdkafka-dev
RUN pip install --upgrade pipenv
RUN pipenv install --system --ignore-pipfile --dev

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]