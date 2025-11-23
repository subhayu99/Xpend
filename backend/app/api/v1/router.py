from fastapi import APIRouter
from app.api.v1.endpoints import auth, accounts, transactions, categories, dashboard, transfers, budgets, analytics, settings

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(categories.router)
api_router.include_router(dashboard.router)
api_router.include_router(transfers.router)
api_router.include_router(budgets.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
