from apps.templates.diff_utils import TemplateElementDiffer

old = {
    "prosemirror_json": {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {
                    "id": "HDR001",
                    "level": 1,
                },
                "content": [
                    {
                        "type": "text",
                        "text": "SAMPLE SANCTION LETTER",
                    }
                ],
            }
        ],
    }
}

new = {
    "prosemirror_json": {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {
                    "id": "HDR001",
                    "level": 1,
                },
                "content": [
                    {
                        "type": "text",
                        "text": "SANCTION LETTER",
                    }
                ],
            }
        ],
    }
}

d = TemplateElementDiffer()
diff = d.calculate_diff(old, new)

print("summary:", diff.get("summary"))
print("semantic_summary:", diff.get("semantic_summary"))
print("added:", len(diff.get("added", [])))
print("deleted:", len(diff.get("deleted", [])))
print("modified:", len(diff.get("modified", [])))
print("modified_element_ids:", [m.get("element_id") for m in diff.get("modified", [])])
print("structured_types:", [c.get("type") for c in diff.get("structured_changes", [])])
print("structured_node_ids:", [c.get("nodeId") for c in diff.get("structured_changes", [])])