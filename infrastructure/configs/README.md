# Environment Configs

## What is this?

YAML files chua cau hinh rieng cho moi environment (dev, staging, prod). Cung 1 CDK code nhung deploy khac nhau tuy moi truong.

## What problem does it solve?

- **Dev re hon**: Dev dung it workers (G.1X, 2 workers) --> chi phi thap khi test
- **Prod manh hon**: Prod dung nhieu workers (G.2X, 10 workers) --> xu ly data lon nhanh
- **Tach biet alert**: Dev alert gui cho dev team, Prod alert gui cho oncall
- **Mot code base**: Khong can maintain 3 ban code khac nhau cho 3 environments

## How does it work?

CDK doc `env` context variable, chon config tuong ung, truyen vao cac stacks.

```python
cdk deploy --context env=dev   # --> doc dev.yaml
cdk deploy --context env=prod  # --> doc prod.yaml
```

## Files

| File | Environment | Dac diem |
|------|-------------|----------|
| `dev.yaml` | Development | Workers nho, alert gui dev team |
| `prod.yaml` | Production | Workers lon, alert gui oncall team |
