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
        
        if not excel_path.exists():
            print(f"❌ ERROR: Could not find the main CEDA .xlsx file at {excel_path}")
            sys.exit(1)

        print(f"📁 Found Excel File: {excel_path.name}\n")

        print("1. Seeding CEDA Categories (Master Taxonomy)...")
        seed_ceda_categories(excel_path)
        print("✅ Categories seeded successfully!\n")

        print("2. Seeding Global CEDA Emission Factors (This may take a few minutes)...")
        seed_ceda_factors(excel_path)
        print("✅ Emission factors seeded successfully!\n")

        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ An error occurred during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()