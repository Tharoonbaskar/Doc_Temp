from __future__ import annotations

import hashlib
import json
from typing import Any

from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response

from apps.common.exceptions import (
    BaseApplicationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response

from .repositories import TemplateRepository, TemplateVersionRepository


class TemplateService:
    """Service layer for Template aggregate operations."""

    _VALID_PAGE_SIZES = {"A4", "A3", "LETTER", "LEGAL"}
    _VALID_PAGE_ORIENTATIONS = {"PORTRAIT", "LANDSCAPE"}

    def __init__(self, repository: TemplateRepository | None = None) -> None:
        self.repository = repository or TemplateRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data.pop("content_json", None)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        if getattr(instance, "document_id", None):
            data["document_id"] = str(instance.document_id)
            document = getattr(instance, "document", None)
            if document is not None:
                data["document"] = {
                    "id": str(document.id),
                    "code": document.code,
                    "name": document.name,
                }
        else:
            data["document_id"] = ""
            data["document"] = None
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        data["current_version"] = instance.current_version
        data["version_count"] = instance.version_count
        data["pending_draft_version"] = instance.pending_draft_version
        data["has_pending_draft"] = instance.has_pending_draft
        data["pending_draft_status"] = instance.pending_draft_status
        return data

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
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
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    @staticmethod
    def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data)
        if "name" in payload and isinstance(payload.get("name"), str):
            payload["name"] = payload["name"].strip()
        if "code" in payload and isinstance(payload.get("code"), str):
            payload["code"] = payload["code"].strip().upper()
        if "category" in payload and isinstance(payload.get("category"), str):
            payload["category"] = payload["category"].strip().upper()
        if "content_type" in payload and isinstance(payload.get("content_type"), str):
            payload["content_type"] = payload["content_type"].strip()

        if "content_json" in payload:
            raise ValidationException(detail="Field 'content_json' is no longer supported. Use 'prosemirror_json'.")

        if "prosemirror_json" in payload:
            extracted = TemplateService._extract_prosemirror_and_page(payload.get("prosemirror_json"))
            payload["prosemirror_json"] = extracted["prosemirror_json"]

            if "page_size" not in payload and extracted.get("page_size_provided"):
                payload["page_size"] = extracted["page_size"]
            if "page_orientation" not in payload and extracted.get("page_orientation_provided"):
                payload["page_orientation"] = extracted["page_orientation"]

        if "page_size" in payload:
            normalized_page_size = str(payload.get("page_size") or "A4").upper()
            if normalized_page_size not in TemplateService._VALID_PAGE_SIZES:
                normalized_page_size = "A4"
            payload["page_size"] = normalized_page_size

        if "page_orientation" in payload:
            normalized_page_orientation = str(payload.get("page_orientation") or "PORTRAIT").upper()
            if normalized_page_orientation not in TemplateService._VALID_PAGE_ORIENTATIONS:
                normalized_page_orientation = "PORTRAIT"
            payload["page_orientation"] = normalized_page_orientation

        payload.pop("content_json", None)
        return payload

    @staticmethod
    def _empty_prosemirror_doc() -> dict[str, Any]:
        return {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                }
            ],
        }

    @classmethod
    def _canonicalize_prosemirror_doc(cls, candidate: Any) -> dict[str, Any]:
        if not isinstance(candidate, dict):
            return cls._empty_prosemirror_doc()

        if candidate.get("type") != "doc":
            return cls._empty_prosemirror_doc()

        content = candidate.get("content")
        if not isinstance(content, list):
            return cls._empty_prosemirror_doc()

        valid_nodes = [node for node in content if isinstance(node, dict) and isinstance(node.get("type"), str)]
        if not valid_nodes:
            return cls._empty_prosemirror_doc()

        normalized = dict(candidate)
        normalized["content"] = valid_nodes
        return normalized

    @classmethod
    def _extract_prosemirror_and_page(cls, content: Any) -> dict[str, Any]:
        """Extract ProseMirror JSON and page settings from content payload."""
        parsed: Any = content
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except (json.JSONDecodeError, TypeError):
                parsed = {}

        result = {
            "prosemirror_json": cls._empty_prosemirror_doc(),
            "page_size": "A4",
            "page_orientation": "PORTRAIT",
            "page_size_provided": False,
            "page_orientation_provided": False,
        }

        if isinstance(parsed, dict) and parsed.get('type') == 'doc':
            result["prosemirror_json"] = cls._canonicalize_prosemirror_doc(parsed)
        elif isinstance(parsed, dict):
            candidate = parsed.get('prosemirror_json')
            if isinstance(candidate, dict) and candidate.get('type') == 'doc':
                result["prosemirror_json"] = cls._canonicalize_prosemirror_doc(candidate)

            page = parsed.get('page', {})
            if isinstance(page, dict):
                if page.get('size'):
                    result["page_size"] = str(page['size']).upper()
                    result["page_size_provided"] = True
                if page.get('orientation'):
                    result["page_orientation"] = str(page['orientation']).upper()
                    result["page_orientation_provided"] = True

            page_size = parsed.get('page_size')
            if isinstance(page_size, str) and page_size.strip():
                result["page_size"] = page_size.strip().upper()
                result["page_size_provided"] = True

            page_orientation = parsed.get('page_orientation')
            if isinstance(page_orientation, str) and page_orientation.strip():
                result["page_orientation"] = page_orientation.strip().upper()
                result["page_orientation_provided"] = True

        if result["page_size"] not in cls._VALID_PAGE_SIZES:
            result["page_size"] = "A4"
        if result["page_orientation"] not in cls._VALID_PAGE_ORIENTATIONS:
            result["page_orientation"] = "PORTRAIT"

        return result

    def _restore_soft_deleted_duplicate(self, payload: dict[str, Any]) -> Any | None:
        code = payload.get("code")
        name = payload.get("name")
        document = payload.get("document")

        candidate = None
        if code:
            candidate = self.repository.get_deleted_by_code(code)

        if candidate is None and document is not None and name:
            candidate = self.repository.get_deleted_by_document_and_name(document, name)

        if candidate is None:
            return None

        update_payload = dict(payload)
        update_payload["is_deleted"] = False
        update_payload["deleted_at"] = None
        return self.repository.update(candidate, update_payload)

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    @staticmethod
    def _has_approved_baseline(template: Any, *, exclude_version_id: Any | None = None) -> bool:
        from apps.common.choices import VersionStatusChoices

        queryset = template.versions.filter(version_status=VersionStatusChoices.APPROVED)
        if exclude_version_id:
            queryset = queryset.exclude(id=exclude_version_id)
        return queryset.exists()

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all(query_params=query_params)]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            payload = self._normalize_payload(data)

            if "prosemirror_json" not in payload:
                payload["prosemirror_json"] = self._empty_prosemirror_doc()

            code = payload.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")

            restored = self._restore_soft_deleted_duplicate(payload)
            if restored is not None:
                return success_response(
                    data=self._serialize(restored),
                    message="Record restored successfully.",
                    status_code=status.HTTP_201_CREATED,
                )

            instance = self.repository.create(payload)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            from apps.common.choices import VersionStatusChoices
            
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            payload = self._normalize_payload(data)
            
            # Get the user from updated_by field (set by ViewSet)
            user = payload.get('updated_by')

            has_approved_baseline = self._has_approved_baseline(instance)
            has_content_update = 'prosemirror_json' in payload and payload['prosemirror_json'] != instance.prosemirror_json
            
            # For any template with an approved baseline, content edits must go through
            # versioned draft rows (never mutate approved baseline content directly).
            if has_approved_baseline and has_content_update:
                existing_in_progress = instance.versions.filter(
                    version_status__in=[VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
                ).order_by('-version_number').first()

                if existing_in_progress:
                    raise ValidationException(
                        detail=(
                            f"An in-progress version v{existing_in_progress.version_number}.0 already exists. "
                            "Please continue editing that version instead of creating a new one."
                        )
                    )
                
                # Create a draft version instead of updating directly
                if not user:
                    raise ValidationException(detail="User information is required for version creation.")
                    
                return self.create_draft_version_from_approved(
                    id=id, 
                    user=user, 
                    new_prosemirror_json=payload.get('prosemirror_json')
                )

            # Protect approved baseline status from accidental manual downgrades
            # through generic template edit forms.
            if has_approved_baseline and 'status' in payload:
                payload.pop('status', None)
            
            # Normal update for non-approved templates or non-content changes
            new_code = payload.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, payload)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)
        except Exception as e:
            # Log the actual error for debugging
            import traceback
            traceback.print_exc()
            raise ValidationException(detail=f"Update failed: {str(e)}")

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)
    
    def send_for_review(self, id: Any, user: Any):
        """Send template for review by changing status to FOR_REVIEW."""
        from apps.common.choices import TemplateStatusChoices
        
        instance = self._get_instance_or_raise(id)
        
        if instance.status != TemplateStatusChoices.DRAFT:
            raise ValidationException(detail="Only templates in DRAFT status can be sent for review.")
        
        instance.status = TemplateStatusChoices.FOR_REVIEW
        instance.updated_by = user
        instance.save()
        
        return instance
    
    def approve_template(self, id: Any, user: Any, effective_date: Any, review_comments: str = ""):
        """Approve template and set effective date. Creates version 1.0 on first approval."""
        from django.utils import timezone
        from apps.common.choices import TemplateStatusChoices, LifecycleStatusChoices, VersionStatusChoices
        from .models import TemplateVersion
        
        instance = self._get_instance_or_raise(id)
        
        if instance.status != TemplateStatusChoices.FOR_REVIEW:
            raise ValidationException(detail="Only templates in FOR_REVIEW status can be approved.")
        
        # Update approval fields
        instance.status = TemplateStatusChoices.APPROVED
        instance.approved_by = user
        instance.approved_at = timezone.now()
        instance.effective_date = effective_date
        instance.review_comments = review_comments
        
        # Set lifecycle status based on effective date
        if effective_date <= timezone.now():
            instance.lifecycle_status = LifecycleStatusChoices.ACTIVE
        else:
            instance.lifecycle_status = LifecycleStatusChoices.INACTIVE

        canonical_doc = self._parse_content_payload(instance.prosemirror_json)
        instance.prosemirror_json = canonical_doc
        
        instance.updated_by = user
        instance.save()
        
        # Create version 1.0 on first approval
        if not instance.versions.exists():
            TemplateVersion.objects.create(
                template=instance,
                version_number=1,
                version_name="v1.0",
                version_status=VersionStatusChoices.APPROVED,
                template_json=canonical_doc,
                change_summary="Initial approved version",
                published_at=timezone.now(),
                approved_by=user,
                approved_at=timezone.now(),
                code=f"{instance.code}_V1",
                created_by=user,
                updated_by=user
            )
        
        return instance
    
    def send_back_for_revision(self, id: Any, user: Any, comments: str = ""):
        """Send template back to draft for revision."""
        from apps.common.choices import TemplateStatusChoices, VersionStatusChoices
        from .models import TemplateElementChange, TemplateVersion
        
        with transaction.atomic():
            instance = self._get_instance_or_raise(id)
            
            if instance.status != TemplateStatusChoices.FOR_REVIEW:
                raise ValidationException(detail="Only templates in FOR_REVIEW status can be sent back.")

            pending_versions = list(
                TemplateVersion.objects.select_for_update().filter(
                    template=instance,
                    version_status__in=[VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW],
                )
            )

            approved_baseline_exists = self._has_approved_baseline(instance)

            for pending_version in pending_versions:
                if pending_version.version_status != VersionStatusChoices.DRAFT:
                    pending_version.version_status = VersionStatusChoices.DRAFT
                    pending_version.updated_by = user
                    pending_version.save(update_fields=['version_status', 'updated_by', 'updated_at'])

                TemplateElementChange.objects.filter(version=pending_version).exclude(approval_status='PENDING').update(
                    approval_status='PENDING',
                    reviewed_by=None,
                    reviewed_at=None,
                    review_comment='',
                    updated_by=user,
                )

            instance.status = (
                TemplateStatusChoices.APPROVED
                if approved_baseline_exists
                else TemplateStatusChoices.DRAFT
            )
            instance.review_comments = comments
            instance.updated_by = user
            instance.save(update_fields=['status', 'review_comments', 'updated_by', 'updated_at'])
        
        return instance
    
    def create_draft_version_from_approved(self, id: Any, user: Any, new_prosemirror_json: Any) -> Response:
        """
        Create a new draft version when an approved template is edited.
        This method:
        1. Gets the latest approved version as the base
        2. Calculates diff between base and new content
        3. Creates a new TemplateVersion with status=DRAFT
        4. Creates TemplateElementChange records for granular approval
        """
        from django.utils import timezone
        from apps.common.choices import VersionStatusChoices
        from .models import TemplateVersion, TemplateElementChange
        from .diff_utils import TemplateElementDiffer
        import json
        
        try:
            instance = self._get_instance_or_raise(id)
            
            # Get the latest approved version as base
            base_version = instance.versions.filter(
                version_status=VersionStatusChoices.APPROVED
            ).order_by('-version_number').first()
            
            if not base_version:
                raise ValidationException(detail="No approved version found to use as base.")
            
            old_payload = self._parse_content_payload(base_version.template_json)
            new_payload = self._parse_content_payload(new_prosemirror_json)

            differ = TemplateElementDiffer()
            diff_data = differ.calculate_diff(old_payload, new_payload)
            
            # Check if there are any changes
            if diff_data['summary']['total_changes'] == 0:
                raise ValidationException(detail="No changes detected between base and new content.")
            
            # Create new draft version.
            # If a previously soft-deleted pending draft exists for the same version
            # number, remove it so unique constraints (code/version_number) do not block.
            next_version_number = base_version.version_number + 1
            while TemplateVersion.all_objects.filter(template=instance, version_number=next_version_number).exists():
                existing_same_number = TemplateVersion.all_objects.filter(
                    template=instance,
                    version_number=next_version_number,
                ).first()

                if (
                    existing_same_number
                    and existing_same_number.is_deleted
                    and existing_same_number.version_status in [VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
                ):
                    existing_same_number.delete()
                    break

                next_version_number += 1

            draft_version = TemplateVersion.objects.create(
                template=instance,
                version_number=next_version_number,
                version_name=f"v{next_version_number}.0",
                version_status=VersionStatusChoices.DRAFT,
                template_json=new_payload,
                change_summary=differ.generate_change_summary(diff_data),
                base_version=base_version,
                diff_data=diff_data,
                code=f"{instance.code}_V{next_version_number}",
                created_by=user,
                updated_by=user
            )
            
            # Create individual element change records for granular approval
            element_changes = differ.extract_element_changes(diff_data)
            change_records = []
            seen_change_keys: set[str] = set()
            
            for elem_id, change_type, old_value, new_value in element_changes:
                if not self._is_reviewable_element_change(change_type, old_value, new_value):
                    continue
                dedup_key = self._change_dedup_key(change_type, old_value, new_value)
                if dedup_key in seen_change_keys:
                    continue
                seen_change_keys.add(dedup_key)
                change_record = TemplateElementChange.objects.create(
                    version=draft_version,
                    element_id=elem_id,
                    change_type=change_type,
                    old_value=old_value,
                    new_value=new_value,
                    approval_status='PENDING',
                    code=self._build_element_change_code(draft_version.code, dedup_key),
                    created_by=user,
                    updated_by=user
                )
                change_records.append(change_record)
            
            return success_response(
                data={
                    'version': self._serialize_version(draft_version),
                    'changes': [self._serialize_element_change(c) for c in change_records]
                },
                message=f"Draft version v{next_version_number}.0 created with {len(change_records)} change(s).",
                status_code=status.HTTP_201_CREATED
            )
            
        except BaseApplicationException as exc:
            return self._error(exc)
    
    def _serialize_version(self, version: Any) -> dict[str, Any]:
        """Serialize a TemplateVersion instance."""
        return {
            'id': str(version.id),
            'template_id': str(version.template_id),
            'version_number': version.version_number,
            'version_name': version.version_name,
            'version_status': version.version_status,
            'template_json': version.template_json,
            'change_summary': version.change_summary,
            'base_version_id': str(version.base_version_id) if version.base_version_id else None,
            'created_at': version.created_at.isoformat() if version.created_at else None,
        }

    @classmethod
    def _parse_content_payload(cls, content: Any) -> dict[str, Any]:
        """Normalize template content payloads for ProseMirror-based diffing."""
        extracted = cls._extract_prosemirror_and_page(content)
        return extracted["prosemirror_json"]

    @staticmethod
    def _extract_semantic_payload(old_value: Any, new_value: Any) -> dict[str, Any]:
        if isinstance(new_value, dict) and isinstance(new_value.get('_semantic'), dict):
            return new_value.get('_semantic')
        if isinstance(old_value, dict) and isinstance(old_value.get('_semantic'), dict):
            return old_value.get('_semantic')
        return {}

    @staticmethod
    def _resolve_change_new_value(value: Any) -> Any:
        """Return the most concrete ProseMirror node payload from a change row."""
        if not isinstance(value, dict):
            return value

        semantic = value.get('_semantic') if isinstance(value.get('_semantic'), dict) else {}
        semantic_new = semantic.get('newValue') if isinstance(semantic, dict) else None
        if isinstance(semantic_new, dict) and isinstance(semantic_new.get('type'), str):
            return semantic_new

        raw = value.get('raw')
        if isinstance(raw, dict) and isinstance(raw.get('type'), str):
            return raw

        return value

    @staticmethod
    def _read_text(value: Any) -> str:
        def from_pm_node(node: Any) -> str:
            if not isinstance(node, dict):
                return ''

            parts = []
            text = node.get('text')
            if isinstance(text, str):
                parts.append(text)

            attrs = node.get('attrs') if isinstance(node.get('attrs'), dict) else {}
            for key in ('binding', 'variable', 'variableKey', 'field'):
                token = attrs.get(key)
                if isinstance(token, str) and token.strip():
                    parts.append(f"{{{{{token.strip()}}}}}")

            content = node.get('content')
            if isinstance(content, list):
                for child in content:
                    child_text = from_pm_node(child)
                    parts.append(child_text)

            return ''.join(parts)

        if isinstance(value, str):
            return value.replace('\r\n', '\n')
        if isinstance(value, dict):
            for key in ('oldText', 'newText', 'text', 'label', 'binding'):
                raw = value.get(key)
                if isinstance(raw, str):
                    return raw.replace('\r\n', '\n')
            pm_text = from_pm_node(value)
            if isinstance(pm_text, str):
                return pm_text.replace('\r\n', '\n')
        return ''

    @classmethod
    def _is_reviewable_element_change(cls, change_type: str, old_value: Any, new_value: Any) -> bool:
        semantic = cls._extract_semantic_payload(old_value, new_value)
        semantic_type = str(semantic.get('type') or '').upper()

        # Ignore unknown/noise rows from fallback matching.
        if semantic_type in {'', 'UNKNOWN_CHANGE'}:
            return False

        old_text = cls._read_text(old_value)
        new_text = cls._read_text(new_value)

        # Ignore no-op textual normalization diffs.
        if semantic_type.startswith('TEXT_') and old_text == new_text:
            return False

        if semantic_type in {'STYLE_CHANGED', 'FONT_CHANGED', 'FONT_SIZE_CHANGED', 'FONT_COLOR_CHANGED', 'ALIGNMENT_CHANGED', 'MARGIN_CHANGED', 'PADDING_CHANGED'}:
            if semantic.get('oldStyle') == semantic.get('newStyle'):
                return False

        # REMOVED: POSITION_CHANGED and IMAGE_MOVED checks (not applicable to ProseMirror)

        if change_type == 'MODIFIED' and old_value == new_value:
            return False

        return True

    @classmethod
    def _change_dedup_key(cls, change_type: str, old_value: Any, new_value: Any) -> str:
        semantic = cls._extract_semantic_payload(old_value, new_value)
        semantic_type = str(semantic.get('type') or '').upper()
        node_id = str(semantic.get('nodeId') or semantic.get('elementId') or '')
        page = str(semantic.get('page') or '')

        # Prefer node-level collapse for semantic editor changes.
        # This prevents fragment/token-level rows from inflating pending counts.
        if node_id:
            return f"{change_type}|{semantic_type}|{node_id}|{page}"

        old_text = cls._read_text(old_value).lower()
        new_text = cls._read_text(new_value).lower()
        return f"{change_type}|{semantic_type}|{node_id}|{page}|{old_text}|{new_text}"

    @staticmethod
    def _build_element_change_code(version_code: str, dedup_key: str) -> str:
        """Build a stable short code that always fits BaseModel.code max_length (100)."""
        digest = hashlib.sha1(dedup_key.encode('utf-8', errors='ignore')).hexdigest()[:24]
        prefix = f"{version_code}_CHG"
        max_prefix_len = max(1, 100 - (len(digest) + 1))
        return f"{prefix[:max_prefix_len]}_{digest}"

    def get_version_detail(self, template_id: Any, version_number: int) -> Response:
        """Get version details for editor/review workspace."""
        try:
            from .models import TemplateVersion

            instance = self._get_instance_or_raise(template_id)
            version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number
            ).first()

            if not version:
                raise ResourceNotFoundException(detail=f"Version {version_number} not found.")

            return success_response(
                data={
                    'template': self._serialize(instance),
                    'version': self._serialize_version(version),
                },
                message="Version detail fetched successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update_draft_version(self, template_id: Any, version_number: int, user: Any, new_prosemirror_json: Any) -> Response:
        """Update an existing draft version content and regenerate element-level diffs."""
        try:
            from apps.common.choices import VersionStatusChoices
            from .models import TemplateVersion, TemplateElementChange
            from .diff_utils import TemplateElementDiffer
            import json

            instance = self._get_instance_or_raise(template_id)
            draft_version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number,
                version_status=VersionStatusChoices.DRAFT
            ).select_related('base_version').first()

            if not draft_version:
                raise ValidationException(detail=f"Draft version v{version_number}.0 is not editable.")

            base_version = draft_version.base_version
            if not base_version:
                raise ValidationException(detail="Draft version has no base approved version.")

            old_payload = self._parse_content_payload(base_version.template_json)
            new_payload = self._parse_content_payload(new_prosemirror_json)
            differ = TemplateElementDiffer()
            diff_data = differ.calculate_diff(old_payload, new_payload)

            if diff_data.get('summary', {}).get('total_changes', 0) == 0:
                raise ValidationException(detail="No changes detected between base and new content.")

            draft_version.template_json = new_payload
            draft_version.diff_data = diff_data
            draft_version.change_summary = differ.generate_change_summary(diff_data)
            draft_version.updated_by = user
            draft_version.save()

            existing_state_by_key: dict[str, dict[str, Any]] = {}
            for row in draft_version.element_changes.all():
                key = self._change_dedup_key(row.change_type, row.old_value, row.new_value)
                existing_state_by_key[key] = {
                    'approval_status': row.approval_status,
                    'reviewed_by': row.reviewed_by,
                    'reviewed_at': row.reviewed_at,
                    'review_comment': row.review_comment,
                }

            draft_version.element_changes.all().delete()
            element_changes = differ.extract_element_changes(diff_data)

            created = []
            seen_change_keys: set[str] = set()
            for elem_id, change_type, old_value, new_value in element_changes:
                if not self._is_reviewable_element_change(change_type, old_value, new_value):
                    continue
                dedup_key = self._change_dedup_key(change_type, old_value, new_value)
                if dedup_key in seen_change_keys:
                    continue
                seen_change_keys.add(dedup_key)
                prior = existing_state_by_key.get(dedup_key)
                change_record = TemplateElementChange.objects.create(
                    version=draft_version,
                    element_id=elem_id,
                    change_type=change_type,
                    old_value=old_value,
                    new_value=new_value,
                    approval_status=(prior['approval_status'] if prior else 'PENDING'),
                    reviewed_by=(prior['reviewed_by'] if prior else None),
                    reviewed_at=(prior['reviewed_at'] if prior else None),
                    review_comment=(prior['review_comment'] if prior else ''),
                    code=self._build_element_change_code(draft_version.code, dedup_key),
                    created_by=user,
                    updated_by=user
                )
                created.append(change_record)

            return success_response(
                data={
                    'version': self._serialize_version(draft_version),
                    'changes': [self._serialize_element_change(c) for c in created],
                },
                message=f"Draft version v{version_number}.0 updated successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def send_draft_version_for_review(self, template_id: Any, version_number: int, user: Any) -> Response:
        """Move a draft version to FOR_REVIEW state for approver workflow."""
        try:
            from apps.common.choices import TemplateStatusChoices, VersionStatusChoices
            from .models import TemplateVersion

            instance = self._get_instance_or_raise(template_id)
            draft_version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number,
                version_status=VersionStatusChoices.DRAFT
            ).first()

            if not draft_version:
                raise ValidationException(detail=f"Draft version v{version_number}.0 not found.")

            if not draft_version.element_changes.exists():
                raise ValidationException(detail="No element changes found to send for review.")

            draft_version.version_status = VersionStatusChoices.FOR_REVIEW
            draft_version.updated_by = user
            draft_version.save(update_fields=['version_status', 'updated_by', 'updated_at'])

            approved_baseline_exists = self._has_approved_baseline(instance, exclude_version_id=draft_version.id)
            desired_template_status = (
                TemplateStatusChoices.APPROVED
                if approved_baseline_exists
                else TemplateStatusChoices.FOR_REVIEW
            )

            if instance.status != desired_template_status:
                instance.status = desired_template_status
                instance.updated_by = user
                instance.save(update_fields=['status', 'updated_by', 'updated_at'])

            return success_response(
                data={'version': self._serialize_version(draft_version)},
                message=f"Version v{version_number}.0 sent for review successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)
    
    def _serialize_element_change(self, change: Any) -> dict[str, Any]:
        """Serialize a TemplateElementChange instance."""
        semantic = {}
        if isinstance(change.new_value, dict) and isinstance(change.new_value.get('_semantic'), dict):
            semantic = change.new_value.get('_semantic')
        elif isinstance(change.old_value, dict) and isinstance(change.old_value.get('_semantic'), dict):
            semantic = change.old_value.get('_semantic')

        old_text = self._read_text(change.old_value)
        new_text = self._read_text(change.new_value)
        old_context_text = old_text
        new_context_text = new_text
        diff_granularity = None
        table_index = None
        row_index = None
        column_index = None
        inline_segments = None
        old_path = None
        new_path = None
        if isinstance(semantic, dict):
            if isinstance(semantic.get('oldText'), str):
                old_text = semantic.get('oldText') or ''
            if isinstance(semantic.get('newText'), str):
                new_text = semantic.get('newText') or ''
            if isinstance(semantic.get('oldContextText'), str):
                old_context_text = semantic.get('oldContextText') or old_context_text
            if isinstance(semantic.get('newContextText'), str):
                new_context_text = semantic.get('newContextText') or new_context_text

            diff_granularity = semantic.get('diffGranularity')
            table_index = semantic.get('tableIndex')
            row_index = semantic.get('rowIndex')
            column_index = semantic.get('columnIndex')
            if isinstance(semantic.get('inlineSegments'), list):
                inline_segments = semantic.get('inlineSegments')
            old_path = semantic.get('oldPath')
            new_path = semantic.get('newPath')

        return {
            'id': str(change.id),
            'element_id': change.element_id,
            'change_type': change.change_type,
            'semantic_type': semantic.get('type') if semantic else None,
            'node_id': semantic.get('nodeId') if semantic else change.element_id,
            'page': semantic.get('page') if semantic else 1,
            'old_text': old_text,
            'new_text': new_text,
            'old_context_text': old_context_text,
            'new_context_text': new_context_text,
            'diff_granularity': diff_granularity,
            'inline_segments': inline_segments,
            'old_path': old_path,
            'new_path': new_path,
            'table_index': table_index,
            'row_index': row_index,
            'column_index': column_index,
            # REMOVED: old_position and new_position (not applicable to ProseMirror)
            'old_style': semantic.get('oldStyle') if semantic else None,
            'new_style': semantic.get('newStyle') if semantic else None,
            'approval_status': change.approval_status,
            'old_value': change.old_value,
            'new_value': change.new_value,
            'reviewed_by': str(change.reviewed_by_id) if change.reviewed_by_id else None,
            'reviewed_by_name': change.reviewed_by.username if change.reviewed_by else None,
            'reviewed_at': change.reviewed_at.isoformat() if change.reviewed_at else None,
            'review_comment': change.review_comment,
            'created_at': change.created_at.isoformat() if change.created_at else None,
            'updated_at': change.updated_at.isoformat() if change.updated_at else None,
        }
    
    def get_version_changes(self, template_id: Any, version_number: int) -> Response:
        """Get a draft version with all its element changes."""
        try:
            from apps.common.choices import VersionStatusChoices
            from .models import TemplateVersion, TemplateElementChange
            from .diff_utils import TemplateElementDiffer
            
            instance = self._get_instance_or_raise(template_id)
            
            version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number
            ).select_related('base_version').prefetch_related('element_changes').first()
            
            if not version:
                raise ResourceNotFoundException(detail=f"Version {version_number} not found.")

            # Auto-heal and reconcile stale diff/change records for draft or in-review versions.
            base_version = version.base_version
            if (
                not base_version
                and version.version_status in [VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
            ):
                base_version = TemplateVersion.objects.filter(
                    template=instance,
                    version_status=VersionStatusChoices.APPROVED,
                    version_number__lt=version.version_number,
                ).order_by('-version_number').first()
                if base_version:
                    version.base_version = base_version
                    version.save(update_fields=['base_version', 'updated_at'])

            if (
                base_version
                and version.version_status in [VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW]
            ):
                existing_changes_qs = version.element_changes.all()
                differ = TemplateElementDiffer()
                old_payload = self._parse_content_payload(base_version.template_json)
                new_payload = self._parse_content_payload(version.template_json)
                recalculated_diff = differ.calculate_diff(old_payload, new_payload)

                existing_state_by_key: dict[str, dict[str, Any]] = {}
                for row in existing_changes_qs:
                    key = self._change_dedup_key(row.change_type, row.old_value, row.new_value)
                    existing_state_by_key[key] = {
                        "approval_status": row.approval_status,
                        "reviewed_by": row.reviewed_by,
                        "reviewed_at": row.reviewed_at,
                        "review_comment": row.review_comment,
                    }

                version.diff_data = recalculated_diff
                version.change_summary = differ.generate_change_summary(recalculated_diff)
                version.save(update_fields=['diff_data', 'change_summary', 'updated_at'])

                existing_changes_qs.delete()
                seen_change_keys: set[str] = set()
                for elem_id, change_type, old_value, new_value in differ.extract_element_changes(recalculated_diff):
                    if not self._is_reviewable_element_change(change_type, old_value, new_value):
                        continue
                    dedup_key = self._change_dedup_key(change_type, old_value, new_value)
                    if dedup_key in seen_change_keys:
                        continue
                    seen_change_keys.add(dedup_key)
                    prior = existing_state_by_key.get(dedup_key)
                    TemplateElementChange.objects.create(
                        version=version,
                        element_id=elem_id,
                        change_type=change_type,
                        old_value=old_value,
                        new_value=new_value,
                        approval_status=(prior["approval_status"] if prior else 'PENDING'),
                        reviewed_by=(prior["reviewed_by"] if prior else None),
                        reviewed_at=(prior["reviewed_at"] if prior else None),
                        review_comment=(prior["review_comment"] if prior else ''),
                        code=self._build_element_change_code(version.code, dedup_key),
                        created_by=version.updated_by,
                        updated_by=version.updated_by,
                    )
            
            changes = list(version.element_changes.all())
            filtered_summary = {
                'added': sum(1 for c in changes if c.change_type == 'ADDED'),
                'modified': sum(1 for c in changes if c.change_type == 'MODIFIED'),
                'deleted': sum(1 for c in changes if c.change_type == 'DELETED'),
                'total_changes': len(changes),
            }
            
            return success_response(
                data={
                    'version': self._serialize_version(version),
                    'changes': [self._serialize_element_change(c) for c in changes],
                    'diff_summary': filtered_summary
                },
                message="Version changes fetched successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)
    
    def review_element_change(self, change_id: Any, user: Any, action: str, comment: str = "") -> Response:
        """
        Review a single element change.
        action: 'APPROVED', 'REJECTED', 'REVERTED', 'SENT_BACK', 'RESOLVED', or 'PENDING'
        """
        try:
            from django.utils import timezone
            from apps.common.choices import TemplateStatusChoices, VersionStatusChoices
            from .models import TemplateElementChange
            
            with transaction.atomic():
                change = TemplateElementChange.objects.select_related('version__template').select_for_update().filter(id=change_id).first()
                
                if not change:
                    raise ResourceNotFoundException(detail="Change not found.")
                
                if action not in ['APPROVED', 'REJECTED', 'REVERTED', 'SENT_BACK', 'RESOLVED', 'PENDING']:
                    raise ValidationException(
                        detail="Invalid action. Must be APPROVED, REJECTED, REVERTED, SENT_BACK, RESOLVED, or PENDING."
                    )
                
                change.approval_status = action
                change.reviewed_by = user
                change.reviewed_at = timezone.now()
                change.review_comment = comment
                change.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at', 'review_comment', 'updated_at'])

                if action == 'SENT_BACK':
                    version = change.version
                    template = getattr(version, 'template', None)

                    if version.version_status == VersionStatusChoices.FOR_REVIEW:
                        version.version_status = VersionStatusChoices.DRAFT
                        version.updated_by = user
                        version.save(update_fields=['version_status', 'updated_by', 'updated_at'])

                    if template is not None:
                        approved_baseline_exists = self._has_approved_baseline(template, exclude_version_id=version.id)
                        desired_template_status = (
                            TemplateStatusChoices.APPROVED
                            if approved_baseline_exists
                            else TemplateStatusChoices.DRAFT
                        )

                        if template.status != desired_template_status:
                            template.status = desired_template_status
                        if comment:
                            template.review_comments = comment
                        template.updated_by = user
                        template.save(update_fields=['status', 'review_comments', 'updated_by', 'updated_at'])
            
            return success_response(
                data=self._serialize_element_change(change),
                message=f"Change {action.lower()} successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)
    
    def approve_draft_version(self, template_id: Any, version_number: int, user: Any) -> Response:
        """
        Approve a draft version after all changes are reviewed.
        Merges approved changes and creates a new approved version.
        """
        try:
            from django.utils import timezone
            from apps.common.choices import TemplateStatusChoices, VersionStatusChoices
            from .models import TemplateVersion
            from .diff_utils import TemplateElementDiffer
            
            instance = self._get_instance_or_raise(template_id)
            
            draft_version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number,
                version_status=VersionStatusChoices.FOR_REVIEW
            ).prefetch_related('element_changes').first()
            
            if not draft_version:
                raise ResourceNotFoundException(detail=f"Version {version_number} in review not found.")
            
            # Check if all changes have been reviewed
            changes = list(draft_version.element_changes.all())
            pending_changes = [c for c in changes if c.approval_status == 'PENDING']
            
            if pending_changes:
                raise ValidationException(
                    detail=f"{len(pending_changes)} change(s) still pending review. All changes must be reviewed before approval."
                )
            
            accepted_statuses = {'APPROVED', 'RESOLVED'}
            rejected_statuses = {'REJECTED', 'REVERTED', 'SENT_BACK'}

            accepted_changes = [c for c in changes if c.approval_status in accepted_statuses]
            rejected_changes = [c for c in changes if c.approval_status in rejected_statuses]

            # Draft document contains all proposed edits. Apply review decisions on top:
            # approve keeps current draft content, reject reverts only that specific change.
            draft_document = self._parse_content_payload(draft_version.template_json)
            if not isinstance(draft_document, dict) or draft_document.get('type') != 'doc':
                draft_document = self._empty_prosemirror_doc()

            base_document: dict[str, Any] = self._empty_prosemirror_doc()
            if draft_version.base_version:
                base_document = self._parse_content_payload(draft_version.base_version.template_json)
                if not isinstance(base_document, dict) or base_document.get('type') != 'doc':
                    base_document = self._empty_prosemirror_doc()

            reviewed_changes = [
                {
                    'element_id': c.element_id,
                    'change_type': c.change_type,
                    'approval_status': c.approval_status,
                    'old_value': c.old_value,
                    'new_value': c.new_value,
                }
                for c in changes
            ]

            differ = TemplateElementDiffer()
            final_document = self._canonicalize_prosemirror_doc(
                differ.merge_reviewed_changes(base_document, draft_document, reviewed_changes)
            )
            
            # Update draft version to approved
            draft_version.version_status = VersionStatusChoices.APPROVED
            draft_version.approved_by = user
            draft_version.approved_at = timezone.now()
            draft_version.published_at = timezone.now()
            draft_version.template_json = final_document
            draft_version.save()
            
            # Update main template content
            instance.prosemirror_json = final_document
            instance.status = TemplateStatusChoices.APPROVED
            instance.updated_by = user
            instance.save(update_fields=['prosemirror_json', 'status', 'updated_by', 'updated_at'])
            
            return success_response(
                data={
                    'version': self._serialize_version(draft_version),
                    'approved_changes': len(accepted_changes),
                    'rejected_changes': len(rejected_changes)
                },
                message=f"Version v{version_number}.0 approved successfully."
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete_draft_version(self, template_id: Any, version_number: int, user: Any) -> Response:
        """Delete (soft delete) a pending draft/in-review version."""
        try:
            from apps.common.choices import VersionStatusChoices
            from .models import TemplateVersion

            instance = self._get_instance_or_raise(template_id)

            draft_version = TemplateVersion.objects.filter(
                template=instance,
                version_number=version_number,
                version_status__in=[VersionStatusChoices.DRAFT, VersionStatusChoices.FOR_REVIEW],
            ).first()

            if not draft_version:
                raise ResourceNotFoundException(
                    detail=f"Pending draft version v{version_number}.0 not found."
                )

            # Hard delete pending drafts so they no longer block future version/code creation.
            # (Soft delete keeps unique key values occupied.)
            draft_version.delete()

            return success_response(
                data={
                    'template_id': str(instance.id),
                    'version_number': version_number,
                    'deleted': True,
                },
                message=f"Draft version v{version_number}.0 deleted successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)


class TemplateVersionService:
    """Service layer for TemplateVersion aggregate operations."""

    def __init__(self, repository: TemplateVersionRepository | None = None) -> None:
        self.repository = repository or TemplateVersionRepository()

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        if getattr(instance, "template_id", None):
            data["template_id"] = str(instance.template_id)
            template = getattr(instance, "template", None)
            if template is not None:
                data["template"] = {
                    "id": str(template.id),
                    "code": template.code,
                    "name": template.name,
                    "template_type": template.template_type,
                }
        else:
            data["template_id"] = ""
            data["template"] = None
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        data["published_at"] = instance.published_at.isoformat() if instance.published_at else None
        return data

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
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
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    def get_all(self, query_params: dict[str, Any] | None = None) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all(query_params=query_params)]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            code = data.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(data)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            new_code = data.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, data)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)
