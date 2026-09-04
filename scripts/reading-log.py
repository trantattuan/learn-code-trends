#!/usr/bin/env python3
"""Quản lý nhật ký đọc báo cáo trend (trends/READING-LOG.md).

Chỉ dùng thư viện chuẩn. Cách dùng:

    ./scripts/reading-log.py                  # xem tiến độ + báo cáo cần đọc tiếp
    ./scripts/reading-log.py sync             # nạp báo cáo mới vào nhật ký
    ./scripts/reading-log.py next             # in đường dẫn báo cáo chưa đọc cũ nhất
    ./scripts/reading-log.py read 2026-08-09  # đánh dấu đã đọc (mặc định: hôm nay)
    ./scripts/reading-log.py read next --note "áp dụng vào X"
    ./scripts/reading-log.py reading 2026-08-16
    ./scripts/reading-log.py skip 2026-08-02
    ./scripts/reading-log.py reset 2026-08-02
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "trends" / "READING-LOG.md"
REPORTS = ROOT / "trends" / "reports"

UNREAD = "⬜ Chưa đọc"
READING = "🔄 Đang đọc"
READ = "✅ Đã đọc"
SKIPPED = "⏭️ Bỏ qua"

STATUSES = {"read": READ, "reading": READING, "skip": SKIPPED, "reset": UNREAD}

ROW_RE = re.compile(
    r"^\|\s*\[(?P<date>\d{4}-\d{2}-\d{2})\]\((?P<link>[^)]*)\)\s*\|"
    r"(?P<status>[^|]*)\|(?P<read_on>[^|]*)\|(?P<note>[^|]*)\|\s*$"
)
TOPIC_RE = re.compile(r"^##\s+\d+\.\s+(.*)$")

TEMPLATE = """\
# Nhật ký đọc báo cáo trend

File này trả lời đúng một câu hỏi: **lần trước tôi đọc tới đâu rồi?**

Không cần nhớ gì. Mỗi lần quay lại chỉ cần chạy:

```bash
./scripts/reading-log.py            # tiến độ + báo cáo cần đọc tiếp
./scripts/reading-log.py read next  # đọc xong thì đánh dấu
```

Script tự quét `trends/reports/`, tự thêm báo cáo mới vào bảng dưới và tự cập
nhật phần tiến độ. Bảng và phần ghi chú bạn cũng có thể sửa tay thoải mái —
script chỉ thêm dòng mới và đổi cột trạng thái, không đụng vào ghi chú của bạn.

<!-- progress:start -->
<!-- progress:end -->

## Bảng tiến độ

Trạng thái: `⬜ Chưa đọc` · `🔄 Đang đọc` · `✅ Đã đọc` · `⏭️ Bỏ qua`

<!-- table:start -->
| Báo cáo | Trạng thái | Ngày đọc | Ghi chú nhanh |
| --- | --- | --- | --- |
<!-- table:end -->

## Ghi chú từng báo cáo

Ba chủ đề của mỗi báo cáo được điền sẵn để bạn nhìn tiêu đề là nhớ ra nội dung.
Phần "Ghi chú của tôi" để trống cho bạn viết: điều đã áp dụng, điều còn nghi ngờ,
việc cần làm.

