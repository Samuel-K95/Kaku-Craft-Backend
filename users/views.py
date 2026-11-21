from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import (  # type: ignore
	ChangePasswordSerializer,
	CustomTokenObtainPairSerializer,
	ProfileUpdateSerializer,
	RegisterSerializer,
	UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
	serializer_class = RegisterSerializer   
	permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_object(self):
		return self.request.user


class ProfileUpdateView(generics.UpdateAPIView):
	serializer_class = ProfileUpdateSerializer
	permission_classes = [permissions.IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser]

	def get_object(self):
		return self.request.user


class ChangePasswordView(generics.GenericAPIView):
	serializer_class = ChangePasswordSerializer
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
	serializer_class = CustomTokenObtainPairSerializer


class ImpersonateView(APIView):
	"""
	POST /api/users/impersonate/
	Body: { "target_email": "someone@example.com" }

	Only accessible by users with can_impersonate=True (system_admin).
	Returns a fresh JWT pair for the target user so the caller can
	sign into the frontend as that user without knowing their password.
	"""

	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, *args, **kwargs):
		if not getattr(request.user, "can_impersonate", False):
			return Response(
				{"detail": "You do not have permission to impersonate users."},
				status=status.HTTP_403_FORBIDDEN,
			)

		target_email = request.data.get("target_email", "").strip()
		if not target_email:
			return Response({"detail": "target_email is required."}, status=status.HTTP_400_BAD_REQUEST)

		try:
			target = User.objects.get(email=target_email, is_active=True)
		except User.DoesNotExist:
			return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

		refresh = RefreshToken.for_user(target)
		# Embed role into access token (mirrors CustomTokenObtainPairSerializer)
		refresh.access_token["role"] = target.role

		return Response(
			{
				"impersonating": UserSerializer(target).data,
				"refresh": str(refresh),
				"access": str(refresh.access_token),
			},
			status=status.HTTP_200_OK,
		)

