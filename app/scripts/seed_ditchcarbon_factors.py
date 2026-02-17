import os
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import engine
from scopeops.app.models.emission_factors import EmissionFactor

load_dotenv()

API_KEY = os.getenv("DITCHCARBON_API_KEY")

if not API_KEY:
    raise ValueError("DITCHCARBON_API_KEY not set in environment")

URL = "https://api.ditchcarbon.com/industries"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}"
}


def seed_ditchcarbon():
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    industries = response.json()

    with Session(engine) as session:

        for industry in industries:

            external_id = industry.get("id")
            name = industry.get("name")

            performances = industry.get("performances", [])

            for perf in performances:

                year = perf.get("year")
                region = perf.get("region")
                factor = perf.get("emission_factor")
                source_url = perf.get("source", {}).get("url")

                # Idempotency check
                exists = session.query(EmissionFactor).filter_by(
                    external_id=external_id,
                    provider="DitchCarbon",
                    year=year,
                    geography=region
                ).first()

                if not exists:
                    new_factor = EmissionFactor(
                        external_id=external_id,
                        provider="DitchCarbon",
                        name=name,
                        geography=region,
                        year=year,
                        co2e_per_currency=factor,
                        source_url=source_url,
                        methodology="EPA IO Model (via DitchCarbon)",
                        version="v1.0"
                    )

                    session.add(new_factor)

        session.commit()

    print("DitchCarbon factors seeded successfully")


if __name__ == "__main__":
    seed_ditchcarbon()
