import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cms.models import FAQEntry, SiteContent

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email="cmsadmin@example.com",
		full_name="CMS Admin",
		password="StrongPass!234",
		role=User.Role.ADMIN,
	)


@pytest.mark.django_db
def test_public_cms_and_assistant(api_client, admin_user):
	SiteContent.objects.create(
		key="home-hero",
		section=SiteContent.Section.HOME_HERO,
		title="Kaku Craft",
		body="Handmade crochet",
		is_published=True,
	)
	FAQEntry.objects.create(
		question="How do payments work?",
		answer="Pay 50% deposit then upload a screenshot for verification.",
		keywords="payment,deposit,50%",
		is_active=True,
	)

	content = api_client.get(reverse("cms:content-list"))
	assert content.status_code == status.HTTP_200_OK
	assert len(content.data) == 1

	ask = api_client.post(
		reverse("cms:assistant-ask"),
		{"question": "Tell me about payment deposit"},
		format="json",
	)
	assert ask.status_code == status.HTTP_200_OK
	assert "50%" in ask.data["answer"]

	api_client.force_authenticate(user=admin_user)
	analytics = api_client.get(reverse("cms:analytics"), {"range": "monthly"})
	assert analytics.status_code == status.HTTP_200_OK
	assert "totals" in analytics.data
