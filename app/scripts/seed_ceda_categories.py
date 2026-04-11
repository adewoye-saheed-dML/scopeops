import openpyxl
import re
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import engine
from app.models.category import Category

def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()

def pick_header(headers: list, candidates: list) -> str:
    normalized_map = {normalize_header(h): h for h in headers if h}
    for candidate in candidates:
        candidate_norm = normalize_header(candidate)
        if candidate_norm in normalized_map:
            return normalized_map[candidate_norm]
    return ""

def seed_ceda_categories(xlsx_path: Path) -> None:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    
    # We now know the EXACT name of the sheet from your terminal output
    ws = wb["Metadata"]
    rows = ws.iter_rows(values_only=True)
    
    # Seek headers
    headers = []
    for row in rows:
        row_strs = [str(cell).strip() if cell is not None else "" for cell in row]
        row_lower = [c.lower() for c in row_strs]
        if any("sector code" in c or "sector name" in c for c in row_lower):
            headers = row_strs
            break
            
    print(f"📋 Detected Category Headers: {headers[:5]}...")

    code_col = pick_header(headers, ["Sector Code", "Sector", "Sector ID"])
    name_col = pick_header(headers, ["Sector Name", "Sector", "Industry", "Description"])

    with Session(engine) as session:
        added = 0
        for row in rows:
            row_dict = dict(zip(headers, row))
            sector_code = str(row_dict.get(code_col) or "").strip()
            sector_name = str(row_dict.get(name_col) or "").strip()

            if not sector_code or not sector_name:
                continue

            if not session.get(Category, sector_code):
                session.add(Category(category_id=sector_code, category_name=sector_name))
                added += 1
        
        session.commit()
        print(f"✅ Added {added} CEDA categories.")
    wb.close()

if __name__ == "__main__":
    default_xlsx = Path(__file__).resolve().parent.parent.parent / "data" / "Open CEDA 2025.xlsx"
    seed_ceda_categories(default_xlsx)