from rest_framework import pagination
from rest_framework.exceptions import NotFound

from joompa.settings import db_config


class CustomPagination(pagination.PageNumberPagination):
    page_size = db_config.get("PAGE_SIZE", 25)
    page_size_query_param = db_config.get("PAGE_SIZE_QUERY_PARAM", "page_size")

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except Exception as e:
            message = "Page out of range"
            raise NotFound(f"{message} : {e}")

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        response = {
            "data": data,
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        }
        return response
