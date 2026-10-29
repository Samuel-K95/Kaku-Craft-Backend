from django.db import models


class SiteContent(models.Model):
	class Section(models.TextChoices):
		HOME_HERO = "home_hero", "Home Hero"
		HOME_ABOUT_TEASER = "home_about_teaser", "Home About Teaser"
		ABOUT = "about", "About"
		CONTACT = "contact", "Contact"
		BANNER = "banner", "Promotional Banner"
		FOOTER = "footer", "Footer"
		SOCIAL = "social", "Social Links"
		FAQ = "faq", "FAQ"

	key = models.SlugField(max_length=80, unique=True)
	section = models.CharField(max_length=40, choices=Section.choices)
	title = models.CharField(max_length=200, blank=True)
	body = models.TextField(blank=True)
	data = models.JSONField(default=dict, blank=True)
	image = models.ImageField(upload_to="cms/", blank=True, null=True)
	is_published = models.BooleanField(default=True)
	sort_order = models.PositiveIntegerField(default=0)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["section", "sort_order", "key"]

	def __str__(self):
		return f"{self.section}:{self.key}"


class FAQEntry(models.Model):
	question = models.CharField(max_length=300)
	answer = models.TextField()
	keywords = models.CharField(
		max_length=500,
		blank=True,
		help_text="Comma-separated keywords to improve retrieval.",
	)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["question"]
		verbose_name = "FAQ entry"
		verbose_name_plural = "FAQ entries"

	def __str__(self):
		return self.question
