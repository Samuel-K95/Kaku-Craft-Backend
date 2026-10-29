import pytest


@pytest.fixture(autouse=True)
def isolate_test_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
