"""
API Routes Package
"""
from .questionnaire import router as questionnaire_router
from .responses import router as responses_router
from .admin import router as admin_router

__all__ = ["questionnaire_router", "responses_router", "admin_router"]
