import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoria_backend.settings')
django.setup()

from users.models import User

email = "test@example.com"
user = User.objects.get(email=email)
print(f"Reset token: {user.reset_token}")
