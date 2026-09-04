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
    ./scripts/reading-log.py footers          # gắn link "đã đọc" vào cuối mỗi báo cáo
    ./scripts/reading-log.py from-issue       # xử lý issue bấm từ GitHub (dùng trong CI)
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import secrets
import shutil
import subprocess
import sys
import urllib.parse
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
            lines.append(f"**Sau đó còn:** {len(pending) - 1} báo cáo — {rest}")
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


def open_report(text: str, token: str) -> str:
    """Mở báo cáo để đọc, tự đánh dấu 'đang đọc', đọc xong thì hỏi để chốt lại."""
    rows = parse_rows(text)
    date = resolve(rows, token)
    path = REPORTS / f"{date}.md"

    for r in rows:
        if r["date"] == date and r["status"] == UNREAD:
            r["status"] = READING
    text = replace_block(text, "table", render_rows(rows))
    save(text)

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print(f"(không phải terminal tương tác — đã đánh dấu đang đọc)\n{path}")
        return LOG.read_text(encoding="utf-8")

    pager = os.environ.get("PAGER") or ("less" if shutil.which("less") else "cat")
    subprocess.run([*pager.split(), str(path)], check=False)

    answer = input(f"\nĐã đọc xong {date} chưa? [Y/n/s(bỏ qua)] ").strip().lower()
    if answer.startswith("n"):
        print(f"{date}: {READING} — để dành, lần sau chạy 'read next' là quay lại đúng chỗ.")
        return LOG.read_text(encoding="utf-8")

    status = SKIPPED if answer.startswith("s") else READ
    note = input("Ghi chú nhanh (Enter để bỏ trống): ").strip()

    text = LOG.read_text(encoding="utf-8")
    rows = parse_rows(text)
    for r in rows:
        if r["date"] == date:
            r["status"] = status
            r["read_on"] = dt.date.today().isoformat() if status == READ else "—"
            if note:
                r["note"] = f"{r['note']} {note}".strip()
    print(f"{date}: {status}")
    return replace_block(text, "table", render_rows(rows))


FOOTER_MARK = "<!-- reading-log:footer -->"
ISSUE_MARK_RE = re.compile(r"<!--\s*reading-log:(?P<action>read|skip)\s+(?P<date>\d{4}-\d{2}-\d{2})\s*-->")


