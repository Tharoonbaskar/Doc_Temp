from rest_framework.response import Response


def success_response(data, status_code=200):
    return Response({"success": True, "data": data}, status=status_code)


def error_response(message, status_code=400, errors=None):
    payload = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)
