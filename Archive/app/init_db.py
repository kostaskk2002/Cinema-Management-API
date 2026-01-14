"""
Script gia na dimiourgithoun oi pinakes kai na mpei o default ADMIN user
"""
from sqlalchemy import text
from app.database import engine, Base, SessionLocal

#Import ola ta models
from app.models.user import User, UserRole, AuthToken
from app.models.program import Program, ProgramRole
from app.models.screening import Screening
from app.utils.security import get_password_hash


def init_database():
    """
    Dimiourgia database tables kai default admin user
    """
    print("Dropping existing tables...")
    
    #Drop ola ta tables me swsti seira (antistrofi apo tin dimiourgia)
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS screenings"))
        conn.execute(text("DROP TABLE IF EXISTS program_roles"))
        conn.execute(text("DROP TABLE IF EXISTS auth_tokens"))
        conn.execute(text("DROP TABLE IF EXISTS programs"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    
    print("Creating database tables...")
    
    #Dimiourgia tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created!")
    
    #Dimiourgia default admin user
    db = SessionLocal()
    
    try:
        #Elegxos an yparxei idi admin
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if not existing_admin:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("Admin@123"),
                full_name="System Administrator",
                email="admin@cinema.com",
                role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            print("Default admin user created!")
            print("Username: admin")
            print("Password: Admin@123")
        else:
            print("Admin user already exists!")
    
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()