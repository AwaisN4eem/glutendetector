import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Ensure `backend/` is on sys.path so imports like `routers.analysis` work
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def test_db_session():
    """
    Creates an isolated in-memory SQLite DB per test.
    We avoid importing the full `main` app to prevent heavy model downloads (CV/NLP).
    """
    # Use StaticPool so the in-memory DB persists across connections/threads (TestClient).
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from database import Base  # imported after sys.path fix
    # Import models so SQLAlchemy registers all tables on Base.metadata
    import models  # noqa: F401

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_app(test_db_session):
    """FastAPI app with only lightweight routers + DB dependency override."""
    from database import get_db
    from routers import analysis, explain, prediction

    app = FastAPI()
    app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(explain.router, prefix="/api/explain", tags=["explain"])
    app.include_router(prediction.router, prefix="/api/prediction", tags=["prediction"])

    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture()
def client(test_app):
    return TestClient(test_app)


