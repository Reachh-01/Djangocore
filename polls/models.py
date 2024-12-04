from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import MinLengthValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


# Custom User Manager
class UserManager(BaseUserManager):
    """
    Custom manager for User model with support for phone-based authentication.
    """

    def create_user(self, phone, password=None, **extra_fields):
        """
        Create and return a regular user with the given phone and password.
        """
        if not phone:
            raise ValueError(_("The Phone Number field must be set"))
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Create and return a superuser with the given phone and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(phone, password, **extra_fields)


# Custom User Model
class User(AbstractBaseUser):
    """
    Custom user model that supports authentication via phone number.
    """
    phone = PhoneNumberField(unique=True, verbose_name=_("Phone Number"))
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    max_otp_try = models.IntegerField(default=3)
    otp_attempts = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"User {self.phone}"


# Category Model
class Category(models.Model):
    """
    Represents categories for posts.
    """
    name = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    description = models.CharField(max_length=255, default="No description provided")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.name


# Post Model
class Post(models.Model):
    """
    Represents a post created by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    categories = models.ManyToManyField(
        Category,
        related_name='posts',
        blank=True,
        help_text=_("Categories associated with the post")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post'
        constraints = [
            models.UniqueConstraint(fields=['user', 'title'], name='unique_user_title'),
        ]
        indexes = [
            models.Index(fields=['user', 'title']),
        ]

    def __str__(self):
        return f"Post '{self.title}' by {self.user.phone}"
