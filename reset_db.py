from app.database import engine, Base
from sqlalchemy import text

def reset_database():
    print("🗑️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))
        conn.commit()
        
    print("✨ Database is now a clean slate!")

if __name__ == "__main__":
    reset_database()