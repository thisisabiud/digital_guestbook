"""
WSGI config for project_name project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the 'wsgi' application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_guestbook.settings')

# This is the WSGI application object that servers will use
application = get_wsgi_application()