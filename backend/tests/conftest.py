import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app
from app.core.database import Base, engine, import_all_models


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import_all_models()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)
