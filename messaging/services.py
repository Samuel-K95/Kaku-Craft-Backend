from django.contrib.auth import get_user_model

from orders.models import CustomOrder, Order

from .models import Conversation, Message

User = get_user_model()


def ensure_conversation_for_order(order: Order) -> Conversation:
	conversation, _ = Conversation.objects.get_or_create(
		order=order,
		defaults={
			"customer": order.user,
			"subject": f"Order #{order.pk}",
		},
	)
	return conversation


def ensure_conversation_for_custom_order(custom_order: CustomOrder) -> Conversation:
	conversation, created = Conversation.objects.get_or_create(
		custom_order=custom_order,
		defaults={
			"customer": custom_order.customer,
			"subject": f"Custom order #{custom_order.pk}",
		},
	)
	if created:
		Message.objects.create(
			conversation=conversation,
			sender=custom_order.customer,
			body=(
				"New custom crochet request submitted.\n\n"
				f"{custom_order.description[:2000]}"
			),
		)
	return conversation
