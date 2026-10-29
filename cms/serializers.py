from rest_framework import serializers

from .models import FAQEntry, SiteContent


class SiteContentSerializer(serializers.ModelSerializer):
	class Meta:
		model = SiteContent
		fields = [
			"id",
			"key",
			"section",
			"title",
			"body",
			"data",
			"image",
			"is_published",
			"sort_order",
			"updated_at",
			"created_at",
		]
		read_only_fields = ["id", "updated_at", "created_at"]


class FAQEntrySerializer(serializers.ModelSerializer):
	class Meta:
		model = FAQEntry
		fields = ["id", "question", "answer", "keywords", "is_active", "updated_at"]
		read_only_fields = ["id", "updated_at"]


class RAGQuerySerializer(serializers.Serializer):
	question = serializers.CharField(max_length=500)
