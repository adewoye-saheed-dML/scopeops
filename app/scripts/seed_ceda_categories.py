import openpyxl
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import engine
from app.models.category import Category


def seed_ceda_categories(xlsx_path: Path, sheet_name: str = "metadata") -> None:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)

    if sheet_name not in wb.sheetnames:
        raise ValueError(
            f"Sheet '{sheet_name}' not found. Available sheets: {wb.sheetnames}"
        )

    ws = wb[sheet_name]
    rows = ws.iter_rows(values_only=True)

    # Use the first row as headers
    headers = [str(cell).strip() if cell is not None else "" for cell in next(rows)]

    with Session(engine) as session:
        for row in rows:
            row_dict = dict(zip(headers, row))

            sector_code = (str(row_dict.get("Sector Code") or "")).strip()
            sector_name = (str(row_dict.get("Sector Name") or "")).strip()

            if not sector_code or not sector_name:
                continue

            if not session.get(Category, sector_code):
                session.add(
                    Category(
                        category_id=sector_code,
                        category_name=sector_name,
                    )
                )
        session.commit()

    wb.close()


if __name__ == "__main__":
    default_xlsx = Path(__file__).resolve().parent / "Open CEDA 2025.xlsx"
    seed_ceda_categories(default_xlsx)
    print("Open CEDA categories seeded successfully")