from __future__ import annotations

from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from .responses import paginated_response


class EnterprisePageNumberPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"
    page_size = getattr(settings, "REST_PAGE_SIZE", 20)
    max_page_size = getattr(settings, "REST_MAX_PAGE_SIZE", 100)

    def get_paginated_response(self, data):
        return paginated_response(
            data=data,
            count=self.page.paginator.count,
            next_link=self.get_next_link(),
            previous_link=self.get_previous_link(),
            page=self.page.number,
            page_size=self.get_page_size(self.request) or self.page_size,
        )