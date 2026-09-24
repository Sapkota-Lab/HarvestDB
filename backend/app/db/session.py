from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from app.core.config import settings

engine = create_engine(settings.database_url, future=True)
testengine = create_engine(settings.testing_database_url, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
testingSessionLocal = sessionmaker(bind=testengine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_db():
    db = testingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_test_db_connection(): # function to verify the connection to the testing database
    try:
        with testengine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False