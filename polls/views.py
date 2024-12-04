from datetime import timedelta
import random
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Category, Post
from .serializers import (
    RegisterSerializer,
    PostSerializer,
    CategorySerializer,
)
from .utils import send_otp

# Utility for success and error responses
def success(data, message="Success", status_code=status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data}, status=status_code)

def success_get(data):
    return success(data, "Data fetched successfully.")

def un_success(data, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"success": False, "errors": data}, status=status_code)


# Authentication and User Management Views
class UserRegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone']
        otp = random.randint(100000, 999999)
        cache.set(f"user_registration_{phone_number}", {
            **serializer.validated_data,
            "otp": otp,
            "otp_expiry": timezone.now() + timedelta(minutes=5),
        }, timeout=300)

        send_otp(phone_number, otp)

        return success({"message": "OTP sent to your phone.", "otp": otp, "otp_expires_in_seconds": 300})


class PhoneLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone')
        password = request.data.get('password')

        user = authenticate(request, phone=phone_number, password=password)
        if user is not None and user.is_active:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "message": "Login successful",
                "user": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": str(user.phone),
                    "is_active": user.is_active
                },
                "access_token": access_token
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid phone number or password."}, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return un_success({"error": "Phone number and OTP are required."})

        user_data = cache.get(f"user_registration_{phone}")
        if not user_data or user_data['otp'] != int(otp):
            return un_success({"error": "Invalid or expired OTP."})

        user = User.objects.create(
            phone=user_data['phone'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            is_active=True
        )
        user.set_password(user_data['password'])
        user.save()

        cache.delete(f"user_registration_{phone}")
        return success({"message": "User successfully registered and activated!"})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        user = get_object_or_404(User, phone=phone)

        otp = random.randint(100000, 999999)
        cache.set(f"password_reset_{phone}", {"otp": otp, "expiry": timezone.now() + timedelta(minutes=5)}, timeout=600)
        send_otp(phone, otp)

        return success({"message": "OTP sent to your phone.", "otp": otp,"otp_expires_in_minutes": 5})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone, otp, new_password = request.data.get('phone'), request.data.get('otp'), request.data.get('new_password')
        cache_data = cache.get(f"password_reset_{phone}")
        if not cache_data or cache_data['otp'] != int(otp):
            return un_success({"error": "Invalid or expired OTP."})

        user = get_object_or_404(User, phone=phone)
        user.set_password(new_password)
        user.save()
        cache.delete(f"password_reset_{phone}")
        return success({"message": "Password reset successful."})


# Category Views
@api_view(["GET", "POST", "PUT", "DELETE"])
def category_operations(request, pk=None):
    if request.method == "GET":
        if pk:
            category = get_object_or_404(Category, pk=pk)
            return success_get(CategorySerializer(category).data)
        return success_get(CategorySerializer(Category.objects.all(), many=True).data)

    if request.method == "POST":
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(serializer.data)

    if request.method == "PUT":
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(serializer.data)

    if request.method == "DELETE":
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        return success({"message": "Category deleted successfully."})


# Post Views
@api_view(["GET", "POST", "PUT", "DELETE"])
def post_operations(request, pk=None):
    if request.method == "GET":
        if pk:
            post = get_object_or_404(Post, pk=pk)
            return success_get(PostSerializer(post).data)
        return success_get(PostSerializer(Post.objects.all(), many=True).data)

    if request.method == "POST":
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(serializer.data)

    if request.method == "PUT":
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(serializer.data)

    if request.method == "DELETE":
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return success({"message": "Post deleted successfully."})
