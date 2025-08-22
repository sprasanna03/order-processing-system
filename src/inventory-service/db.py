import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DB_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def healthcheck():
    with engine.connect() as conn:
        conn.execute(text("select 1"))
