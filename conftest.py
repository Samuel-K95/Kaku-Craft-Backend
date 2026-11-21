import pytest


@pytest.fixture(autouse=True)
def isolate_test_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    # Always use local filesystem storage during tests — never hit Cloudinary.
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
