# Lazy import to avoid database initialization during module imports
# The FastAPI app is only initialized when actually needed
def get_app():
    from app.main import app
    return app

__all__ = ["get_app"]

