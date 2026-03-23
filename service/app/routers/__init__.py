from app.routers.user import router as user_router
from app.routers.clothes import router as clothes_router
from app.routers.outfit import router as outfit_router
from app.routers.outfit_history import router as outfit_history_router

__all__ = ["user_router", "clothes_router", "outfit_router", "outfit_history_router"]