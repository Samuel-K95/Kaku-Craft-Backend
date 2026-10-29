from django.core.management.base import BaseCommand

from cms.models import FAQEntry

DEFAULT_FAQS = [
	{
		"question": "How do payments work?",
		"answer": (
			"Orders require a 50% deposit before production starts. Upload a payment "
			"screenshot for admin verification. The remaining 50% is paid on delivery."
		),
		"keywords": "payment,deposit,50%,screenshot,proof,prepayment",
	},
	{
		"question": "How do custom crochet orders work?",
		"answer": (
			"Submit a reference image and description. An admin will review, quote a "
			"price, and chat with you. After you confirm the quote, pay the 50% deposit."
		),
		"keywords": "custom,commission,quote,reference image",
	},
	{
		"question": "What are delivery timelines?",
		"answer": (
			"Delivery timelines depend on item complexity and current queue. After your "
			"deposit is verified, the order moves to In Progress and you receive status updates."
		),
		"keywords": "delivery,timeline,shipping,when",
	},
	{
		"question": "How do I track my order status?",
		"answer": (
			"Sign in and open your orders list. Statuses include Pending Payment, "
			"Payment Submitted, Payment Verified, In Progress, Delivered, and Completed."
		),
		"keywords": "track,status,order history",
	},
]


class Command(BaseCommand):
	help = "Seed default FAQ entries for the RAG assistant"

	def handle(self, *args, **options):
		created = 0
		for item in DEFAULT_FAQS:
			obj, was_created = FAQEntry.objects.get_or_create(
				question=item["question"],
				defaults={
					"answer": item["answer"],
					"keywords": item["keywords"],
					"is_active": True,
				},
			)
			if was_created:
				created += 1
		self.stdout.write(self.style.SUCCESS(f"Seeded FAQs. Newly created: {created}"))
