import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoria_backend.settings')
django.setup()

from users.models import User

email = "test@example.com"
password = "testpass123"

if not User.objects.filter(email=email).exists():
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password
    )
    print(f"Test user created: {email} / {password}")
else:
    print(f"Test user already exists: {email}")
