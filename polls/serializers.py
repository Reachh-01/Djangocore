from rest_framework import serializers
from django.utils import timezone
from .models import User, Category, Post


# User Serializer for listing and basic user details
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'is_active']


# Registration Serializer for user creation
class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(min_length=3, max_length=100)
    last_name = serializers.CharField(min_length=3, max_length=100)
    phone = serializers.CharField(min_length=6, max_length=15)
    password = serializers.CharField(min_length=6, max_length=100)
    confirm_password = serializers.CharField(min_length=6, max_length=100)


    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError('Passwords must match')
        return data

    def create(self, validated_data):
        """
        Overriding create to handle custom user creation logic.
        """
        user = User(
            phone=validated_data['phone'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # Hash the password before saving
        user.set_password(validated_data['password'])
        user.save()
        return user


# OTP Verification Serializer
class OTPVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField()  # Accept phone number for verification
    otp = serializers.CharField(max_length=6)  # OTP must be 6 digits

    def validate(self, data):
        """
        Validate OTP and ensure it's correct and hasn't expired.
        """
        phone = data.get("phone")
        otp = data.get("otp")

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        # Check OTP correctness
        if user.otp != otp:
            user.otp_attempts += 1  # Increment OTP attempts
            user.save()

            # Optional: Lock the account after too many failed attempts
            if user.otp_attempts > user.max_otp_try:
                raise serializers.ValidationError("Maximum OTP attempts exceeded.")
            raise serializers.ValidationError("Invalid OTP.")

        # Check OTP expiry
        if timezone.now() > user.otp_expiry:
            raise serializers.ValidationError("OTP has expired.")

        return data

    def save(self, **kwargs):
        """
        Activate user and reset OTP fields upon successful validation.
        """
        phone = self.validated_data["phone"]
        user = User.objects.get(phone=phone)
        user.is_active = True  # Activate the user
        user.otp = None  # Clear the OTP
        user.otp_expiry = None  # Clear OTP expiry
        user.otp_attempts = 0  # Reset OTP attempts
        user.save()
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class ModelSerializer:
    pass