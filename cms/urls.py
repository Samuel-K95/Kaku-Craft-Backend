from django.urls import path

from . import views

app_name = "cms"

urlpatterns = [
	path("content/", views.SiteContentListCreateView.as_view(), name="content-list"),
	path(
		"content/<slug:key>/",
		views.SiteContentDetailView.as_view(),
		name="content-detail",
	),
	path("faqs/", views.FAQListCreateView.as_view(), name="faq-list"),
	path("faqs/<int:pk>/", views.FAQDetailView.as_view(), name="faq-detail"),
	path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
	path("assistant/ask/", views.RAGAskView.as_view(), name="assistant-ask"),
]
