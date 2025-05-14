"""Settings package initializer."""
import os
from dotenv import load_dotenv

load_dotenv()

if os.getenv('ENVIRONMENT', 'development') == 'production':
    from .production import *
else:
    from .development import *