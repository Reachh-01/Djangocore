from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class PhoneNumberAuthBackend(ModelBackend):
    def authenticate(self, request, phone=None, password=None, **kwargs):
        print(f"Phone: {phone}, Password: {password}")  # Print phone and password to check input

        # Ensure the phone number is provided
        if phone is None or password is None:
            return None

        phone_number = str(phone).strip()  # Ensure phone is treated as a string
        print(f"Normalized phone number: {phone_number}")  # Check the normalized phone number

        # Get the User model
        User = get_user_model()
        try:
            user = User.objects.get(phone=phone_number)
            print(f"User found: {user}")  # Print the user found
        except User.DoesNotExist:
            print("User does not exist.")
            return None  # Return None if no user is found

        # Check password
        if user.check_password(password):
            print("Password is correct.")
            return user  # Return the authenticated user
        else:
            print("Password is incorrect.")
            return None  # Return None if password is incorrect
