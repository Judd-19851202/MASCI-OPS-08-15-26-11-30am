from pathlib import Path


def test_preview_banner_strings_are_non_production_safe():
    env_banner = Path("/app/frontend/src/components/EnvBanner.jsx").read_text(encoding="utf-8")
    leadership = Path("/app/frontend/src/pages/LeadershipHubV2.jsx").read_text(encoding="utf-8")

    assert "PREVIEW ENVIRONMENT" not in env_banner
    assert "Cross-portal executive attention · Companion lane" not in leadership
    assert "NON-PRODUCTION ENVIRONMENT" in env_banner
    assert "Non-production companion lane" in leadership