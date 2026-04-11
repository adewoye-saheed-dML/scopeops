import csv
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import engine
from app.models.category import Category

def seed_ceda_categories(csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        with Session(engine) as session:
            added = 0
            for row in reader:
                sector_code = str(row.get("Sector Code") or "").strip()
                sector_name = str(row.get("Sector Name") or "").strip()
                if not sector_code or not sector_name:
                    continue
                if not session.get(Category, sector_code):
                    session.add(Category(category_id=sector_code, category_name=sector_name))
                    added += 1
            session.commit()
            print(f"Added {added} CEDA categories.")

if __name__ == "__main__":
    default_csv = Path(__file__).resolve().parent.parent.parent / "data" / "Open CEDA 2025.xlsx - Metadata.csv"
    seed_ceda_categories(default_csv)