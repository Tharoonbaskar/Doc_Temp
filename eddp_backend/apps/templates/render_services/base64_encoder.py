from __future__ import annotations

import base64


class Base64Encoder:
    @staticmethod
    def encode(content: bytes) -> str:
        return base64.b64encode(content).decode("ascii")
