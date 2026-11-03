#!/usr/bin/env python3
"""Static acceptance for the audit client-IP filter.

Reads the repository copy; never imports the SPA or calls a browser.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(problems: list[str], message: str) -> None:
    problems.append(message)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    problems: list[str] = []

    page = (root / "web/src/pages/AuditPage.tsx").read_text(encoding="utf-8")
    if not re.search(r"type Filters = \{[^}]*\bclientIp\b", page, re.S):
        fail(problems, "AuditPage Filters type is missing clientIp")
    if not re.search(r"function defaults\(\)[\s\S]*?clientIp:\s*''", page):
        fail(problems, "AuditPage defaults() is missing clientIp: ''")
    if not re.search(r"\['client_ip',\s*filters\.clientIp\]", page):
        fail(problems, "queryString is missing ['client_ip', filters.clientIp]")
    if "update('clientIp'" not in page:
        fail(problems, "the filter input does not call update('clientIp', ...)")
    if "t('ip')" not in page and "t('clientIp')" not in page:
        fail(problems, "the client-IP filter label is not localized through t()")

    messages = (root / "web/src/pages/audit-messages.ts").read_text(encoding="utf-8")
    if "t('clientIp')" in page:
        for block in ("auditEn", "auditZh"):
            match = re.search(
                rf"export const {block}(?:\s*:[^=]+)?\s*=\s*\{{([\s\S]*?)\n\}}",
                messages,
            )
            if not match or not re.search(r"\bclientIp\s*:", match.group(1)):
                fail(problems, f"{block} is missing the clientIp label used by AuditPage")

    manual_zh = (root / "docs/guides/manual/zh-CN.md").read_text(encoding="utf-8")
    manual_en = (root / "docs/guides/manual/en.md").read_text(encoding="utf-8")
    zh_filter = next(
        (line for line in manual_zh.splitlines() if "**筛选**" in line), ""
    )
    en_filter = next(
        (line for line in manual_en.splitlines() if "**Filters**" in line), ""
    )
    if "客户端 IP" not in zh_filter:
        fail(problems, "zh-CN manual Filters line does not mention 客户端 IP")
    if "client ip" not in en_filter.lower():
        fail(problems, "en manual Filters line does not mention client IP")

    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    print("ok: client-IP filter wired through backend/UI/manual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
