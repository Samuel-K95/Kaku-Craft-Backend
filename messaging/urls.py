from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
	path("conversations/", views.ConversationListCreateView.as_view(), name="conversation-list"),
	path(
		"conversations/<int:pk>/",
		views.ConversationDetailView.as_view(),
		name="conversation-detail",
	),
	path(
		"conversations/<int:pk>/messages/",
		views.ConversationMessagesView.as_view(),
		name="conversation-messages",
	),
	path(
		"conversations/<int:pk>/read/",
		views.ConversationMarkReadView.as_view(),
		name="conversation-read",
	),
	path(
		"conversations/<int:pk>/close/",
		views.ConversationCloseView.as_view(),
		name="conversation-close",
	),
]
