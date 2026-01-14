from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

#automata diavazoume tis plirofories pou uparxoun sto arxeio .env
settings = get_settings()

#Dimiourgia engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

#Dimiourgia session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class gia models
Base = declarative_base()


#Dependency gia FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#Function gia na dimiourgithoun oi pinakes me swsti seira
def create_tables():
    #Import ola ta models gia na ta "dei" to Base
    from app.models import user, program, screening
    
    #Drop ola kai ksanadimiourgia (mono gia development!)
    if settings.DEBUG:
        Base.metadata.drop_all(bind=engine)
    
    #Dimiourgia me swsti seira
    Base.metadata.create_all(bind=engine)