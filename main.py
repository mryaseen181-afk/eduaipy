from eduai.database.connection import init_db
from eduai.app.main_app import start_flet_app

def main():
    # 1. Initialize SQLite Database schemas and seed initial data
    init_db()
    
    # 2. Start the Flet application
    print("\n-----------------------------------------------------------")
    print("StudyFlow EduAI Flet Mobile/Desktop application starting...")
    print("-----------------------------------------------------------\n")
    start_flet_app()

if __name__ == "__main__":
    main()
