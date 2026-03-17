# ScopeOps Backend API

The backend services and RESTful API for the ScopeOps platform. Built with Python and FastAPI, this robust backend handles complex climate data modeling, hierarchical supplier relationships, secure authentication, and automated Scope 1, 2, and 3 emissions calculations using industry-standard factors (EPA, DitchCarbon).

<img width="1410" height="773" alt="Image" src="https://github.com/user-attachments/assets/74437333-942c-480a-b426-b7a0311cfcbe" />

- **swagger docs:** https://scopeops-adewoyesaheed1845-unpbv5or.leapcell.dev/docs

## Features

- **High-Performance API:** Fast, asynchronous REST APIs built with [FastAPI](https://fastapi.tiangolo.com/).
- **Emissions Calculation Engine:** Automated carbon accounting and spend-based emissions modeling (`app/services/emission_calculator.py`).
- **Hierarchical Data Rollups:** Calculates aggregated emissions across complex supplier and spend trees (`app/services/tree_rollup.py`).
- **Database Management:** Relational data modeling with [SQLAlchemy](https://www.sqlalchemy.org/) and automated database migrations using [Alembic](https://alembic.sqlalchemy.org/).
- **Data Validation:** Strict type-checking and schema validation using [Pydantic](https://docs.pydantic.dev/).
- **Secure Authentication:** JWT-based user authentication and role management.
- **Factor Seeding Scripts:** Built-in scripts to seed EPA and DitchCarbon emission factors directly into the database.

## Tech Stack

- **Framework:** FastAPI (Python 3.10+)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Validation:** Pydantic
- **Testing:** Pytest
- **Security:** Passlib, JWT

## Project Structure

```text
scopeops/
├── app/
│   ├── config/          # Configuration and static lists (e.g., verified suppliers)
│   ├── models/          # SQLAlchemy database models (User, Supplier, Spend, etc.)
│   ├── routers/         # FastAPI route endpoints (auth, suppliers, spend, factors)
│   ├── schemas/         # Pydantic schemas for request/response validation
│   ├── scripts/         # Data seeding scripts (EPA, DitchCarbon factors)
│   ├── services/        # Core business logic and emission calculators
│   ├── tests/           # Pytest test suites
│   ├── database.py      # Database connection setup
│   └── main.py          # FastAPI application instance and entry point
├── data/                # Raw datasets (e.g., GHG Emission Factors Hub)
├── migration/           # Alembic migration environments and versions
├── alembic.ini          # Alembic configuration
└── requirements.txt     # Python dependencies
```

## Getting Started

### Prerequisites

- **Python** (v3.10 or higher)
- **pip** (Python package installer)

### Installation & Setup

1. **Clone the repository:**

```bash
git clone https://github.com/adewoye-saheed-dML/scopeops.git
cd scopeops
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Environment Variables:** Create a `.env` file in the root directory and set your database URL and secret keys:

```env
DATABASE_URL=sqlite:///./scopeops.db
SECRET_KEY=your_super_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. **Run Database Migrations:** Apply the latest database schemas using Alembic:

```bash
alembic upgrade head
```

6. **Seed Initial Data _(Optional)_:** Populate emission factors into the database:

```bash
python -m app.scripts.seed_epa_factors
```

7. **Start the Development Server:**

```bash
uvicorn app.main:app --reload
```

8. **Access API Documentation:** Once the server is running, navigate to:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Testing

Ensure your virtual environment is activated, then run the full test suite:

```bash
pytest
```

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/adewoye-saheed-dML/scopeops/issues).

## Author

**Saheed Damilola Adewoye**

- GitHub: [@adewoye-saheed-dML](https://github.com/adewoye-saheed-dML)
- LinkedIn: [adewoye-saheed-dml](https://www.linkedin.com/in/adewoye-saheed-dml)

## License

This project is licensed under the [MIT License](LICENSE).