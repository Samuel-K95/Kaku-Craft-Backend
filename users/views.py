from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer # type: ignore


class RegisterView(generics.CreateAPIView):
	serializer_class = RegisterSerializer   
	permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_object(self):
		return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
	serializer_class = CustomTokenObtainPairSerializer
