"""Utilities for semantic ProseMirror document differences.

This module compares ProseMirror JSON nodes only and returns structured
change records suitable for enterprise review workflows.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Tuple


class TemplateElementDiffer:
    """Calculate semantic differences between ProseMirror template contents."""

    _TOKEN_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_\.\-]+)\s*\}\}")
    _ANGLE_TOKEN_PATTERN = re.compile(r"<\s*([A-Za-z0-9_\.\-]+)\s*>")
    _WORD_OR_TOKEN_PATTERN = re.compile(r"\{\{[A-Za-z0-9_\.\-]+\}\}|<[A-Za-z0-9_\.\-]+>|[A-Za-z0-9_]+")
    _DIFF_SEGMENT_PATTERN = re.compile(r"\{\{[A-Za-z0-9_\.\-]+\}\}|<[A-Za-z0-9_\.\-]+>|\s+|[A-Za-z0-9_]+|[^\w\s]")
    _NON_VISIBLE_ATTR_KEYS = {
        "id",
        "element_id",
        "node_id",
        "uuid",
        "guid",
        "key",
        "class",
        "data-id",
        "data-node-id",
        "data-node-view-content",
        "contenteditable",
        "styleId",
        "pm-id",
        "pm-offset",
        "pm-size",
        "data-pm-slice",
    }

    @classmethod
    def _normalize_string(cls, value: str) -> str:
        # Preserve meaningful spacing while normalizing placeholder token wrappers.
        normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("\u00a0", " ")
        normalized = cls._TOKEN_PATTERN.sub(r"{{\1}}", normalized)
        normalized = cls._ANGLE_TOKEN_PATTERN.sub(r"<\1>", normalized)
        return normalized

    @classmethod
    def _normalize_whitespace_edges(cls, value: str) -> str:
        if not value:
            return ""
        return value.rstrip("\r\n")

    @classmethod
    def _tokenize_for_diff(cls, value: str) -> List[str]:
        normalized = cls._normalize_string(value)
        return cls._DIFF_SEGMENT_PATTERN.findall(normalized)

    @classmethod
    def _first_non_space_token(cls, tokens: List[str], start: int) -> str:
        for idx in range(max(0, start), len(tokens)):
            candidate = tokens[idx]
            if candidate and not candidate.isspace():
                return candidate
        return ""

    @classmethod
    def _slice_text_delta(cls, old_text: str, new_text: str) -> Tuple[str, str]:
        old_norm = cls._normalize_string(old_text)
        new_norm = cls._normalize_string(new_text)

        if old_norm == new_norm:
            return old_norm, new_norm

        matcher = SequenceMatcher(None, old_norm, new_norm, autojunk=False)
        old_start = None
        old_end = None
        new_start = None
        new_end = None

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            if old_start is None:
                old_start = i1
                new_start = j1
            old_end = i2
            new_end = j2

        if old_start is None or old_end is None or new_start is None or new_end is None:
            return old_norm, new_norm

        old_fragment = old_norm[old_start:old_end]
        new_fragment = new_norm[new_start:new_end]

        return old_fragment, new_fragment

    @classmethod
    def _delta_text_pair(cls, old_text: str, new_text: str) -> Tuple[str, str]:
        old_norm = cls._normalize_string(old_text)
        new_norm = cls._normalize_string(new_text)

        if not old_norm and not new_norm:
            return "", ""
        if not old_norm:
            return "", new_norm
        if not new_norm:
            return old_norm, ""

        old_tokens = cls._tokenize_for_diff(old_norm)
        new_tokens = cls._tokenize_for_diff(new_norm)

        if not old_tokens and not new_tokens:
            return old_norm, new_norm

        matcher = SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
        old_parts: List[str] = []
        new_parts: List[str] = []
        first_changed_old_idx = None
        first_changed_new_idx = None

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            if first_changed_old_idx is None:
                first_changed_old_idx = i1
            if first_changed_new_idx is None:
                first_changed_new_idx = j1

            if tag in {"replace", "delete"}:
                old_parts.append("".join(old_tokens[i1:i2]))
            if tag in {"replace", "insert"}:
                new_parts.append("".join(new_tokens[j1:j2]))

        old_fragment = "".join(old_parts)
        new_fragment = "".join(new_parts)

        base_old_visible = bool(old_fragment.strip())
        base_new_visible = bool(new_fragment.strip())
        whitespace_only_mutation = old_norm != new_norm and not base_old_visible and not base_new_visible

        # For whitespace-only edits, include an adjacent token to make the delta reviewable.
        # Do not do this for real insert/remove edits, otherwise unrelated text can leak in.
        if whitespace_only_mutation:
            if old_fragment.strip() == "":
                token_hint = cls._first_non_space_token(old_tokens, int(first_changed_old_idx or 0))
                if token_hint:
                    old_fragment = f"{old_fragment}{token_hint}" if old_fragment else token_hint
            if new_fragment.strip() == "":
                token_hint = cls._first_non_space_token(new_tokens, int(first_changed_new_idx or 0))
                if token_hint:
                    new_fragment = f"{new_fragment}{token_hint}" if new_fragment else token_hint

        if whitespace_only_mutation:
            old_fragment = cls._normalize_whitespace_edges(old_fragment)
            new_fragment = cls._normalize_whitespace_edges(new_fragment)
            return old_fragment.strip("\n"), new_fragment.strip("\n")

        old_is_whitespace_only = old_fragment != "" and old_fragment.strip() == ""
        new_is_whitespace_only = new_fragment != "" and new_fragment.strip() == ""

        if not old_is_whitespace_only:
            old_fragment = old_fragment.strip()
        if not new_is_whitespace_only:
            new_fragment = new_fragment.strip()

        old_fragment = cls._normalize_whitespace_edges(old_fragment)
        new_fragment = cls._normalize_whitespace_edges(new_fragment)

        if old_fragment or new_fragment:
            return old_fragment.strip("\n"), new_fragment.strip("\n")

        return cls._slice_text_delta(old_norm, new_norm)

    @classmethod
    def _inline_segments(cls, old_text: str, new_text: str) -> List[Dict[str, str]]:
        """Return an ORDERED list of inline diff segments.

        Each segment is ``{"op": "equal"|"insert"|"delete", "text": ...}`` and the
        segments always appear in reading order. This is the key to a clean,
        Word-style track-changes view: because segments preserve order and
        adjacency, the frontend never has to fuzzy-search rendered text (which was
        the root cause of the scrambled strike-through output).
        """
        old_norm = cls._normalize_string(old_text or "")
        new_norm = cls._normalize_string(new_text or "")

        if old_norm == new_norm:
            return [{"op": "equal", "text": new_norm}] if new_norm else []

        old_tokens = cls._DIFF_SEGMENT_PATTERN.findall(old_norm)
        new_tokens = cls._DIFF_SEGMENT_PATTERN.findall(new_norm)

        if not old_tokens and not new_tokens:
            fallback: List[Dict[str, str]] = []
            if old_norm:
                fallback.append({"op": "delete", "text": old_norm})
            if new_norm:
                fallback.append({"op": "insert", "text": new_norm})
            return fallback

        matcher = SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
        segments: List[Dict[str, str]] = []

        def push(op: str, text: str) -> None:
            if not text:
                return
            if segments and segments[-1]["op"] == op:
                segments[-1]["text"] += text
            else:
                segments.append({"op": op, "text": text})

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                push("equal", "".join(new_tokens[j1:j2]))
            elif tag == "delete":
                push("delete", "".join(old_tokens[i1:i2]))
            elif tag == "insert":
                push("insert", "".join(new_tokens[j1:j2]))
            elif tag == "replace":
                push("delete", "".join(old_tokens[i1:i2]))
                push("insert", "".join(new_tokens[j1:j2]))

        return segments

    @classmethod
    def _token_counts(cls, value: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for token in cls._WORD_OR_TOKEN_PATTERN.findall(cls._normalize_string(value).lower()):
            normalized = token.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
        return counts

    @classmethod
    def _is_token_subset(cls, candidate: str, container: str) -> bool:
        candidate_counts = cls._token_counts(candidate)
        container_counts = cls._token_counts(container)
        if not candidate_counts:
            return True
        for token, count in candidate_counts.items():
            if container_counts.get(token, 0) < count:
                return False
        return True

    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls._normalize_string(value)
        if isinstance(value, list):
            return [cls._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._normalize_value(item) for key, item in value.items()}
        return value

    @classmethod
    def _sanitize_attrs_for_compare(cls, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(attrs, dict):
            return {}

        sanitized: Dict[str, Any] = {}
        for key, raw_value in attrs.items():
            key_text = str(key)
            lowered = key_text.lower()

            if lowered in cls._NON_VISIBLE_ATTR_KEYS:
                continue
            if lowered.startswith("data-"):
                continue
            if lowered in {"pmattrs", "prosemirrorid", "prosemirror_id"}:
                continue

            if lowered == "docxtablestyle":
                # Table style IDs from Word are often non-semantic metadata.
                continue

            sanitized[key_text] = cls._normalize_value(raw_value)

        return sanitized

    @classmethod
    def _content_to_payload(cls, value: Any) -> Dict[str, Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return {}

        if not isinstance(value, dict):
            return {}

        return value

    @classmethod
    def _extract_pm_doc(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload, dict) and payload.get("type") == "doc":
            return payload

        candidates: Iterable[Any] = (payload.get("prosemirror_json"),)
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("type") == "doc":
                return candidate
        return {}

    @classmethod
    def _is_supported_pm_node(cls, node_type: str, attrs: Dict[str, Any]) -> bool:
        normalized = node_type.lower()
        if normalized in {
            "heading",
            "paragraph",
            "image",
            "table",
            "tablerow",
            "table_row",
            "tablecell",
            "table_cell",
            "tableheader",
            "table_header",
            "variable",
        }:
            return True

        if isinstance(attrs.get("binding"), str) and attrs.get("binding", "").strip():
            return True

        if isinstance(attrs.get("variable"), str) and attrs.get("variable", "").strip():
            return True

        if isinstance(attrs.get("variableKey"), str) and attrs.get("variableKey", "").strip():
            return True

        if isinstance(attrs.get("field"), str) and attrs.get("field", "").strip():
            return True

        return False

    @classmethod
    def _node_identifier(cls, node: Dict[str, Any], path: str, node_type: str) -> str:
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        raw_id = attrs.get("id") or attrs.get("element_id") or attrs.get("node_id")
        if isinstance(raw_id, str) and raw_id.strip():
            return raw_id.strip()
        # Deterministic positional fallback so plain text edits do not create synthetic IDs.
        return f"path:{path}:{node_type}"

    @classmethod
    def _node_hash(cls, node: Dict[str, Any]) -> str:
        canonical = json.dumps(cls._normalize_value(node), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _flatten_pm_nodes(cls, doc: Dict[str, Any], page_hint: int = 1) -> List[Dict[str, Any]]:
        flattened: List[Dict[str, Any]] = []

        def collect_text(node: Dict[str, Any]) -> str:
            if not isinstance(node, dict):
                return ""

            node_type = str(node.get("type") or "").lower()

            # Preserve line breaks so multi-line blocks (e.g. addresses) are not
            # concatenated together: "CHENNAI" + "TAMIL" -> "CHENNAI\nTAMIL".
            if node_type in ("hard_break", "hardbreak"):
                return "\n"

            # Plain text node.
            if isinstance(node.get("text"), str):
                return node.get("text", "")

            # Variable / field chips are ATOMIC (they carry no text child).
            # Emit their literal placeholder so the diff can see and align them,
            # e.g. "<loan_tenure>" -> lets "Months" removal be detected correctly.
            attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
            for key in ("binding", "variable", "variableKey", "field"):
                binding = attrs.get(key)
                if isinstance(binding, str) and binding.strip():
                    if key == "field":
                        return f"<{binding.strip()}>"
                    return f"{{{{{binding.strip()}}}}}"

            content = node.get("content")
            if not isinstance(content, list):
                return ""
            parts: List[str] = []
            for child in content:
                if isinstance(child, dict):
                    parts.append(collect_text(child))
            return "".join(parts)

        def walk(node: Dict[str, Any], path: str, page: int, inside_table_cell: bool = False) -> None:
            if not isinstance(node, dict):
                return

            node_type = str(node.get("type") or "unknown")
            node_type_lower = node_type.lower()
            attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
            marks = node.get("marks") if isinstance(node.get("marks"), list) else []
            text = collect_text(node)
            node_page = int(attrs.get("page") or page)
            node_id = cls._node_identifier(node, path, node_type)

            # Compare only supported semantic nodes from the canonical ProseMirror model.
            skip_descendant_textual = inside_table_cell and node_type_lower in {"paragraph", "heading", "variable"}
            if cls._is_supported_pm_node(node_type, attrs) and not skip_descendant_textual:
                flattened.append(
                    {
                        "id": node_id,
                        "path": path,
                        "type": node_type,
                        "text": cls._normalize_string(text),
                        "attrs": attrs,
                        "marks": marks,
                        "page": node_page,
                        "raw": node,
                    }
                )

            content = node.get("content")
            if isinstance(content, list):
                child_inside_table_cell = inside_table_cell or node_type_lower in {"tablecell", "table_cell", "tableheader", "table_header"}
                for index, child in enumerate(content):
                    if isinstance(child, dict):
                        walk(child, f"{path}.{index}", node_page, child_inside_table_cell)

        walk(doc, "0", page_hint)
        return flattened


    @staticmethod
    def _node_sort_key(node: Dict[str, Any]) -> int:
        path = str(node.get("path") or "")
        numbers = [int(part) for part in re.findall(r"\d+", path)]
        return numbers[-1] if numbers else 0

    @classmethod
    def _normalized_node_text(cls, node: Dict[str, Any]) -> str:
        text = str(node.get("text") or "")
        if text:
            return cls._normalize_string(text).lower()

        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        for key in ("binding", "variable", "variableKey", "field"):
            binding = attrs.get(key)
            if isinstance(binding, str) and binding.strip():
                if key == "field":
                    return cls._normalize_string(f"<{binding}>").lower()
                return cls._normalize_string(f"{{{{{binding}}}}}").lower()

        return ""

    @classmethod
    def _table_shape(cls, node: Dict[str, Any]) -> Dict[str, int]:
        raw = node.get("raw") if isinstance(node.get("raw"), dict) else node
        content = raw.get("content") if isinstance(raw.get("content"), list) else []

        if str(raw.get("type") or "").lower() == "table":
            rows = [child for child in content if isinstance(child, dict) and str(child.get("type") or "").lower() in {"tablerow", "table_row"}]
            row_count = len(rows)
            col_count = 0
            for row in rows:
                row_cells = row.get("content") if isinstance(row.get("content"), list) else []
                col_count = max(
                    col_count,
                    len(
                        [
                            cell
                            for cell in row_cells
                            if isinstance(cell, dict)
                            and str(cell.get("type") or "").lower() in {"tablecell", "table_cell", "tableheader", "table_header"}
                        ]
                    ),
                )
            return {"rows": row_count, "cols": col_count}

        if str(raw.get("type") or "").lower() in {"tablerow", "table_row"}:
            cells = [
                child
                for child in content
                if isinstance(child, dict)
                and str(child.get("type") or "").lower() in {"tablecell", "table_cell", "tableheader", "table_header"}
            ]
            return {"cells": len(cells)}

        return {}

    @classmethod
    def _normalized_compare_payload(cls, node: Dict[str, Any]) -> Any:
        node_type = str(node.get("type") or "").lower()
        attrs = cls._sanitize_attrs_for_compare(node.get("attrs") if isinstance(node.get("attrs"), dict) else {})

        if node_type == "table":
            return cls._normalize_value(
                {
                    "type": "table",
                    "attrs": attrs,
                    "shape": cls._table_shape(node),
                }
            )

        if node_type in {"tablerow", "table_row"}:
            return cls._normalize_value(
                {
                    "type": "tableRow",
                    "attrs": attrs,
                    "shape": cls._table_shape(node),
                }
            )

        if node_type in {"tablecell", "table_cell", "tableheader", "table_header"}:
            return cls._normalize_value(
                {
                    "type": "tableCell" if node_type in {"tablecell", "table_cell"} else "tableHeader",
                    "attrs": attrs,
                    "text": cls._normalize_string(str(node.get("text") or "")),
                }
            )

        return cls._normalize_value(node)

    @staticmethod
    def _path_indices(path: str) -> List[int]:
        if not isinstance(path, str):
            return []
        return [int(part) for part in re.findall(r"\d+", path)]

    @classmethod
    def _table_coordinates(cls, node: Dict[str, Any] | None) -> Dict[str, int]:
        if not isinstance(node, dict):
            return {}

        node_type = str(node.get("type") or "").lower()
        indices = cls._path_indices(str(node.get("path") or ""))
        if not indices:
            return {}

        if node_type in {"tablecell", "table_cell", "tableheader", "table_header"} and len(indices) >= 4:
            return {
                "tableIndex": indices[-4],
                "rowIndex": indices[-2],
                "columnIndex": indices[-1],
            }

        if node_type in {"tablerow", "table_row"} and len(indices) >= 3:
            return {
                "tableIndex": indices[-3],
                "rowIndex": indices[-1],
            }

        if node_type == "table":
            return {
                "tableIndex": indices[-1],
            }

        return {}

    @classmethod
    def _is_empty_placeholder_node(cls, node: Dict[str, Any]) -> bool:
        node_type = str(node.get("type") or "").lower()
        if node_type != "paragraph":
            return False

        if cls._normalized_node_text(node).strip():
            return False

        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        # Preserve paragraphs that carry meaningful attributes (e.g. variables/bindings).
        for key in ("binding", "variable", "variableKey", "field"):
            value = attrs.get(key)
            if isinstance(value, str) and value.strip():
                return False

        return True

    @classmethod
    def _candidate_match_score(cls, old_node: Dict[str, Any], new_node: Dict[str, Any]) -> int:
        score = 0
        old_type = str(old_node.get("type") or "")
        new_type = str(new_node.get("type") or "")
        if old_type != new_type:
            return -1

        score += 5

        old_text = cls._normalized_node_text(old_node)
        new_text = cls._normalized_node_text(new_node)
        if old_text and new_text:
            if old_text == new_text:
                score += 8
            elif old_text in new_text or new_text in old_text:
                score += 3

        old_attrs = old_node.get("attrs") if isinstance(old_node.get("attrs"), dict) else {}
        new_attrs = new_node.get("attrs") if isinstance(new_node.get("attrs"), dict) else {}

        for key in ("binding", "imageUrl", "src", "label"):
            if old_attrs.get(key) and old_attrs.get(key) == new_attrs.get(key):
                score += 4

        old_index = cls._node_sort_key(old_node)
        new_index = cls._node_sort_key(new_node)
        score += max(0, 3 - abs(old_index - new_index))
        return score

    @classmethod
    def _align_nodes_by_similarity(
        cls,
        old_nodes: List[Dict[str, Any]],
        new_nodes: List[Dict[str, Any]],
    ) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        unmatched_old = old_nodes.copy()
        unmatched_new = new_nodes.copy()

        consumed_old: set[str] = set()
        consumed_new: set[str] = set()

        while True:
            best_score = -1
            best_old = None
            best_new = None

            for old_node in unmatched_old:
                old_id = str(old_node.get("id") or "")
                if old_id in consumed_old:
                    continue
                for new_node in unmatched_new:
                    new_id = str(new_node.get("id") or "")
                    if new_id in consumed_new:
                        continue
                    score = cls._candidate_match_score(old_node, new_node)
                    if score > best_score:
                        best_score = score
                        best_old = old_node
                        best_new = new_node

            if best_score < 7 or best_old is None or best_new is None:
                break

            old_id = str(best_old.get("id") or "")
            new_id = str(best_new.get("id") or "")
            consumed_old.add(old_id)
            consumed_new.add(new_id)
            pairs.append((best_old, best_new))

        remaining_old = [
            item for item in unmatched_old if str(item.get("id") or "") not in consumed_old
        ]
        remaining_new = [
            item for item in unmatched_new if str(item.get("id") or "") not in consumed_new
        ]

        return pairs, remaining_old, remaining_new

    @classmethod
    def _infer_semantic_type(cls, old_node: Dict[str, Any] | None, new_node: Dict[str, Any] | None) -> str:
        node = new_node or old_node or {}
        node_type = str(node.get("type") or "").lower()

        if old_node is None and new_node is not None:
            if "variable" in node_type or (new_node.get("attrs") or {}).get("binding"):
                return "VARIABLE_ADDED"
            if node_type in {"image", "logo", "signature", "barcode", "qr_code"}:
                return "IMAGE_ADDED"
            return "TEXT_ADDED"

        if old_node is not None and new_node is None:
            if "variable" in node_type or (old_node.get("attrs") or {}).get("binding"):
                return "VARIABLE_REMOVED"
            if node_type in {"image", "logo", "signature", "barcode", "qr_code"}:
                return "IMAGE_REMOVED"
            return "TEXT_REMOVED"

        old_attrs = old_node.get("attrs") if isinstance(old_node.get("attrs"), dict) else {}
        new_attrs = new_node.get("attrs") if isinstance(new_node.get("attrs"), dict) else {}
        old_text = str(old_node.get("text") or "")
        new_text = str(new_node.get("text") or "")

        old_binding = old_attrs.get("binding") or old_attrs.get("variable") or old_attrs.get("variableKey") or old_attrs.get("field")
        new_binding = new_attrs.get("binding") or new_attrs.get("variable") or new_attrs.get("variableKey") or new_attrs.get("field")
        if old_binding != new_binding:
            return "VARIABLE_MODIFIED"

        if node_type in {"image", "logo", "signature", "barcode", "qr_code"}:
            if old_attrs.get("src") != new_attrs.get("src"):
                return "IMAGE_REPLACED"
            if old_attrs.get("width") != new_attrs.get("width") or old_attrs.get("height") != new_attrs.get("height"):
                return "IMAGE_RESIZED"
            return "IMAGE_REPLACED"

        if node_type == "table":
            old_shape = cls._table_shape(old_node or {})
            new_shape = cls._table_shape(new_node or {})
            if old_shape != new_shape:
                return "TABLE_STRUCTURE_CHANGED"
            if old_attrs != new_attrs:
                return "TABLE_STYLE_CHANGED"
            if old_text != new_text:
                return "TABLE_CONTENT_CHANGED"
            return "UNKNOWN_CHANGE"

        if node_type in {"tablerow", "table_row", "tablecell", "table_cell", "tableheader", "table_header"}:
            if old_text != new_text:
                return "TABLE_CONTENT_CHANGED"
            if old_attrs != new_attrs:
                return "TABLE_STYLE_CHANGED"
            return "UNKNOWN_CHANGE"

        if node_type in {"heading", "paragraph", "variable"} and old_text != new_text:
            if old_text and not new_text:
                return "TEXT_REMOVED"
            if new_text and not old_text:
                return "TEXT_ADDED"

            if cls._is_token_subset(new_text, old_text) and not cls._is_token_subset(old_text, new_text):
                return "TEXT_REMOVED"

            if cls._is_token_subset(old_text, new_text) and not cls._is_token_subset(new_text, old_text):
                return "TEXT_ADDED"

            return "TEXT_MODIFIED"

        old_marks = old_node.get("marks") if isinstance(old_node.get("marks"), list) else []
        new_marks = new_node.get("marks") if isinstance(new_node.get("marks"), list) else []
        if cls._normalize_value(old_marks) != cls._normalize_value(new_marks):
            return "STYLE_CHANGED"

        if old_attrs.get("textAlign") != new_attrs.get("textAlign") or old_attrs.get("align") != new_attrs.get("align"):
            return "ALIGNMENT_CHANGED"
        if old_attrs.get("fontFamily") != new_attrs.get("fontFamily"):
            return "FONT_CHANGED"
        if old_attrs.get("fontSize") != new_attrs.get("fontSize"):
            return "FONT_SIZE_CHANGED"
        if old_attrs.get("color") != new_attrs.get("color"):
            return "FONT_COLOR_CHANGED"
        if old_attrs.get("margin") != new_attrs.get("margin"):
            return "MARGIN_CHANGED"
        if old_attrs.get("padding") != new_attrs.get("padding"):
            return "PADDING_CHANGED"
        if old_attrs.get("pageSize") != new_attrs.get("pageSize"):
            return "PAGE_SIZE_CHANGED"
        if old_attrs.get("orientation") != new_attrs.get("orientation"):
            return "ORIENTATION_CHANGED"
        # REMOVED: POSITION_CHANGED (x, y coordinates - not applicable to ProseMirror documents)

        return "UNKNOWN_CHANGE"

    @classmethod
    def _build_structured_change(
        cls,
        node_id: str,
        coarse_change_type: str,
        old_node: Dict[str, Any] | None,
        new_node: Dict[str, Any] | None,
        index: int,
    ) -> Dict[str, Any]:
        semantic_type = cls._infer_semantic_type(old_node, new_node)
        old_attrs = old_node.get("attrs") if isinstance(old_node and old_node.get("attrs"), dict) else {}
        new_attrs = new_node.get("attrs") if isinstance(new_node and new_node.get("attrs"), dict) else {}
        page = int((new_node or old_node or {}).get("page") or 1)

        old_text_raw = str(old_node.get("text") or "") if isinstance(old_node, dict) else ""
        new_text_raw = str(new_node.get("text") or "") if isinstance(new_node, dict) else ""

        table_cell_types = {"tablecell", "table_cell", "tableheader", "table_header"}
        active_type = str((new_node or old_node or {}).get("type") or "").lower()

        inline_segments = cls._inline_segments(old_text_raw, new_text_raw)

        if active_type in table_cell_types:
            old_text_delta, new_text_delta = old_text_raw, new_text_raw
        else:
            old_text_delta, new_text_delta = cls._delta_text_pair(old_text_raw, new_text_raw)

        return {
            "changeId": f"chg-{node_id}-{index}",
            "nodeId": node_id,
            "page": page,
            "type": semantic_type,
            "coarseType": coarse_change_type,
            "oldValue": old_node.get("raw") if old_node else None,
            "newValue": new_node.get("raw") if new_node else None,
            "oldPath": old_node.get("path") if old_node else None,
            "newPath": new_node.get("path") if new_node else None,
            "oldStyle": old_attrs,
            "newStyle": new_attrs,
            "reviewStatus": "PENDING",
            "reviewer": None,
            "timestamp": None,
            "oldText": old_text_delta,
            "newText": new_text_delta,
            "oldContextText": old_text_raw,
            "newContextText": new_text_raw,
            "diffGranularity": "cell" if active_type in table_cell_types else "token-char",
            "inlineSegments": inline_segments,
            **cls._table_coordinates(new_node or old_node),
        }
    
    @classmethod
    def calculate_diff(cls, old_content: Any, new_content: Any) -> Dict[str, Any]:
        """
        Calculate the difference between two template element lists.
        
        Returns a structure with:
        {
            'added': [elements],
            'modified': [{'element_id': ..., 'old': ..., 'new': ..., 'changes': ...}],
            'deleted': [elements],
            'summary': {'added': count, 'modified': count, 'deleted': count}
        }
        """
        old_payload = cls._content_to_payload(old_content)
        new_payload = cls._content_to_payload(new_content)

        old_pm = cls._extract_pm_doc(old_payload)
        new_pm = cls._extract_pm_doc(new_payload)

        old_nodes = cls._flatten_pm_nodes(old_pm) if old_pm else []
        new_nodes = cls._flatten_pm_nodes(new_pm) if new_pm else []

        old_map = {str(node.get('id')): node for node in old_nodes if node.get('id')}
        new_map = {str(node.get('id')): node for node in new_nodes if node.get('id')}
        
        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())
        
        # Find additions, deletions, and potential modifications
        added_ids = new_ids - old_ids
        deleted_ids = old_ids - new_ids
        common_ids = old_ids & new_ids
        
        unmatched_new = [new_map[eid] for eid in sorted(added_ids)]
        unmatched_old = [old_map[eid] for eid in sorted(deleted_ids)]

        similarity_pairs, remaining_old, remaining_new = cls._align_nodes_by_similarity(unmatched_old, unmatched_new)

        added_elements = remaining_new
        deleted_elements = remaining_old
        modified_elements: List[Dict[str, Any]] = []
        structured_changes: List[Dict[str, Any]] = []
        
        # Check for modifications in common elements
        for index, elem_id in enumerate(sorted(common_ids)):
            old_elem = old_map[elem_id]
            new_elem = new_map[elem_id]
            old_elem_normalized = cls._normalized_compare_payload(old_elem)
            new_elem_normalized = cls._normalized_compare_payload(new_elem)
            old_text = cls._normalized_node_text(old_elem)
            new_text = cls._normalized_node_text(new_elem)

            if old_text and not new_text:
                deleted_elements.append(old_elem)
                continue

            if new_text and not old_text:
                added_elements.append(new_elem)
                continue

            if old_elem_normalized != new_elem_normalized:
                modified_elements.append({
                    'element_id': elem_id,
                    'old': old_elem,
                    'new': new_elem,
                    'changes': {
                        'semantic_type': cls._infer_semantic_type(old_elem, new_elem),
                    }
                })

                structured_changes.append(
                    cls._build_structured_change(
                        node_id=elem_id,
                        coarse_change_type='MODIFIED',
                        old_node=old_elem,
                        new_node=new_elem,
                        index=index,
                    )
                )

        # Treat similarity-aligned nodes as modifications even when IDs differ.
        for old_elem, new_elem in similarity_pairs:
            node_id = str(old_elem.get('id') or new_elem.get('id') or cls._node_hash(new_elem))
            old_elem_normalized = cls._normalized_compare_payload(old_elem)
            new_elem_normalized = cls._normalized_compare_payload(new_elem)
            old_text = cls._normalized_node_text(old_elem)
            new_text = cls._normalized_node_text(new_elem)

            if old_text and not new_text:
                deleted_elements.append(old_elem)
                continue

            if new_text and not old_text:
                added_elements.append(new_elem)
                continue

            if old_elem_normalized == new_elem_normalized:
                continue

            modified_elements.append(
                {
                    'element_id': node_id,
                    'old': old_elem,
                    'new': new_elem,
                    'changes': {
                        'semantic_type': cls._infer_semantic_type(old_elem, new_elem),
                        'matched_by': 'similarity',
                    },
                }
            )
            structured_changes.append(
                cls._build_structured_change(
                    node_id=node_id,
                    coarse_change_type='MODIFIED',
                    old_node=old_elem,
                    new_node=new_elem,
                    index=len(structured_changes),
                )
            )

        # Ignore auto-generated empty paragraphs that represent editor placeholder state.
        if deleted_elements:
            added_elements = [node for node in added_elements if not cls._is_empty_placeholder_node(node)]

        start_index = len(structured_changes)
        for index, node in enumerate(added_elements):
            structured_changes.append(
                cls._build_structured_change(
                    node_id=str(node.get('id') or f'added-{index}'),
                    coarse_change_type='ADDED',
                    old_node=None,
                    new_node=node,
                    index=start_index + index,
                )
            )

        start_index = len(structured_changes)
        for index, node in enumerate(deleted_elements):
            structured_changes.append(
                cls._build_structured_change(
                    node_id=str(node.get('id') or f'deleted-{index}'),
                    coarse_change_type='DELETED',
                    old_node=node,
                    new_node=None,
                    index=start_index + index,
                )
            )

        semantic_summary: Dict[str, int] = {}
        for change in structured_changes:
            key = str(change.get('type') or 'UNKNOWN_CHANGE')
            semantic_summary[key] = semantic_summary.get(key, 0) + 1
        
        return {
            'added': added_elements,
            'modified': modified_elements,
            'deleted': deleted_elements,
            'summary': {
                'added': len(added_elements),
                'modified': len(modified_elements),
                'deleted': len(deleted_elements),
                'total_changes': len(added_elements) + len(modified_elements) + len(deleted_elements)
            },
            'structured_changes': structured_changes,
            'semantic_summary': semantic_summary,
        }
    
    @staticmethod
    def generate_change_summary(diff_data: Dict[str, Any]) -> str:
        """Generate a human-readable summary of changes."""
        summary = diff_data.get('summary', {})
        parts = []
        
        if summary.get('added', 0) > 0:
            parts.append(f"{summary['added']} element(s) added")
        if summary.get('modified', 0) > 0:
            parts.append(f"{summary['modified']} element(s) modified")
        if summary.get('deleted', 0) > 0:
            parts.append(f"{summary['deleted']} element(s) deleted")
        
        if not parts:
            return "No changes"
        
        return ", ".join(parts)
    
    @staticmethod
    def extract_element_changes(diff_data: Dict[str, Any]) -> List[Tuple[str, str, Any, Any]]:
        """
        Extract individual element changes for TemplateElementChange model.
        
        Returns: List of (element_id, change_type, old_value, new_value) tuples
        """
        changes = []
        
        structured_by_node = {
            str(item.get('nodeId')): item
            for item in diff_data.get('structured_changes', [])
            if isinstance(item, dict) and item.get('nodeId')
        }

        for elem in diff_data.get('added', []):
            elem_id = str(elem.get('id', f"new_{elem.get('type', 'unknown')}"))
            semantic = structured_by_node.get(elem_id, {})
            enriched_new = copy.deepcopy(elem)
            if semantic:
                enriched_new['_semantic'] = semantic
            changes.append((elem_id, 'ADDED', None, enriched_new))

        for mod in diff_data.get('modified', []):
            elem_id = str(mod.get('element_id'))
            old_val = copy.deepcopy(mod.get('old'))
            new_val = copy.deepcopy(mod.get('new'))
            semantic = structured_by_node.get(elem_id, {})
            if semantic:
                if isinstance(old_val, dict):
                    old_val['_semantic'] = semantic
                if isinstance(new_val, dict):
                    new_val['_semantic'] = semantic
            changes.append((elem_id, 'MODIFIED', old_val, new_val))

        for elem in diff_data.get('deleted', []):
            elem_id = str(elem.get('id', f"deleted_{elem.get('type', 'unknown')}"))
            semantic = structured_by_node.get(elem_id, {})
            enriched_old = copy.deepcopy(elem)
            if semantic:
                enriched_old['_semantic'] = semantic
            changes.append((elem_id, 'DELETED', enriched_old, None))
        
        return changes
    
    @staticmethod
    def merge_approved_changes(
        base_document: Dict[str, Any],
        approved_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge approved changes into a base ProseMirror document.
        
        approved_changes: List of change records with element_id/change_type/new_value.
        """
        if not isinstance(base_document, dict) or base_document.get('type') != 'doc':
            return {'type': 'doc', 'content': [{'type': 'paragraph'}]}

        merged = copy.deepcopy(base_document)
        if not isinstance(merged.get('content'), list):
            merged['content'] = []

        def node_id_from_raw(node: Any, fallback: str | None = None) -> str:
            if isinstance(node, dict):
                attrs = node.get('attrs') if isinstance(node.get('attrs'), dict) else {}
                candidate = attrs.get('id') or attrs.get('element_id') or attrs.get('node_id')
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            return fallback or ''

        def walk_with_parent(root: Dict[str, Any]) -> List[Tuple[List[Any], int, Dict[str, Any], str]]:
            found: List[Tuple[List[Any], int, Dict[str, Any], str]] = []

            def walk(node: Dict[str, Any], path: str, parent_content: List[Any] | None, index: int | None) -> None:
                if not isinstance(node, dict):
                    return
                if parent_content is not None and index is not None:
                    found.append((parent_content, index, node, path))
                content = node.get('content')
                if isinstance(content, list):
                    for child_index, child in enumerate(content):
                        if isinstance(child, dict):
                            walk(child, f"{path}.{child_index}", content, child_index)

            walk(root, '0', None, None)
            return found

        def find_node_ref(root: Dict[str, Any], element_id: str) -> Tuple[List[Any], int, Dict[str, Any]] | None:
            for parent_content, idx, node, path in walk_with_parent(root):
                current_id = node_id_from_raw(node, fallback=f"path:{path}:{node.get('type', 'unknown')}")
                if current_id == element_id:
                    return parent_content, idx, node
            return None

        def get_content_list_at_path(root: Dict[str, Any], path: str) -> List[Any] | None:
            if not isinstance(path, str) or not path:
                return root.get('content') if isinstance(root.get('content'), list) else None

            parts = [segment for segment in path.split('.') if segment.strip()]
            if parts and parts[0] == '0':
                parts = parts[1:]

            current: Dict[str, Any] = root
            for segment in parts:
                if not segment.isdigit():
                    return None
                content = current.get('content')
                if not isinstance(content, list):
                    return None
                idx = int(segment)
                if idx < 0 or idx >= len(content):
                    return None
                child = content[idx]
                if not isinstance(child, dict):
                    return None
                current = child

            content = current.get('content')
            if not isinstance(content, list):
                current['content'] = []
            return current.get('content')

        def extract_insert_slot(change_row: Dict[str, Any]) -> Tuple[List[Any] | None, int | None]:
            new_value = change_row.get('new_value')
            semantic = {}
            if isinstance(new_value, dict) and isinstance(new_value.get('_semantic'), dict):
                semantic = new_value.get('_semantic')

            path = None
            if isinstance(semantic.get('newPosition'), dict):
                raw_path = semantic['newPosition'].get('path')
                if isinstance(raw_path, str) and raw_path.strip():
                    path = raw_path.strip()

            if not path:
                return merged.get('content') if isinstance(merged.get('content'), list) else None, None

            path_parts = [segment for segment in path.split('.') if segment.strip()]
            if not path_parts:
                return merged.get('content') if isinstance(merged.get('content'), list) else None, None

            index = None
            if path_parts[-1].isdigit():
                index = int(path_parts[-1])
                parent_path = '.'.join(path_parts[:-1])
            else:
                parent_path = '.'.join(path_parts)

            parent_content = get_content_list_at_path(merged, parent_path)
            return parent_content, index

        for change in approved_changes:
            if not isinstance(change, dict):
                continue

            change_type = str(change.get('change_type') or '').upper()
            element_id = str(change.get('element_id') or '')
            new_value = change.get('new_value')

            if change_type == 'DELETED':
                if not element_id:
                    continue
                ref = find_node_ref(merged, element_id)
                if ref:
                    parent_content, idx, _ = ref
                    if 0 <= idx < len(parent_content):
                        parent_content.pop(idx)
                continue

            if change_type not in {'ADDED', 'MODIFIED'}:
                continue

            if not isinstance(new_value, dict):
                continue

            new_node_id = node_id_from_raw(new_value, fallback=element_id)
            target_id = element_id or new_node_id

            existing_ref = find_node_ref(merged, target_id) if target_id else None

            if existing_ref:
                parent_content, idx, _ = existing_ref
                if 0 <= idx < len(parent_content):
                    parent_content[idx] = copy.deepcopy(new_value)
                continue

            parent_content, insert_index = extract_insert_slot(change)
            if not isinstance(parent_content, list):
                parent_content = merged.get('content') if isinstance(merged.get('content'), list) else []
                merged['content'] = parent_content

            if insert_index is None:
                parent_content.append(copy.deepcopy(new_value))
            else:
                safe_index = max(0, min(insert_index, len(parent_content)))
                parent_content.insert(safe_index, copy.deepcopy(new_value))

        return merged

    @staticmethod
    def _resolve_change_node(value: Any, prefer: str = 'new') -> Any:
        """Resolve the most concrete ProseMirror node payload from a change row value."""
        if not isinstance(value, dict):
            return value

        semantic = value.get('_semantic') if isinstance(value.get('_semantic'), dict) else {}
        semantic_key = 'newValue' if prefer == 'new' else 'oldValue'
        semantic_value = semantic.get(semantic_key) if isinstance(semantic, dict) else None
        if isinstance(semantic_value, dict) and isinstance(semantic_value.get('type'), str):
            return semantic_value

        raw = value.get('raw')
        if isinstance(raw, dict) and isinstance(raw.get('type'), str):
            return raw

        return value

    @staticmethod
    def merge_reviewed_changes(
        base_document: Dict[str, Any],
        draft_document: Dict[str, Any],
        reviewed_changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge per-change review decisions using Word-style semantics.

        Design:
        - Draft document is the source-of-truth for proposed edits.
        - Approve keeps draft content as-is.
        - Reject reverts only that specific change.
        """
        if not isinstance(draft_document, dict) or draft_document.get('type') != 'doc':
            draft_document = {'type': 'doc', 'content': [{'type': 'paragraph'}]}

        if not isinstance(base_document, dict) or base_document.get('type') != 'doc':
            base_document = {'type': 'doc', 'content': [{'type': 'paragraph'}]}

        merged = copy.deepcopy(draft_document)
        if not isinstance(merged.get('content'), list):
            merged['content'] = []

        rejected_statuses = {'REJECTED', 'REVERTED', 'SENT_BACK'}

        def node_id_from_raw(node: Any, fallback: str | None = None) -> str:
            if isinstance(node, dict):
                attrs = node.get('attrs') if isinstance(node.get('attrs'), dict) else {}
                candidate = attrs.get('id') or attrs.get('element_id') or attrs.get('node_id')
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            return fallback or ''

        def walk_with_parent(root: Dict[str, Any]) -> List[Tuple[List[Any], int, Dict[str, Any], str]]:
            found: List[Tuple[List[Any], int, Dict[str, Any], str]] = []

            def walk(node: Dict[str, Any], path: str, parent_content: List[Any] | None, index: int | None) -> None:
                if not isinstance(node, dict):
                    return
                if parent_content is not None and index is not None:
                    found.append((parent_content, index, node, path))
                content = node.get('content')
                if isinstance(content, list):
                    for child_index, child in enumerate(content):
                        if isinstance(child, dict):
                            walk(child, f"{path}.{child_index}", content, child_index)

            walk(root, '0', None, None)
            return found

        def find_node_ref(root: Dict[str, Any], element_id: str) -> Tuple[List[Any], int, Dict[str, Any]] | None:
            for parent_content, idx, node, path in walk_with_parent(root):
                current_id = node_id_from_raw(node, fallback=f"path:{path}:{node.get('type', 'unknown')}")
                if current_id == element_id:
                    return parent_content, idx, node
            return None

        def find_by_value(root: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[List[Any], int, Dict[str, Any]] | None:
            candidate_norm = TemplateElementDiffer._normalize_value(candidate)
            for parent_content, idx, node, _ in walk_with_parent(root):
                if TemplateElementDiffer._normalize_value(node) == candidate_norm:
                    return parent_content, idx, node
            return None

        def get_content_list_at_path(root: Dict[str, Any], path: str) -> List[Any] | None:
            if not isinstance(path, str) or not path:
                return root.get('content') if isinstance(root.get('content'), list) else None

            parts = [segment for segment in path.split('.') if segment.strip()]
            if parts and parts[0] == '0':
                parts = parts[1:]

            current: Dict[str, Any] = root
            for segment in parts:
                if not segment.isdigit():
                    return None
                content = current.get('content')
                if not isinstance(content, list):
                    return None
                idx = int(segment)
                if idx < 0 or idx >= len(content):
                    return None
                child = content[idx]
                if not isinstance(child, dict):
                    return None
                current = child

            content = current.get('content')
            if not isinstance(content, list):
                current['content'] = []
            return current.get('content')

        def slot_from_element_id(element_id: str) -> Tuple[List[Any] | None, int | None]:
            if not isinstance(element_id, str) or not element_id.startswith('path:'):
                return merged.get('content') if isinstance(merged.get('content'), list) else None, None

            # Expected format: path:0.2.1:paragraph
            raw = element_id[len('path:'):]
            path_part = raw.split(':', 1)[0]
            path_tokens = [token for token in path_part.split('.') if token.strip()]
            if not path_tokens:
                return merged.get('content') if isinstance(merged.get('content'), list) else None, None

            insert_index = int(path_tokens[-1]) if path_tokens[-1].isdigit() else None
            parent_path = '.'.join(path_tokens[:-1])
            parent_content = get_content_list_at_path(merged, parent_path)
            return parent_content, insert_index

        for change in reviewed_changes:
            if not isinstance(change, dict):
                continue

            decision = str(change.get('approval_status') or '').upper()
            if decision not in rejected_statuses:
                continue

            change_type = str(change.get('change_type') or '').upper()
            element_id = str(change.get('element_id') or '')

            old_node = TemplateElementDiffer._resolve_change_node(change.get('old_value'), prefer='old')
            new_node = TemplateElementDiffer._resolve_change_node(change.get('new_value'), prefer='new')

            if change_type == 'ADDED':
                # Reject add: remove inserted node from draft document.
                ref = find_node_ref(merged, element_id) if element_id else None
                if not ref and isinstance(new_node, dict):
                    ref = find_by_value(merged, new_node)
                if ref:
                    parent_content, idx, _ = ref
                    if 0 <= idx < len(parent_content):
                        parent_content.pop(idx)
                continue

            if change_type == 'DELETED':
                # Reject delete: restore old node if absent.
                if not isinstance(old_node, dict):
                    continue

                old_node_id = node_id_from_raw(old_node, fallback=element_id)
                existing_ref = find_node_ref(merged, old_node_id) if old_node_id else None
                if existing_ref:
                    parent_content, idx, existing_node = existing_ref
                    if 0 <= idx < len(parent_content):
                        existing_norm = TemplateElementDiffer._normalize_value(existing_node)
                        old_norm = TemplateElementDiffer._normalize_value(old_node)
                        if existing_norm != old_norm:
                            parent_content[idx] = copy.deepcopy(old_node)
                    continue

                parent_content, insert_index = slot_from_element_id(element_id)
                if not isinstance(parent_content, list):
                    parent_content = merged.get('content') if isinstance(merged.get('content'), list) else []
                    merged['content'] = parent_content

                restored = copy.deepcopy(old_node)
                if insert_index is None:
                    parent_content.append(restored)
                else:
                    safe_index = max(0, min(insert_index, len(parent_content)))
                    parent_content.insert(safe_index, restored)
                continue

            if change_type == 'MODIFIED':
                # Reject modify: restore old node in place.
                if not isinstance(old_node, dict):
                    continue

                ref = find_node_ref(merged, element_id) if element_id else None
                if not ref and isinstance(new_node, dict):
                    new_node_id = node_id_from_raw(new_node, fallback='')
                    if new_node_id:
                        ref = find_node_ref(merged, new_node_id)
                if not ref and isinstance(new_node, dict):
                    ref = find_by_value(merged, new_node)

                if ref:
                    parent_content, idx, _ = ref
                    if 0 <= idx < len(parent_content):
                        parent_content[idx] = copy.deepcopy(old_node)
                else:
                    parent_content, insert_index = slot_from_element_id(element_id)
                    if not isinstance(parent_content, list):
                        parent_content = merged.get('content') if isinstance(merged.get('content'), list) else []
                        merged['content'] = parent_content

                    restored = copy.deepcopy(old_node)
                    if insert_index is None:
                        parent_content.append(restored)
                    else:
                        safe_index = max(0, min(insert_index, len(parent_content)))
                        parent_content.insert(safe_index, restored)

        return merged
