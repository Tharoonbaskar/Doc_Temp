from apps.templates.diff_utils import TemplateElementDiffer

d = TemplateElementDiffer()

tests = [
    (
        "VARIABLE",
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "variable",
                        "attrs": {
                            "id": "VAR001",
                            "binding": "customer_name",
                        },
                        "content": [
                            {
                                "type": "text",
                                "text": "Customer Name",
                            }
                        ],
                    }
                ],
            }
        },
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "variable",
                        "attrs": {
                            "id": "VAR001",
                            "binding": "customer_full_name",
                        },
                        "content": [
                            {
                                "type": "text",
                                "text": "Customer Full Name",
                            }
                        ],
                    }
                ],
            }
        },
    ),
    (
        "TABLE",
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "table",
                        "attrs": {"id": "TBL001"},
                        "content": [
                            {
                                "type": "tableRow",
                                "content": [
                                    {
                                        "type": "tableCell",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {
                                                        "type": "text",
                                                        "text": "Amount",
                                                    }
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        },
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "table",
                        "attrs": {"id": "TBL001"},
                        "content": [
                            {
                                "type": "tableRow",
                                "content": [
                                    {
                                        "type": "tableCell",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {
                                                        "type": "text",
                                                        "text": "Loan Amount",
                                                    }
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        },
    ),
    (
        "IMAGE",
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "image",
                        "attrs": {
                            "id": "IMG001",
                            "src": "/img/logo-v1.png",
                            "width": 120,
                            "height": 40,
                        },
                    }
                ],
            }
        },
        {
            "prosemirror_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "image",
                        "attrs": {
                            "id": "IMG001",
                            "src": "/img/logo-v2.png",
                            "width": 120,
                            "height": 40,
                        },
                    }
                ],
            }
        },
    ),
]

for name, old_doc, new_doc in tests:
    diff = d.calculate_diff(old_doc, new_doc)

    print("=" * 80)
    print(name)
    print("=" * 80)
    print("summary:", diff.get("summary"))
    print("semantic_summary:", diff.get("semantic_summary"))
    print("added:", len(diff.get("added", [])))
    print("deleted:", len(diff.get("deleted", [])))
    print("modified:", len(diff.get("modified", [])))
    print("modified_element_ids:", [m.get("element_id") for m in diff.get("modified", [])])
    print("structured_types:", [c.get("type") for c in diff.get("structured_changes", [])])
    print("structured_node_ids:", [c.get("nodeId") for c in diff.get("structured_changes", [])])