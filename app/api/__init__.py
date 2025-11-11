"""
API Routes Package
"""
from .questionnaire import router as questionnaire_router
from .responses import router as responses_router
from .admin import router as admin_router
from .vendors import router as vendors_router
from .risk_management import router as risk_router

__all__ = ["questionnaire_router", "responses_router", "admin_router", "vendors_router", "risk_router"]
