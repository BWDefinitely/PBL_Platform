"""Minimal API connectivity check."""

from __future__ import annotations

import os
import requests


def main() -> None:
    """Send a minimal request and print raw response."""
    api_key = os.getenv("JENIYA_API_KEY", "").strip()
    base_url = os.getenv(
        "JENIYA_BASE_URL",
        "https://jeniya.cn/",
    ).strip()
    model = os.getenv("JENIYA_MODEL", "gpt-4o").strip()

    response = requests.post(
        base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": "你好，请回复“连接成功”"}
            ],
            "stream": False,
        },
        timeout=60,
    )

    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type", ""))
    print("BODY:")
    print(response.text[:2000])


if __name__ == "__main__":
    main()