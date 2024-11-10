from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Remplacez 'user', 'password' et 'sportify' par vos détails
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://sportify:sportify2@localhost/sportify"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
