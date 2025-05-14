import os
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

load_dotenv()

environment = os.getenv('ENVIRONMENT', 'development')

if environment == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_guestbook.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_guestbook.settings.dev')

application = get_wsgi_application()
