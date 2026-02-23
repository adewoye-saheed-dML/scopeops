import os
import requests
import uuid
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import engine
from app.models.emission_factors import EmissionFactor
from app.models.user import User

load_dotenv()

API_KEY = os.getenv("DITCHCARBON_API_KEY")

if not API_KEY:
    raise ValueError("DITCHCARBON_API_KEY not set in environment")

URL = "https://api.ditchcarbon.com/industries"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}"
}

def get_system_user(session: Session) -> uuid.UUID:
    """Gets or creates the system admin user to own global emission factors."""
    sys_email = "system_epa@scopeops.local"
    sys_user = session.query(User).filter(User.email == sys_email).first()
    if not sys_user:
        sys_user = User(
            email=sys_email, 
            full_name="System Administrator", 
            provider="system", 
            is_active=True
        )
        session.add(sys_user)
        session.commit()
        session.refresh(sys_user)
    return sys_user.id


def seed_ditchcarbon_factors():
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    industries = response.json()

    with Session(engine) as session:
        # Get the system user ID for the new mandatory owner_id field
        sys_user_id = get_system_user(session)

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
                        
                        
                        unit_of_measure="USD",
                        co2e_per_unit=factor,
                        scope_1_intensity=None,
                        scope_2_intensity=None,
                        scope_3_intensity=factor,  
                        owner_id=sys_user_id,
                       
                        
                        source_url=source_url,
                        methodology="EPA IO Model (via DitchCarbon)",
                        version="v1.0"
                    )

                    session.add(new_factor)

        session.commit()

    print("DitchCarbon factors seeded successfully")


if __name__ == "__main__":
    seed_ditchcarbon_factors()