from django.db import models


class DeliveryType(models.TextChoices):
    """Типы доставки"""
    MINSK = 'minsk', 'Доставка по Минску'
    BELARUS = 'belarus', 'Доставка по Беларуси'
    PICKUP = 'pickup', 'Самовывоз'

class AttributeFilterType(models.TextChoices):
    """Типы фильтров атрибутов"""
    CHECKBOX = 'checkbox', 'Чекбокс'
    RADIO = 'radio', 'Радио кнопка'
    SELECT = 'select', 'Выпадающий список'
    RANGE = 'range', 'Диапазон значений'
    COLOR = 'color', 'Цветовая палитра'


class ReviewRating(models.IntegerChoices):
    """Рейтинги отзывов"""
    ONE = 1, '1 звезда'
    TWO = 2, '2 звезды'
    THREE = 3, '3 звезды'
    FOUR = 4, '4 звезды'
    FIVE = 5, '5 звезд'
