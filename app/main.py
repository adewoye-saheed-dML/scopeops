from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from app.database import Base, engine, get_db
from app.routers import suppliers, spend, emission_factors,auth
from sqlalchemy import text
from app.scripts.seed_categories import seed_categories
from app.scripts.seed_ditchcarbon_factors import  seed_ditchcarbon_factors
from app.scripts.seed_epa_factors import seed_epa_factors
from app.routers.auth import get_current_user, get_admin_user,User
import app.models
from fastapi.middleware.cors import CORSMiddleware

 

app = FastAPI(title="Procurement Carbon Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"       
        # "https://your-frontend-url.com" 
    ], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)



app.include_router(suppliers.router)
app.include_router(spend.router)
app.include_router(emission_factors.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.post("/admin/seed-database", tags=["Admin"])
def trigger_database_seed(admin_user: User = Depends(get_admin_user)):
    """
    Trigger this endpoint ONCE on the live server to populate the database.
    Strictly protected: Only users with is_admin=True can access this.
    """
    try:
        seed_categories()
        seed_ditchcarbon_factors()
        seed_epa_factors()
        
        return {"message": "Live database successfully seeded with Categories, DitchCarbon, and EPA Factors!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health/db")
def db_health_check(db = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok_fine"}
