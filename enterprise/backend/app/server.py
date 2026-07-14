from .main import app
from .ai_routes import router as ai_router
from .authoring_routes import router as authoring_router
from .password_routes import router as password_router
from .admin_routes import projects_router as admin_projects_router
from .admin_routes import router as admin_router

app.include_router(ai_router)
app.include_router(authoring_router)
app.include_router(password_router)
app.include_router(admin_router)
app.include_router(admin_projects_router)
