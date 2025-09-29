from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'username']