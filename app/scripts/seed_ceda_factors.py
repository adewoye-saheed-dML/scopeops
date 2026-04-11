import re
import uuid
import openpyxl
from decimal import Decimal, InvalidOperation
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import engine
from app.models.emission_factors import EmissionFactor
from app.models.user import User
from app.models.category import Category

PROVIDER = "Open CEDA"
UNIT_OF_MEASURE = "USD"
YEAR = 2023
VERSION = "2025-11-12"

def get_system_user(session: Session) -> uuid.UUID:
    sys_email = "system_epa@scopeops.local"
    sys_user = session.query(User).filter(User.email == sys_email).first()
    if not sys_user:
        sys_user = User(email=sys_email, full_name="EPA System Administrator", provider="system", is_active=True)
        session.add(sys_user)
        session.commit()
        session.refresh(sys_user)
    return sys_user.id

def parse_decimal(value: object) -> Decimal | None:
    if value is None: return None
    text = str(value).strip()
    if not text or text.lower() in {"na", "n/a", "nan", "null"}: return None
    cleaned = text.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"): cleaned = f"-{cleaned[1:-1]}"
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None

def format_external_id(sector_code: str) -> str:
    slug = sector_code.strip().upper()
    return f"OPEN-CEDA-2025-{slug}"

def seed_ceda_factors(xlsx_path: Path) -> None:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    
    # ----------------------------------------------------
    # 1. Load Conversions (Horizontal Matrix)
    # ----------------------------------------------------
    sheet_conv = next((s for s in wb.sheetnames if "conversion" in s.lower()), None)
    ws_conv = wb[sheet_conv]
    
    code_row = []
    mult_row = []
    
    for row in ws_conv.iter_rows(values_only=True):
        row_strs = [str(c).strip() if c is not None else "" for c in row]
        row_lower = [x.lower() for x in row_strs]
        
        # '1111a0' is the first sector code. This is a foolproof way to find the header row!
        if "1111a0" in row_lower:
            code_row = row_strs
        elif any("purchaser" in x and "producer" in x for x in row_lower):
            mult_row = row_strs
            
        if code_row and mult_row:
            break
            
    conversions = {}
    for code, mult_val in zip(code_row, mult_row):
        code_str = code.strip()
        # Skip the label columns
        if not code_str or code_str.lower() in ["sector name", "sector code", "purchaser - producer conversion", "source"]:
            continue
            
        mult = parse_decimal(mult_val)
        if mult:
            conversions[code_str] = mult

    print(f"🔢 Extracted {len(conversions)} conversion multipliers horizontally.")

    # ----------------------------------------------------
    # 2. Process Raw Factors (Horizontal Matrix)
    # ----------------------------------------------------
    sheet_raw = next((s for s in wb.sheetnames if "raw" in s.lower()), None)
    ws_raw = wb[sheet_raw]
    
    codes_row = []
    data_rows = []
    found_headers = False
    
    for row in ws_raw.iter_rows(values_only=True):
        row_strs = [str(c).strip() if c is not None else "" for c in row]
        row_lower = [x.lower() for x in row_strs]
        
        if not found_headers:
            if "1111a0" in row_lower:
                codes_row = row_strs
                found_headers = True
        else:
            if any(row_strs): # Ensure row isn't completely blank
                data_rows.append(row_strs)
                
    print(f"📋 Detected {len(data_rows)} Country Rows to process.")

    with Session(engine) as session:
        sys_user_id = get_system_user(session)
        # Fetch categories to give the factors nice names
        category_map = {c.category_id: c.category_name for c in session.query(Category).all()}
        added = 0
        
        # Iterate over each Country (Row)
        for row in data_rows:
            country_name = str(row[1]).strip() # The 2nd column is the Country Name
            
            if not country_name or country_name.lower() in ["country", "geography", ""]:
                continue
                
            # Iterate over every Sector Code (Column)
            for col_idx in range(len(row)):
                if col_idx >= len(codes_row):
                    continue
                    
                code = codes_row[col_idx].strip()
                
                # Skip the label columns on the far left (Country, Country Code, etc.)
                if not code or code.lower() in ["country code", "country", "country ", "geography"]:
                    continue
                    
                base_ef = parse_decimal(row[col_idx])
                multiplier = conversions.get(code)
                
                if not base_ef or not multiplier:
                    continue

                final_ef = base_ef * multiplier
                ext_id = format_external_id(code)

                # Check if it exists
                exists = session.query(EmissionFactor).filter_by(
                    external_id=ext_id, geography=country_name
                ).first()

                if not exists:
                    sector_name = category_map.get(code, f"Sector {code}")
                    
                    session.add(EmissionFactor(
                        external_id=ext_id, provider=PROVIDER, name=f"{sector_name} ({code})",
                        geography=country_name, year=YEAR, unit_of_measure=UNIT_OF_MEASURE,
                        co2e_per_unit=final_ef, scope_3_intensity=final_ef,
                        owner_id=sys_user_id, version=VERSION,
                        methodology=f"Open CEDA 2025 Global Factors - {country_name}"
                    ))
                    added += 1
                    
                    if added % 2000 == 0:
                        session.commit()
                        print(f"   ...committing batch ({added} factors loaded)...")
        
        session.commit()
        print(f"✅ Successfully seeded {added} Global Open CEDA factors!")
        
    wb.close()

if __name__ == "__main__":
    default_xlsx = Path(__file__).resolve().parent.parent.parent / "data" / "Open CEDA 2025.xlsx"
    seed_ceda_factors(default_xlsx)