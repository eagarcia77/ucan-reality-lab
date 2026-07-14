from .main import app
from .ai_routes import router as ai_router

app.include_router(ai_router)
