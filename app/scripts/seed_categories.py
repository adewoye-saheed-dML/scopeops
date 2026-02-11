from sqlalchemy.orm import Session
from app.database import engine
from app.models.category import Category

CATEGORIES = [
    {"category_id": "DIRECT_MAT", "category_name": "Direct Materials"},
    {"category_id": "INDIRECT_MAT", "category_name": "Indirect Materials"},
    {"category_id": "LOGISTICS", "category_name": "Logistics"},
    {"category_id": "PRO_SERV", "category_name": "Professional Services"},
    {"category_id": "IT_SERV", "category_name": "IT Services"},
    {"category_id": "FAC_MGMT", "category_name": "Facilities Management"},
    {"category_id": "CAP_GOODS", "category_name": "Capital Goods"},
]

def seed_categories():
    with Session(engine) as session:
        for cat in CATEGORIES:
            exists = session.get(Category, cat["category_id"])
            if not exists:
                session.add(Category(**cat))
        session.commit()

if __name__ == "__main__":
    seed_categories()
    print("Categories seeded successfully")
