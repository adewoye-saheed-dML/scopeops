import csv
import re
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import engine
from app.models.emission_factors import EmissionFactor
from app.models.user import User

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
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None

def format_external_id(sector_code: str, sector_name: str) -> str:
    slug = sector_code if sector_code else re.sub(r"[^A-Za-z0-9]+", "_", sector_name).strip("_").upper()
    return f"OPEN-CEDA-2025-{slug}"

def seed_ceda_factors(raw_csv_path: Path, conversion_csv_path: Path) -> None:
    # 1. Load Conversions (These are generally global/sector-based)
    conversions = {}
    with conversion_csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = str(row.get("Sector Code") or "").strip()
            mult = parse_decimal(row.get("Purchaser - producer conversion"))
            if code and mult:
                conversions[code] = mult

    # 2. Process Raw Factors for ALL Countries
    with raw_csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        with Session(engine) as session:
            sys_user_id = get_system_user(session)
            added = 0
            
            for row in reader:
                # Capture the actual Country/Geography from the CSV
                country = str(row.get("Country") or row.get("Geography") or "Global").strip()
                
                code = str(row.get("Sector Code") or "").strip()
                name = str(row.get("Sector Name") or "").strip()
                base_ef = parse_decimal(row.get("GHG_t_Raw"))
                
                multiplier = conversions.get(code)
                if not base_ef or not multiplier:
                    continue

                final_ef = base_ef * multiplier
                ext_id = format_external_id(code, name)

                # Check for existing factor by ID AND specific Geography
                exists = session.query(EmissionFactor).filter_by(
                    external_id=ext_id, 
                    geography=country
                ).first()

                if not exists:
                    session.add(EmissionFactor(
                        external_id=ext_id, 
                        provider=PROVIDER, 
                        name=f"{name} ({code})",
                        geography=country, # Now saves the actual country (e.g., Germany, China, etc.)
                        year=YEAR, 
                        unit_of_measure=UNIT_OF_MEASURE,
                        co2e_per_unit=final_ef, 
                        scope_3_intensity=final_ef,
                        owner_id=sys_user_id, 
                        version=VERSION,
                        methodology=f"Open CEDA 2025 Global Factors - {country}"
                    ))
                    added += 1
                    
                    # Commit in batches of 500 to handle the large global dataset
                    if added % 500 == 0:
                        session.commit()
            
            session.commit()
            print(f"Seeded {added} Global Open CEDA factors.")

if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    raw = data_dir / "Open CEDA 2025.xlsx - GHG_t_Raw.csv"
    conv = data_dir / "Open CEDA 2025.xlsx - Purchaser - producer conversion.csv"
    seed_ceda_factors(raw, conv)