import sys
from PySide6.QtWidgets import QApplication, QDialog
from eduai.database.connection import init_db
from eduai.ui.login_dialog import LoginDialog
from eduai.ui.main_window import MainWindow

def main():
    # 1. Initialize SQLite Database schemas and seed initial data
    init_db()
    
    # 2. Setup QApp and styles
    app = QApplication(sys.argv)
    
    # 3. Spawn Login and session check Dialog
    login = LoginDialog()
    if login.exec() == QDialog.Accepted and login.user:
        window = MainWindow(login.user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
