import uvicorn
from app.database import init_db

if __name__ == "__main__":
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database ready!")
    
    # Run the app
    print("Starting server on http://localhost:8000")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)