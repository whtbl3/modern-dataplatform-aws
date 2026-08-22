"""Unit tests for domain onboarding script."""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "domains" / "domain-template"))
from onboard import onboard_domain


@pytest.fixture
def temp_domains_dir(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    template_dir = tmp / "domain-template"
    template_dir.mkdir()
    monkeypatch.setattr("onboard.Path", lambda *a: template_dir if not a else Path(*a))

    import onboard
    original_parent = Path(onboard.__file__).parent
    monkeypatch.setattr(onboard, "__file__", str(template_dir / "onboard.py"))
    yield tmp
    shutil.rmtree(tmp)


def test_onboard_creates_directory(temp_domains_dir):
    domain_dir = temp_domains_dir / "test-domain"
    assert not domain_dir.exists()

    import onboard
    onboard.__file__ = str(temp_domains_dir / "domain-template" / "onboard.py")
    result = onboard_domain("test-domain", "test@co.com", "events")

    assert result is True
    assert domain_dir.exists()
    assert (domain_dir / "config.yaml").exists()
    assert (domain_dir / "transforms" / "stage_a" / "main.py").exists()


def test_onboard_rejects_existing_domain(temp_domains_dir):
    import onboard
    onboard.__file__ = str(temp_domains_dir / "domain-template" / "onboard.py")

    onboard_domain("existing", "test@co.com", "data")
    result = onboard_domain("existing", "test@co.com", "data")

    assert result is False


def test_onboard_config_content(temp_domains_dir):
    import yaml
    import onboard
    onboard.__file__ = str(temp_domains_dir / "domain-template" / "onboard.py")

    onboard_domain("sales", "sales@co.com", "transactions", "Sales data domain")

    config_path = temp_domains_dir / "sales" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert config["domain"]["name"] == "sales"
    assert config["domain"]["owner"] == "sales@co.com"
    assert config["datasets"][0]["name"] == "transactions"
    assert config["data_quality"]["enabled"] is True
    assert config["governance"]["classification"] == "internal"
