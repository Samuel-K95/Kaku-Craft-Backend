from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "profile_picture", "date_joined"]
        read_only_fields = ["id", "role", "date_joined"]


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "profile_picture",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "full_name", "profile_picture", "date_joined"]

    def validate_role(self, value):
        request = self.context.get("request")
        if not request:
            return value
        # Prevent demoting yourself out of admin access.
        if self.instance and self.instance.pk == request.user.pk:
            if value not in {
                User.Role.ADMIN,
                User.Role.SUPER_ADMIN,
                User.Role.SYSTEM_ADMIN,
            }:
                raise serializers.ValidationError("You cannot remove your own admin access.")
        return value

    def update(self, instance, validated_data):
        role = validated_data.get("role", instance.role)
        if role in {User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.SYSTEM_ADMIN}:
            instance.is_staff = True
        elif role == User.Role.EXPERT:
            instance.is_staff = False
        else:
            instance.is_staff = False
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False, default=User.Role.CUSTOMER)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "password", "role"]
        read_only_fields = ["id"]

    def validate_role(self, value):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            if value != User.Role.CUSTOMER:
                raise serializers.ValidationError("Only customer signup is allowed.")
            return value

        if request.user.role == User.Role.SUPER_ADMIN:
            return value

        if request.user.role == User.Role.ADMIN and value == User.Role.CUSTOMER:
            return value

        raise serializers.ValidationError("You do not have permission to create this role.")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "full_name", "profile_picture"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
