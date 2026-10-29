from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.permissions import IsAdminOrSuperAdmin

from .analytics import build_analytics
from .models import FAQEntry, SiteContent
from .rag import answer_question
from .serializers import FAQEntrySerializer, RAGQuerySerializer, SiteContentSerializer


class SiteContentListCreateView(generics.ListCreateAPIView):
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	serializer_class = SiteContentSerializer

	def get_permissions(self):
		if self.request.method == "GET":
			return [AllowAny()]
		return [IsAdminOrSuperAdmin()]

	def get_queryset(self):
		qs = SiteContent.objects.all()
		section = self.request.query_params.get("section")
		if section:
			qs = qs.filter(section=section)
		if self.request.method == "GET" and getattr(
			self.request.user, "role", None
		) not in {"admin", "super_admin"}:
			qs = qs.filter(is_published=True)
		return qs


class SiteContentDetailView(generics.RetrieveUpdateDestroyAPIView):
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	serializer_class = SiteContentSerializer
	lookup_field = "key"

	def get_permissions(self):
		if self.request.method == "GET":
			return [AllowAny()]
		return [IsAdminOrSuperAdmin()]

	def get_queryset(self):
		qs = SiteContent.objects.all()
		if self.request.method == "GET" and getattr(
			self.request.user, "role", None
		) not in {"admin", "super_admin"}:
			qs = qs.filter(is_published=True)
		return qs


class FAQListCreateView(generics.ListCreateAPIView):
	serializer_class = FAQEntrySerializer

	def get_permissions(self):
		if self.request.method == "GET":
			return [AllowAny()]
		return [IsAdminOrSuperAdmin()]

	def get_queryset(self):
		qs = FAQEntry.objects.all()
		if self.request.method == "GET" and getattr(
			self.request.user, "role", None
		) not in {"admin", "super_admin"}:
			qs = qs.filter(is_active=True)
		return qs


class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = FAQEntrySerializer
	queryset = FAQEntry.objects.all()
	permission_classes = [IsAdminOrSuperAdmin]


class AnalyticsView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def get(self, request):
		return Response(build_analytics(request.query_params))


class RAGAskView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = RAGQuerySerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		result = answer_question(serializer.validated_data["question"])
		return Response(result, status=status.HTTP_200_OK)
