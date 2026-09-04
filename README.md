# learn-code-trends

Repo riêng để cloud routine hàng tuần (xem `learn-code` vault, mảnh "vòng lặp cập nhật kiến thức AI") ghi báo cáo xu hướng AI-agent mới nhất.

## Cấu trúc

`trends/reports/YYYY-MM-DD.md` — mỗi file là báo cáo 1 tuần: 3 thông tin quan trọng nhất, kèm phản biện độ chính xác/uy tín nguồn và đánh giá mức độ phù hợp với dự án.

## Quy trình

Không sửa tay các file trong `trends/reports/` — routine tự động ghi. Đưa nội dung vào `decision-library/` của vault Learn Code là bước thủ công, do người dùng tự quyết định khi đã áp dụng thật.

## Theo dõi tiến độ đọc

`trends/READING-LOG.md` ghi lại bạn đã đọc tới báo cáo nào, đọc ngày nào và
ghi chú gì. Không cần nhớ — mở file đó ra là thấy ngay dòng **👉 Đọc tiếp**.

```bash
./scripts/reading-log.py            # tiến độ + báo cáo cần đọc tiếp
./scripts/reading-log.py open       # mở báo cáo tiếp theo, đọc xong tự hỏi để đánh dấu
./scripts/reading-log.py next       # chỉ in đường dẫn báo cáo chưa đọc cũ nhất
./scripts/reading-log.py read next --note "đã áp dụng X"   # đọc xong thì đánh dấu
./scripts/reading-log.py reading 2026-08-16                # đọc dở, để dành
./scripts/reading-log.py skip 2026-08-02                   # bỏ qua tuần này
./scripts/reading-log.py sync       # nạp báo cáo mới (mọi lệnh trên đều tự chạy)
```

Báo cáo mới do routine ghi vào `trends/reports/` sẽ tự xuất hiện trong nhật ký
ở lần chạy script kế tiếp, kèm sẵn tiêu đề 3 chủ đề. Script chỉ thêm dòng mới và
đổi cột trạng thái — ghi chú bạn viết tay trong file không bị đụng tới.

Bạn không phải sửa bảng bằng tay. `open` là cách ít thao tác nhất: nó mở báo cáo
chưa đọc cũ nhất, đánh dấu "đang đọc" ngay lúc mở (nên có bỏ dở giữa chừng cũng
không mất dấu), đọc xong thoát ra thì hỏi một câu để chốt trạng thái và ghi chú.

### Đánh dấu ngay trên GitHub (không cần terminal)

Cuối mỗi báo cáo có hai link: **✅ Đánh dấu đã đọc** và **⏭️ Bỏ qua tuần này**.
Bấm vào là GitHub mở sẵn form issue (điền sẵn tiêu đề, ngày báo cáo và chỗ ghi
chú) — bạn chỉ cần bấm nút tạo issue. Workflow `.github/workflows/reading-log.yml`
sẽ cập nhật `trends/READING-LOG.md`, trả lời kèm link báo cáo tiếp theo, rồi tự
đóng issue. Làm được trên điện thoại.

Workflow đó cũng chạy khi routine đẩy báo cáo mới: nó nạp báo cáo vào nhật ký và
gắn sẵn hai link trên vào cuối file, nên không cần bảo trì gì thêm.

> Cần bật một lần: **Settings → Actions → General → Workflow permissions** chọn
> *Read and write permissions*, nếu không workflow sẽ không commit được nhật ký.
