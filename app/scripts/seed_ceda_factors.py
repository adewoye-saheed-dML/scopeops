import csv
import re
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import engine
from app.models.emission_factors import EmissionFactor
from app.models.user import User


RAW_FILENAME = "Open CEDA 2025 (updated 2025-11-12) - GHG_t_Raw.csv"
CONVERSION_FILENAME = (
    "Open CEDA 2025 (updated 2025-11-12) - Purchaser - producer conversion.csv"
)

PROVIDER = "Open CEDA"
GEOGRAPHY = "US"
UNIT_OF_MEASURE = "USD"
YEAR = 2023
VERSION = "2025-11-12"

US_ALIASES = {
    "us",
    "usa",
    "united states",
    "united states of america",
}


def get_system_user(session: Session) -> uuid.UUID:
    sys_email = "system_epa@scopeops.local"
    sys_user = session.query(User).filter(User.email == sys_email).first()
    if not sys_user:
        sys_user = User(
            email=sys_email,
            full_name="EPA System Administrator",
            provider="system",
            is_active=True,
        )
        session.add(sys_user)
        session.commit()
        session.refresh(sys_user)
    return sys_user.id


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def pick_header(headers: list[str], candidates: list[str]) -> str | None:
    normalized_map = {normalize_header(h): h for h in headers if h}

    for candidate in candidates:
        candidate_norm = normalize_header(candidate)
        if candidate_norm in normalized_map:
            return normalized_map[candidate_norm]

    for candidate in candidates:
        candidate_norm = normalize_header(candidate)
        for header_norm, header in normalized_map.items():
            if candidate_norm and candidate_norm in header_norm:
                return header

    return None


def parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"na", "n/a", "nan", "null"}:
        return None
    cleaned = text.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def read_raw_factors(csv_path: Path) -> list[dict[str, str | Decimal]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []

        headers = reader.fieldnames
        sector_code_col = pick_header(headers, ["Sector Code", "Sector", "Sector ID"])
        sector_name_col = pick_header(headers, ["Sector Name", "Sector", "Industry"])
        geography_col = pick_header(headers, ["Country", "Geography", "Region"])
        factor_col = pick_header(
            headers,
            [
                "GHG_t_Raw",
                "GHG t Raw",
                "GHG_t_Raw_2023_USD",
                "GHG_t_Raw_2023 USD",
                "GHG_t_Raw (2023 USD)",
                "GHG_t_Raw 2023 USD",
                "Emission Factor",
            ],
        )

        if not factor_col:
            raise ValueError(
                f"Could not find a GHG_t_Raw column in {csv_path.name}. "
                f"Columns found: {headers}"
            )

        rows: list[dict[str, str | Decimal]] = []
        for row in reader:
            if geography_col:
                geography_val = str(row.get(geography_col) or "").strip().lower()
                if geography_val and geography_val not in US_ALIASES:
                    continue

            sector_code = str(row.get(sector_code_col) or "").strip()
            sector_name = str(row.get(sector_name_col) or "").strip()
            factor = parse_decimal(row.get(factor_col))

            if not sector_code and not sector_name:
                continue
            if factor is None:
                continue

            rows.append(
                {
                    "sector_code": sector_code,
                    "sector_name": sector_name,
                    "factor": factor,
                }
            )

    return rows


def read_conversion_factors(csv_path: Path) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return {}, {}

        headers = reader.fieldnames
        sector_code_col = pick_header(headers, ["Sector Code", "Sector", "Sector ID"])
        sector_name_col = pick_header(headers, ["Sector Name", "Sector", "Industry"])
        geography_col = pick_header(headers, ["Country", "Geography", "Region"])
        multiplier_col = pick_header(
            headers,
            [
                "Purchaser - producer conversion",
                "Purchaser-producer conversion",
                "Purchaser producer conversion",
                "Purchaser producer",
                "Conversion",
                "Multiplier",
            ],
        )

        if not multiplier_col:
            raise ValueError(
                f"Could not find a conversion multiplier column in {csv_path.name}. "
                f"Columns found: {headers}"
            )

        by_code: dict[str, Decimal] = {}
        by_name: dict[str, Decimal] = {}
        for row in reader:
            if geography_col:
                geography_val = str(row.get(geography_col) or "").strip().lower()
                if geography_val and geography_val not in US_ALIASES:
                    continue

            sector_code = str(row.get(sector_code_col) or "").strip()
            sector_name = str(row.get(sector_name_col) or "").strip()
            multiplier = parse_decimal(row.get(multiplier_col))

            if multiplier is None:
                continue

            if sector_code:
                by_code[sector_code] = multiplier
            if sector_name:
                by_name[sector_name] = multiplier

    return by_code, by_name


def format_external_id(sector_code: str, sector_name: str) -> str:
    if sector_code:
        return f"OPEN-CEDA-2025-{sector_code}"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", sector_name.strip()).strip("_")
    return f"OPEN-CEDA-2025-{slug.upper() or 'UNKNOWN'}"


def seed_ceda_factors(
    raw_csv_path: Path | None = None,
    conversion_csv_path: Path | None = None,
) -> None:
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir.parent.parent / "data"

    raw_csv_path = raw_csv_path or (data_dir / RAW_FILENAME)
    conversion_csv_path = conversion_csv_path or (data_dir / CONVERSION_FILENAME)

    if not raw_csv_path.exists():
        raise FileNotFoundError(f"Raw CSV file not found: {raw_csv_path}")
    if not conversion_csv_path.exists():
        raise FileNotFoundError(f"Conversion CSV file not found: {conversion_csv_path}")

    raw_rows = read_raw_factors(raw_csv_path)
    conversion_by_code, conversion_by_name = read_conversion_factors(conversion_csv_path)

    print(f"Loaded {len(raw_rows)} raw factors from {raw_csv_path.name}.")
    print(
        f"Loaded {len(conversion_by_code) + len(conversion_by_name)} conversion factors "
        f"from {conversion_csv_path.name}."
    )

    with Session(engine) as session:
        sys_user_id = get_system_user(session)
        added = 0
        skipped = 0

        for row in raw_rows:
            sector_code = row["sector_code"]
            sector_name = row["sector_name"]
            base_factor = row["factor"]

            multiplier = None
            if sector_code and sector_code in conversion_by_code:
                multiplier = conversion_by_code[sector_code]
            elif sector_name and sector_name in conversion_by_name:
                multiplier = conversion_by_name[sector_name]

            if multiplier is None:
                skipped += 1
                continue

            final_factor = base_factor * multiplier
            name = sector_name or sector_code or "Unknown Sector"
            if sector_code and sector_name:
                name = f"{sector_name} ({sector_code})"

            external_id = format_external_id(sector_code, sector_name)

            exists = (
                session.query(EmissionFactor)
                .filter_by(
                    external_id=external_id,
                    provider=PROVIDER,
                    year=YEAR,
                    geography=GEOGRAPHY,
                )
                .first()
            )

            if exists:
                continue

            session.add(
                EmissionFactor(
                    external_id=external_id,
                    provider=PROVIDER,
                    name=name,
                    geography=GEOGRAPHY,
                    year=YEAR,
                    unit_of_measure=UNIT_OF_MEASURE,
                    co2e_per_unit=final_factor,
                    scope_1_intensity=None,
                    scope_2_intensity=None,
                    scope_3_intensity=final_factor,
                    owner_id=sys_user_id,
                    source_url=None,
                    methodology="Open CEDA 2025 GHG_t_Raw x Purchaser-Producer conversion",
                    version=VERSION,
                )
            )
            added += 1

        session.commit()

    print(f"Seeded {added} Open CEDA factors. Skipped {skipped} without conversion.")


if __name__ == "__main__":
    seed_ceda_factors()
