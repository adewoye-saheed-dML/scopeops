from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from app.database import Base, engine, get_db
from app.routers import suppliers, spend, emission_factors, auth
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Procurement Carbon Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       
        "https://scopeopsfe-adewoyesaheed1845-nzqvbt9r.leapcell.dev" 
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

@app.get("/health/db", tags=["Health"])
def db_health_check(db = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok_fine"}
