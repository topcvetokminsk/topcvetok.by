from rest_framework import pagination


class LimitPagination(pagination.LimitOffsetPagination):
    default_limit = 20  # Увеличено с 10 до 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100  # Максимальный лимит для защиты от больших запросов


class LimitPagination1C(pagination.LimitOffsetPagination):
    default_limit = 20  # Увеличено с 10 до 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
