"""
Modern Data Platform on AWS - Project entry point.

File nay cung cap huong dan nhanh cho developer moi.
Platform thuc su duoc deploy qua CDK (infrastructure/cdk/app.py),
khong phai qua file nay.
"""


def main():
    """In huong dan su dung co ban cua project."""
    print("Modern Data Platform on AWS")
    print("=" * 40)
    print()
    print("Commands:")
    print("  uv run pytest tests/unit/ -v                    # Run tests")
    print("  uv run python domains/sample-domain/data/generate_sample.py  # Generate data")
    print("  cdk synth --context env=dev --app '...'         # Validate stacks")
    print("  cdk deploy --all --context env=dev              # Deploy to AWS")
    print()
    print("Onboard new domain:")
    print("  uv run python domains/domain-template/onboard.py --domain <name> --owner <email> --dataset <name>")


if __name__ == "__main__":
    main()
