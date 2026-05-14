import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from auth import get_current_user
from routers import accounts, categories, transactions, reports, recurring_rules, exclusion_rules, admin
from routers import auth as auth_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budgeting App API", version="1.0.0")

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router (public - no auth required)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# Protected routers (require authentication)
protected = [Depends(get_current_user)]
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"], dependencies=protected)
app.include_router(categories.router, prefix="/categories", tags=["categories"], dependencies=protected)
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"], dependencies=protected)
app.include_router(reports.router, prefix="/reports", tags=["reports"], dependencies=protected)
app.include_router(recurring_rules.router, prefix="/rules", tags=["rules"], dependencies=protected)
app.include_router(exclusion_rules.router, prefix="/exclusions", tags=["exclusions"], dependencies=protected)
app.include_router(admin.router, prefix="/admin", tags=["admin"], dependencies=protected)


@app.get("/")
def root():
    return {"message": "Budgeting App API", "docs": "/docs"}
