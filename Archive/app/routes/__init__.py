from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.programs import router as programs_router
from app.routes.screenings import router as screenings_router

__all__ = ['auth_router', 'users_router', 'programs_router', 'screenings_router']