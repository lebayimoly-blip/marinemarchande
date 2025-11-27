from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Exemple avec SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./app/database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dépendance pour FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
