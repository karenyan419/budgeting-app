from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import accounts, categories, transactions, reports, recurring_rules, exclusion_rules, admin

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Budgeting App API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(recurring_rules.router, prefix="/rules", tags=["rules"])
app.include_router(exclusion_rules.router, prefix="/exclusions", tags=["exclusions"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/")
def root():
    return {"message": "Budgeting App API", "docs": "/docs"}
