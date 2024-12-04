from django.urls import path
from .views import (
    UserRegisterView,
    PhoneLoginView,
    OTPVerificationView,
    ForgotPasswordView,
    ResetPasswordView,
    category_operations,
    post_operations,
)

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", PhoneLoginView.as_view(), name="login"),
    path("verify-otp/", OTPVerificationView.as_view(), name="verify_otp"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("categories/", category_operations, name="category_list_create"),
    path("categories/<int:pk>/", category_operations, name="category_detail_update_delete"),
    path("posts/", post_operations, name="post_list_create"),
    path("posts/<int:pk>/", post_operations, name="post_detail_update_delete"),
]
