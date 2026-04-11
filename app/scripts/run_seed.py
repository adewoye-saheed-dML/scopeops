import sys
from pathlib import Path
from app.scripts.seed_ceda_categories import seed_ceda_categories
from app.scripts.seed_ceda_factors import seed_ceda_factors

def main():
    print("Starting manual database seed process...")
    try:
        root_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = root_dir / "data"
        
        excel_path = data_dir / "Open CEDA 2025.xlsx"
        raw_csv_path = data_dir / "Open CEDA 2025.xlsx - GHG_t_Raw.csv"
        conv_csv_path = data_dir / "Open CEDA 2025.xlsx - Purchaser - producer conversion.csv"
        
        
        for path in [excel_path, raw_csv_path, conv_csv_path]:
            if not path.exists():
                print(f"ERROR: Could not find file at {path}")
                sys.exit(1)

        print("1. Seeding CEDA Categories (Master Taxonomy)...")
        # Categories script takes the Excel file
        seed_ceda_categories(excel_path)
        print("Categories seeded successfully!\n")

        print("2. Seeding Global CEDA Emission Factors (This may take a minute)...")
        # Factors script takes the two CSV files
        seed_ceda_factors(raw_csv_path=raw_csv_path, conversion_csv_path=conv_csv_path)
        print("Emission factors seeded successfully!\n")

        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()