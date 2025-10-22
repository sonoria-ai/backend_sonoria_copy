import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware to log incoming requests for debugging CORS and other issues."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        logger.info(f"Incoming {request.method} request to {request.path}")
        logger.info(f"Origin: {request.headers.get('Origin', 'Not set')}")
        logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
        logger.info(f"Authorization: {'Present' if request.headers.get('Authorization') else 'Not present'}")

        response = self.get_response(request)

        # Log response details
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        return response
