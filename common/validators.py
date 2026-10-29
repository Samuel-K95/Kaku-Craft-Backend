from django.core.exceptions import ValidationError


ALLOWED_IMAGE_CONTENT_TYPES = {
	"image/jpeg",
	"image/png",
	"image/webp",
}

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_upload(uploaded_file, *, max_bytes=MAX_UPLOAD_BYTES):
	if uploaded_file is None:
		return uploaded_file

	size = getattr(uploaded_file, "size", None)
	if size is not None and size > max_bytes:
		raise ValidationError(f"File too large. Max size is {max_bytes // (1024 * 1024)}MB.")

	content_type = getattr(uploaded_file, "content_type", None)
	name = getattr(uploaded_file, "name", "") or ""
	ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

	if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
		raise ValidationError("Unsupported image type. Use JPEG, PNG, or WebP.")

	if ext and ext not in {"jpg", "jpeg", "png", "webp"}:
		raise ValidationError("Unsupported image extension. Use .jpg, .jpeg, .png, or .webp.")

	return uploaded_file
