# Domain Template

## What is this?

Template va script tu dong de onboard mot data domain moi len platform. Thay vi phai setup thu cong (tao folders, viet boilerplate code, cau hinh permissions), team chi can chay 1 lenh.

## What problem does it solve?

- **Giam thoi gian onboard**: Tu 1-2 tuan (neu setup thu cong) xuong con 5 phut
- **Dam bao consistency**: Tat ca domain deu co cung cau truc, de cho platform team support
- **Khong quen buoc nao**: Template bao gom san data quality, governance config, transform boilerplate
- **Self-service**: Team tu lam duoc, khong can dat ticket cho platform team

## How does it work?

```bash
python onboard.py --domain sales --owner sales-team@company.com --dataset transactions
```

Script se:
1. Tao folder structure: transforms/, data_quality/, athena/, data/
2. Generate config.yaml voi thong tin domain
3. Tao stage_a transform boilerplate (san sang chay)
4. In ra next steps de team biet can lam gi tiep

## Files

| File | Chuc nang |
|------|-----------|
| `config.yaml` | Template config - mo ta tat ca options co the cau hinh |
| `onboard.py` | Script chinh - nhan arguments va tao domain folder |
