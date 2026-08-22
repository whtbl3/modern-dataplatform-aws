# Domain Template

## Đây là gì?

Template và script tự động để onboard một data domain mới lên platform. Thay vì phải setup thủ công (tạo folders, viết boilerplate code, cấu hình permissions), team chỉ cần chạy 1 lệnh.

## Giải quyết vấn đề gì?

- **Giảm thời gian onboard**: Từ 1-2 tuần (nếu setup thủ công) xuống còn 5 phút
- **Đảm bảo consistency**: Tất cả domain đều có cùng cấu trúc, dễ cho platform team support
- **Không quên bước nào**: Template bao gồm sẵn data quality, governance config, transform boilerplate
- **Self-service**: Team tự làm được, không cần đặt ticket cho platform team

## Hoạt động như thế nào?

```bash
python onboard.py --domain sales --owner sales-team@company.com --dataset transactions
```

Script sẽ:
1. Tạo folder structure: transforms/, data_quality/, athena/, data/
2. Generate config.yaml với thông tin domain
3. Tạo stage_a transform boilerplate (sẵn sàng chạy)
4. In ra next steps để team biết cần làm gì tiếp

## Files

| File | Chức năng |
|------|-----------|
| `config.yaml` | Template config - mô tả tất cả options có thể cấu hình |
| `onboard.py` | Script chính - nhận arguments và tạo domain folder |
