# Infrastructure

## What is this?

Thu muc chua toan bo Infrastructure as Code (IaC) cua data platform. Moi thanh phan AWS (S3, Glue, Lambda, Step Functions, ...) deu duoc dinh nghia bang code o day, khong co gi duoc tao thu cong qua AWS Console.

## What problem does it solve?

- **Reproducibility**: Deploy cung mot platform vao dev/staging/prod chi bang 1 lenh, dam bao cac moi truong giong nhau
- **Version control**: Moi thay doi infrastructure deu duoc track trong git, co the rollback bat cu luc nao
- **Review process**: Thay doi phai qua code review truoc khi deploy, tranh loi do 1 nguoi tu y sua
- **Self-documenting**: Doc code la biet platform gom nhung gi, khong can doc tai lieu rieng

## How does it work?

Su dung AWS CDK (Python) de dinh nghia resources. CDK compile Python code thanh CloudFormation templates, roi CloudFormation deploy len AWS.

```
Python CDK Code --> CloudFormation Templates --> AWS Resources
(developer viet)    (CDK tu generate)           (CloudFormation deploy)
```

## Structure

```
infrastructure/
├── cdk/
│   ├── app.py              # Entry point - khoi tao tat ca stacks
│   ├── cdk.json            # CDK config
│   ├── lambda/             # Lambda function code (deploy cung CDK)
│   └── stacks/             # Moi stack = 1 nhom resources lien quan
└── configs/
    ├── dev.yaml            # Config rieng cho dev environment
    └── prod.yaml           # Config rieng cho prod environment
```
