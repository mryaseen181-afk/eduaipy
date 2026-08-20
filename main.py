import uvicorn
from eduai.database.connection import init_db

def main():
    # 1. Initialize SQLite Database schemas and seed initial data
    init_db()
    
    # 2. Run Uvicorn server for the FastAPI mobile-responsive Web App
    print("\n-----------------------------------------------------------")
    print("StudyFlow EduAI server starting locally...")
    print("To open the mobile-friendly web app:")
    print("--> Open your browser and go to: http://127.0.0.1:8000")
    print("-----------------------------------------------------------\n")
    
    uvicorn.run("eduai.web.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
