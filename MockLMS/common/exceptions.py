import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        logger.warning(
            "API exception on %s: %s",
            context.get("view", context.get("request")),
            exc,
        )
    return response
