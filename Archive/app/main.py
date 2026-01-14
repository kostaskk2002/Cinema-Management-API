from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, inspect
import time

from app.database import engine, Base, SessionLocal
from app.config import get_settings
from app.routes import auth_router, users_router, programs_router, screenings_router

settings = get_settings()

#Dimiourgia FastAPI app
app = FastAPI(
    title="Cinema Management System API",
    description="RESTful API gia diaxeirisi kinimatorafou",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Middleware gia logging kai error handling
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware gia na metraei to response time
    """
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(e) if settings.DEBUG else "An error occurred"
            }
        )


#Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler gia database errors
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "error": str(exc) if settings.DEBUG else "Database operation failed"
        }
    )


#Startup event
@app.on_event("startup")
async def startup_event():
    """
    Dimiourgia ton database tables MONO an den yparxoun
    """
    print("Initializing database...")
    
    #Import ola ta models gia na ta "dei" to Base
    from app.models.user import User, UserRole, AuthToken
    from app.models.program import Program, ProgramRole
    from app.models.screening import Screening
    from app.utils.security import get_password_hash
    
    try:
        #Elegxos an yparxoun idi tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            print(f"Database already initialized. Existing tables: {', '.join(existing_tables)}")
        else:
            print("No tables found. Creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully!")
            
            #Elegxos poioi pinakes dimiourgithikan
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {', '.join(tables)}")
        
        #Dimiourgia default admin user AN den yparxei
        db = SessionLocal()
        try:
            existing_admin = db.query(User).filter(User.username == "admin").first()
            
            if not existing_admin:
                print("Creating default admin user...")
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
                print("  Username: admin")
                print("  Password: Admin@123")
            else:
                print("Admin user already exists.")
        
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        raise


#Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup otan kleinei to app
    """
    print("Shutting down application...")


#Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "message": "Cinema Management System API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Detailed health check
    """
    try:
        #Elegxos database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e) if settings.DEBUG else "Database connection failed"
            }
        )


#Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(programs_router)
app.include_router(screenings_router)


#Gia na trexei to app directly (optional)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )