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
**Tiến độ:** 0/6 báo cáo đã xử lý.
**Đọc gần nhất:** chưa có.
**👉 Đọc tiếp:** [2026-07-29](reports/2026-07-29.md)
**Còn tồn:** 5 báo cáo — 2026-08-02, 2026-08-09, 2026-08-16, 2026-08-23, 2026-08-30
<!-- progress:end -->

## Bảng tiến độ

Trạng thái: `⬜ Chưa đọc` · `🔄 Đang đọc` · `✅ Đã đọc` · `⏭️ Bỏ qua`

<!-- table:start -->
| Báo cáo | Trạng thái | Ngày đọc | Ghi chú nhanh |
| --- | --- | --- | --- |
| [2026-07-29](reports/2026-07-29.md) | ⬜ Chưa đọc | — |  |
| [2026-08-02](reports/2026-08-02.md) | ⬜ Chưa đọc | — |  |
| [2026-08-09](reports/2026-08-09.md) | ⬜ Chưa đọc | — |  |
| [2026-08-16](reports/2026-08-16.md) | ⬜ Chưa đọc | — |  |
| [2026-08-23](reports/2026-08-23.md) | ⬜ Chưa đọc | — |  |
| [2026-08-30](reports/2026-08-30.md) | ⬜ Chưa đọc | — |  |
<!-- table:end -->

## Ghi chú từng báo cáo

Ba chủ đề của mỗi báo cáo được điền sẵn để bạn nhìn tiêu đề là nhớ ra nội dung.
Phần "Ghi chú của tôi" để trống cho bạn viết: điều đã áp dụng, điều còn nghi ngờ,
việc cần làm.

<!-- details:start -->

### 2026-07-29

1. "The new rules of context engineering" — Anthropic xoá ~80% system prompt của Claude Code cho dòng Claude 5
2. Agent memory stores lên beta mới (`agent-memory-2026-07-22`) và Dreams — decision-library thành hạ tầng có version
3. Dynamic workflows trong Claude Code — biến quy trình vận hành thành script chạy lại được

**Ghi chú của tôi:**
-


### 2026-08-02

1. MCP spec `2026-07-28` chính thức phát hành — giao thức chuyển sang stateless core + khung extension có version
2. `effort` trở thành nút điều khiển chi phí chính, và định tuyến effort/model theo từng subagent
3. Chuỗi cung ứng Agent Skills thành mặt tấn công có số liệu — SkillGate và hệ sinh thái quanh nó

**Ghi chú của tôi:**
-


### 2026-08-09

1. Cross-session messaging — các phiên Claude Code nhắn tin trực tiếp cho nhau (v2.1.224, 07/08/2026)
2. Sandbox credential masking — agent làm việc với secret mà không bao giờ nhìn thấy secret (v2.1.221 + v2.1.224)
3. Self-hosted environments — nơi agent chạy trở thành một quyết định triển khai (public beta, 06–07/08/2026)

**Ghi chú của tôi:**
-


### 2026-08-16

1. Auto mode thành mặc định trong Claude Code — Anthropic công bố số liệu nói người duyệt kém hơn classifier (14/08/2026)
2. Fork subagent thành mặc định — giao việc mà không phải kể lại bối cảnh (v2.1.232, 13/08/2026)
3. Agent Plugins 1.0 — chuẩn đóng gói đa nhà cung cấp cho skill + MCP, xây trên định dạng của Anthropic nhưng quản trị không có Anthropic (GA 12/08/2026)

**Ghi chú của tôi:**
-


### 2026-08-23

1. Agent Skills và Skills API ra GA (19/08/2026) — định dạng để đóng gói tri thức vận hành hết thời kỳ beta
2. Browser use tool ra mắt (19/08/2026) — agent đọc cấu trúc trang thay vì đoán từ ảnh chụp, và trình duyệt do *bạn* chạy
3. Python SDK lên v1.0 với breaking change thật (20/08), và Anthropic ship *lệnh agent tự migrate* ngay hôm sau (21/08)

**Ghi chú của tôi:**
-


### 2026-08-30

1. `--restricted`: tầng năng lực (capability tier) tách khỏi chính sách phê duyệt (permission mode)
2. Prompt cache TTL trở thành một field trong định nghĩa agent — và cache lần đầu đo được
3. Model switch trở thành sự kiện quản trị được — kèm một thay đổi ngữ nghĩa âm thầm ở `CLAUDE_CODE_SUBAGENT_MODEL`

**Ghi chú của tôi:**
-

<!-- details:end -->
