# Vercel entrypoint for Python Serverless Functions
# Vercel will detect `app` as the ASGI application.
from api.app import app  # noqa: F401
