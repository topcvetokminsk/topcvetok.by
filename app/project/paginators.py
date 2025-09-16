from rest_framework import pagination


class LimitPagination(pagination.LimitOffsetPagination):
    count = 10
    offset = 0


class LimitPagination1C(pagination.LimitOffsetPagination):
    count = 10
    offset = 0
    default_limit  = 10
