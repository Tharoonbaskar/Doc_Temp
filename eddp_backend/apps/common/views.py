from __future__ import annotations

import inspect
from typing import Any, Callable

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .exceptions import BaseApplicationException
from .permissions import IsAuthenticatedUser
from .responses import error_response, success_response


class HealthCheckAPIView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request, *args, **kwargs) -> Response:
		return success_response(
			data={"status": "ok"},
			message="Service is healthy.",
			status_code=status.HTTP_200_OK,
		)


class EnterpriseServiceViewSet(viewsets.ViewSet):
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticatedUser]
	service_class = None
	serializer_class = None

	@staticmethod
	def _normalized_query_params(query_params) -> dict[str, Any]:
		normalized: dict[str, Any] = {}
		for key in query_params.keys():
			values = query_params.getlist(key)
			if not values:
				normalized[key] = ""
			elif len(values) == 1:
				normalized[key] = values[0]
			else:
				normalized[key] = values
		return normalized

	def get_service(self):
		if self.service_class is None:
			raise NotImplementedError("service_class must be defined.")
		return self.service_class()

	def get_serializer_class(self):
		if self.serializer_class is None:
			raise NotImplementedError("serializer_class must be defined.")
		return self.serializer_class

	def get_serializer_context(self) -> dict[str, Any]:
		return {"request": self.request, "view": self}

	def get_serializer(self, *args, **kwargs):
		kwargs.setdefault("context", self.get_serializer_context())
		serializer_class = self.get_serializer_class()
		return serializer_class(*args, **kwargs)

	def _application_error_response(self, exc: BaseApplicationException) -> Response:
		detail = exc.detail
		message = detail if isinstance(detail, str) else "Request failed."
		errors = exc.errors if getattr(exc, "errors", None) else detail
		return error_response(
			message=message,
			errors=errors,
			status_code=exc.status_code,
			error_code=getattr(exc, "default_code", "application_error"),
		)

	@staticmethod
	def _validation_error_response(exc: ValidationError) -> Response:
		return error_response(
			message="Validation failed.",
			errors=exc.detail,
			status_code=status.HTTP_400_BAD_REQUEST,
			error_code="validation_error",
		)

	@staticmethod
	def _unexpected_error_response() -> Response:
		return error_response(
			message="An unexpected error occurred.",
			errors=[],
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			error_code="internal_server_error",
		)

	def _run_service_call(self, handler: Callable[[], Any]) -> Response:
		try:
			result = handler()
			if isinstance(result, Response):
				return result
			return success_response(data=result)
		except ValidationError as exc:
			return self._validation_error_response(exc)
		except BaseApplicationException as exc:
			return self._application_error_response(exc)
		except Exception:
			return self._unexpected_error_response()

	def _validated_payload(self, *, partial: bool = False) -> dict[str, Any]:
		serializer = self.get_serializer(data=self.request.data, partial=partial)
		serializer.is_valid(raise_exception=True)
		return dict(serializer.validated_data)

	def _validated_payload_for_instance(self, instance: Any, *, partial: bool = False) -> dict[str, Any]:
		serializer = self.get_serializer(instance=instance, data=self.request.data, partial=partial)
		serializer.is_valid(raise_exception=True)
		return dict(serializer.validated_data)

	def list(self, request) -> Response:
		def handler() -> Any:
			service = self.get_service()
			parameters = inspect.signature(service.get_all).parameters
			if "query_params" in parameters:
				return service.get_all(query_params=self._normalized_query_params(request.query_params))
			return service.get_all()

		return self._run_service_call(handler)

	def retrieve(self, request, pk=None) -> Response:
		return self._run_service_call(lambda: self.get_service().get_by_id(pk))

	def create(self, request) -> Response:
		def handler() -> Any:
			payload = self._validated_payload()
			return self.get_service().create(payload)

		return self._run_service_call(handler)

	def update(self, request, pk=None) -> Response:
		def handler() -> Any:
			# Resolve model instance through serializer metadata for accurate unique checks.
			model_cls = self.get_serializer_class().Meta.model
			model_instance = model_cls.all_objects.filter(pk=pk).first()
			if model_instance is None:
				payload = self._validated_payload()
				return self.get_service().update(pk, payload)

			payload = self._validated_payload_for_instance(model_instance)
			return self.get_service().update(pk, payload)

		return self._run_service_call(handler)

	def partial_update(self, request, pk=None) -> Response:
		def handler() -> Any:
			model_cls = self.get_serializer_class().Meta.model
			model_instance = model_cls.all_objects.filter(pk=pk).first()
			if model_instance is None:
				payload = self._validated_payload(partial=True)
				return self.get_service().update(pk, payload)

			payload = self._validated_payload_for_instance(model_instance, partial=True)
			return self.get_service().update(pk, payload)

		return self._run_service_call(handler)

	def destroy(self, request, pk=None) -> Response:
		return self._run_service_call(lambda: self.get_service().delete(pk))

	@action(detail=True, methods=["post"])
	def restore(self, request, pk=None) -> Response:
		return self._run_service_call(lambda: self.get_service().restore(pk))

	@action(detail=False, methods=["get"], url_path="exists")
	def exists(self, request) -> Response:
		code = (request.query_params.get("code") or "").strip()
		return self._run_service_call(lambda: self.get_service().exists(code))