<!-- details:start -->
<!-- details:end -->
"""


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"Lỗi: {msg}", file=sys.stderr)
    sys.exit(1)


def report_dates() -> list[str]:
    return sorted(p.stem for p in REPORTS.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"))


def topics(date: str) -> list[str]:
    out = []
    for line in (REPORTS / f"{date}.md").read_text(encoding="utf-8").splitlines():
        m = TOPIC_RE.match(line)
        if m:
            out.append(m.group(1).strip())
    return out


def read_log() -> str:
    if not LOG.exists():
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(TEMPLATE, encoding="utf-8")
    return LOG.read_text(encoding="utf-8")


def block(text: str, name: str) -> tuple[int, int]:
    start = text.index(f"<!-- {name}:start -->") + len(f"<!-- {name}:start -->")
    end = text.index(f"<!-- {name}:end -->")
    return start, end


def replace_block(text: str, name: str, body: str) -> str:
    start, end = block(text, name)
    return text[:start] + body + text[end:]


def parse_rows(text: str) -> list[dict]:
    start, end = block(text, "table")
    rows = []
    for line in text[start:end].splitlines():
        m = ROW_RE.match(line)
        if m:
            rows.append(
                {
                    "date": m.group("date"),
                    "link": m.group("link"),
                    "status": m.group("status").strip(),
                    "read_on": m.group("read_on").strip(),
                    "note": m.group("note").strip(),
                }
            )
    return rows


def render_rows(rows: list[dict]) -> str:
    head = "\n| Báo cáo | Trạng thái | Ngày đọc | Ghi chú nhanh |\n| --- | --- | --- | --- |\n"
    body = "".join(
        f"| [{r['date']}]({r['link']}) | {r['status']} | {r['read_on'] or '—'} | {r['note']} |\n"
        for r in rows
    )
    return head + body


def sync(text: str) -> tuple[str, list[str]]:
    """Thêm báo cáo mới vào bảng và phần ghi chú. Không đụng dữ liệu cũ."""
    rows = parse_rows(text)
    known = {r["date"] for r in rows}
    added = [d for d in report_dates() if d not in known]

    for date in added:
        rows.append(
            {
                "date": date,
                "link": f"reports/{date}.md",
                "status": UNREAD,
                "read_on": "—",
                "note": "",
            }
        )
    rows.sort(key=lambda r: r["date"])
    text = replace_block(text, "table", render_rows(rows))

    if added:
        start, end = block(text, "details")
        chunks = [text[start:end].rstrip("\n")]
        for date in added:
            lines = [f"\n### {date}", ""]
            tps = topics(date)
            if tps:
                lines += [f"{i}. {t}" for i, t in enumerate(tps, 1)]
            else:
                lines.append("_(không đọc được tiêu đề chủ đề từ file báo cáo)_")
            lines += ["", "**Ghi chú của tôi:**", "-", ""]
            chunks.append("\n".join(lines))
        text = replace_block(text, "details", "\n".join(chunks) + "\n")

    return text, added


def render_progress(rows: list[dict]) -> str:
    total = len(rows)
    done = sum(1 for r in rows if r["status"] in (READ, SKIPPED))
    pending = [r for r in rows if r["status"] not in (READ, SKIPPED)]
    last = [r for r in rows if r["status"] == READ]
    last_read = last[-1]["date"] if last else None

    lines = ["", f"**Tiến độ:** {done}/{total} báo cáo đã xử lý."]
    if last_read:
        lines.append(f"**Đọc gần nhất:** [{last_read}](reports/{last_read}.md)")
    else:
        lines.append("**Đọc gần nhất:** chưa có.")
    if pending:
        nxt = pending[0]
        tag = " (đang đọc dở)" if nxt["status"] == READING else ""
        lines.append(f"**👉 Đọc tiếp:** [{nxt['date']}](reports/{nxt['date']}.md){tag}")
        if len(pending) > 1:
            rest = ", ".join(r["date"] for r in pending[1:])
            lines.append(f"**Còn tồn:** {len(pending) - 1} báo cáo — {rest}")
    else:
        lines.append("**👉 Đọc tiếp:** không còn báo cáo nào tồn đọng. 🎉")
    lines.append("")
    return "\n".join(lines)


def save(text: str) -> list[dict]:
    rows = parse_rows(text)
    text = replace_block(text, "progress", render_progress(rows))
    LOG.write_text(text, encoding="utf-8")
    return rows


def resolve(rows: list[dict], token: str) -> str:
    if token == "next":
        pending = [r for r in rows if r["status"] not in (READ, SKIPPED)]
        if not pending:
            fail("không còn báo cáo nào chưa đọc.")
        return pending[0]["date"]
    if token == "latest":
        if not rows:
            fail("chưa có báo cáo nào.")
        return rows[-1]["date"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        fail(f"'{token}' không phải ngày YYYY-MM-DD (hoặc từ khoá next/latest).")
    if token not in {r["date"] for r in rows}:
        fail(f"không có báo cáo {token} trong nhật ký.")
    return token


def print_status(rows: list[dict]) -> None:
    print(render_progress(rows).strip())
    print()
    for r in rows:
        print(f"  {r['status']:<12} {r['date']}  {r['read_on']:<12} {r['note']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Nhật ký đọc báo cáo trend.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status", help="xem tiến độ (mặc định)")
    sub.add_parser("sync", help="nạp báo cáo mới vào nhật ký")
    sub.add_parser("next", help="in đường dẫn báo cáo chưa đọc cũ nhất")
    for name, helptext in (
        ("read", "đánh dấu đã đọc"),
        ("reading", "đánh dấu đang đọc dở"),
        ("skip", "bỏ qua báo cáo này"),
        ("reset", "trả về chưa đọc"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("date", help="YYYY-MM-DD, hoặc 'next' / 'latest'")
        p.add_argument("--note", default="", help="ghi chú nhanh cho dòng này")
        p.add_argument("--on", default="", help="ngày đọc (mặc định: hôm nay)")

    args = ap.parse_args()
    cmd = args.cmd or "status"

    text = read_log()
    text, added = sync(text)

    if cmd in STATUSES:
        rows = parse_rows(text)
        date = resolve(rows, args.date)
        for r in rows:
            if r["date"] == date:
                r["status"] = STATUSES[cmd]
                if cmd == "read":
                    r["read_on"] = args.on or dt.date.today().isoformat()
                elif cmd == "reset":
                    r["read_on"] = "—"
                if args.note:
                    r["note"] = f"{r['note']} {args.note}".strip()
        text = replace_block(text, "table", render_rows(rows))
        print(f"{date}: {STATUSES[cmd]}")

    rows = save(text)

    if added:
        print(f"Đã nạp {len(added)} báo cáo mới: {', '.join(added)}")

    if cmd == "next":
        pending = [r for r in rows if r["status"] not in (READ, SKIPPED)]
        if not pending:
            print("Không còn báo cáo nào chưa đọc.")
        else:
            print(f"trends/reports/{pending[0]['date']}.md")
    elif cmd == "status":
        print_status(rows)
    elif cmd == "sync" and not added:
        print("Nhật ký đã khớp với thư mục reports/.")


if __name__ == "__main__":
    main()
