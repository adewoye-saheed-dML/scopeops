from fastapi import FastAPI, Depends
from app.database import Base, engine, get_db
from app.routers import suppliers, spend
from sqlalchemy import text
import app.models

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Procurement Carbon Engine")

app.include_router(suppliers.router)
app.include_router(spend.router)


@app.get("/health/db")
def db_health_check(db = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok_fine"}
