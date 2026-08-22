# Domains

## What is this?

Moi thu muc con o day dai dien cho mot data domain - mot nhom du lieu thuoc ve mot team hoac line of business cu the. Day la noi data producers viet transform code, dinh nghia data quality rules, va cau hinh pipeline cua ho.

## What problem does it solve?

- **Ownership ro rang**: Moi domain co code rieng, team rieng chiu trach nhiem
- **Self-service**: Team moi tu onboard bang cach copy domain-template va chay onboard.py
- **Isolation**: Domain A khong the vo tinh anh huong den pipeline cua Domain B
- **Standardization**: Tat ca domains deu theo cung cau truc (stage_a, stage_b, data_quality, athena) nen de hieu va maintain

## How does it work?

Khi mot team muon dua du lieu len platform:

1. Chay `onboard.py` de tao domain moi tu template
2. Cau hinh `config.yaml` (schedule, worker size, governance rules)
3. Viet transform code trong `transforms/stage_a/` va `transforms/stage_b/`
4. Dinh nghia data quality rules
5. Commit + push --> CI/CD tu dong deploy code len S3 --> Glue job doc tu do

## Structure

```
domains/
├── domain-template/        # Template dung de tao domain moi
│   ├── config.yaml         # Template config (dien thong tin domain)
│   └── onboard.py          # Script tu dong tao domain
└── sample-domain/          # Domain mau de lam vi du
    ├── transforms/         # Code Glue jobs
    ├── data_quality/       # DQDL rules
    ├── athena/             # SQL views cho data consumers
    └── data/               # Sample data + generator
```