def repo_slug() -> str:
    """owner/repo — lấy từ GITHUB_REPOSITORY hoặc git remote."""
    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env
    try:
        url = subprocess.run(
            ["git", "-C", str(ROOT), "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        fail("không xác định được repo (thiếu GITHUB_REPOSITORY và git remote).")
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    if not m:
        fail(f"không đọc được owner/repo từ remote: {url}")
    return m.group(1)


def issue_url(slug: str, action: str, date: str) -> str:
    verb = "Đã đọc" if action == "read" else "Bỏ qua"
    icon = "✅" if action == "read" else "⏭️"
    body = (
        f"<!-- reading-log:{action} {date} -->\n"
        "<!-- Đừng xoá dòng trên — nó cho máy biết bạn nói về báo cáo nào. -->\n\n"
        "Ghi chú (không bắt buộc — viết dưới dòng này rồi bấm nút tạo issue):\n"
    )
    q = urllib.parse.urlencode(
        {"title": f"{icon} {verb} báo cáo {date}", "body": body, "labels": "reading-log"},
        quote_via=urllib.parse.quote,
    )
    return f"https://github.com/{slug}/issues/new?{q}"


def footer_for(slug: str, date: str) -> str:
    return f"""
---

{FOOTER_MARK}

### Đọc xong báo cáo này?

Bấm một link dưới đây, GitHub mở sẵn form — bạn chỉ cần bấm nút tạo issue là xong
(muốn ghi chú thì gõ thêm vào ô nội dung trước khi bấm). Nhật ký sẽ tự cập nhật và
issue tự đóng lại sau khoảng một phút.

[✅ Đánh dấu đã đọc]({issue_url(slug, "read", date)}) &nbsp;·&nbsp; [⏭️ Bỏ qua tuần này]({issue_url(slug, "skip", date)}) &nbsp;·&nbsp; [📖 Xem toàn bộ tiến độ](../READING-LOG.md)
"""


def add_footers() -> list[str]:
    """Gắn footer vào mọi báo cáo chưa có. Idempotent."""
    slug = repo_slug()
    touched = []
    for date in report_dates():
        path = REPORTS / f"{date}.md"
        body = path.read_text(encoding="utf-8")
        if FOOTER_MARK in body:
            continue
        path.write_text(body.rstrip("\n") + "\n" + footer_for(slug, date), encoding="utf-8")
        touched.append(date)
    return touched


def clean_note(body: str) -> str:
    """Lấy ghi chú người dùng gõ trong issue, bỏ marker và dòng hướng dẫn."""
    text = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    lines = [
        ln.strip() for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("Ghi chú (không bắt buộc")
    ]
    note = " ".join(lines).replace("|", "/")
    return note[:200]


def from_issue(text: str) -> tuple[str, str]:
    """Đọc ISSUE_TITLE/ISSUE_BODY, cập nhật nhật ký. Trả về (text mới, thông báo)."""
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")

    m = ISSUE_MARK_RE.search(body)
    if m:
        action, date = m.group("action"), m.group("date")
    else:  # dự phòng khi marker bị xoá: đoán từ tiêu đề
        d = re.search(r"\d{4}-\d{2}-\d{2}", title)
        if not d:
            return text, ""
        date = d.group(0)
        action = "skip" if ("Bỏ qua" in title or "⏭" in title) else "read"

    rows = parse_rows(text)
    if date not in {r["date"] for r in rows}:
        return text, f"__NOTFOUND__Không tìm thấy báo cáo `{date}` trong nhật ký."

    note = clean_note(body)
    status = READ if action == "read" else SKIPPED
    for r in rows:
        if r["date"] == date:
            r["status"] = status
            r["read_on"] = dt.date.today().isoformat() if action == "read" else "—"
            if note:
                r["note"] = f"{r['note']} {note}".strip()

    text = replace_block(text, "table", render_rows(rows))
    pending = [r for r in parse_rows(text) if r["status"] not in (READ, SKIPPED)]
    slug = repo_slug()
    nxt = (
        f"👉 Đọc tiếp: [{pending[0]['date']}]"
        f"(https://github.com/{slug}/blob/main/trends/reports/{pending[0]['date']}.md)"
        f" — còn {len(pending)} báo cáo tồn đọng."
        if pending else "Hết báo cáo tồn đọng. 🎉"
    )
    return text, f"Đã ghi nhận: **{date} → {status}**." + (f" Ghi chú: _{note}_" if note else "") + f"\n\n{nxt}"


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
    sub.add_parser("footers", help="gắn link 'đã đọc' vào cuối mỗi báo cáo")
    sub.add_parser("from-issue", help="xử lý issue bấm từ GitHub (ISSUE_TITLE/ISSUE_BODY)")
    p_open = sub.add_parser("open", help="mở báo cáo tiếp theo và tự đánh dấu khi đọc xong")
    p_open.add_argument("date", nargs="?", default="next", help="YYYY-MM-DD, 'next' (mặc định) hoặc 'latest'")
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

    if cmd == "footers":
        touched = add_footers()
        print(f"Đã gắn footer cho {len(touched)} báo cáo: {', '.join(touched)}" if touched
              else "Mọi báo cáo đã có footer.")
    elif cmd == "from-issue":
        text, message = from_issue(text)
        updated = bool(message) and not message.startswith("__NOTFOUND__")
        message = message.replace("__NOTFOUND__", "")
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            # Dấu phân cách ngẫu nhiên: ghi chú do người dùng gõ không đoán được
            # nên không tự chèn thêm output khác được.
            delim = f"EOF_{secrets.token_hex(16)}"
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(f"updated={'true' if updated else 'false'}\n")
                fh.write(f"has_comment={'true' if message else 'false'}\n")
                fh.write(f"comment<<{delim}\n" + (message or "") + f"\n{delim}\n")
        print(message or "Issue không liên quan tới nhật ký — bỏ qua.")
    elif cmd == "open":
        text = open_report(text, args.date)
    elif cmd in STATUSES:
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
