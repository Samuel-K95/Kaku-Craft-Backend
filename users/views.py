from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import (  # type: ignore
	ChangePasswordSerializer,
	CustomTokenObtainPairSerializer,
	ProfileUpdateSerializer,
	RegisterSerializer,
	UserSerializer,
)


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
