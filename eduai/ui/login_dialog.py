from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QComboBox, QCheckBox, QStackedWidget, QWidget
)
from PySide6.QtCore import Qt
from eduai.services.auth_service import AuthService
from eduai.database.models import UserRole

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StudyFlow EduAI — Access Portal")
        self.setFixedSize(380, 480)
        self.user = None
        
        main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Build views
        self.init_login_view()
        self.init_register_view()
        self.init_reset_view()
        
        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.register_widget)
        self.stack.addWidget(self.reset_widget)
        
        # Check for saved session
        saved = AuthService.get_saved_session()
        if saved:
            self.user = saved
            # Accept immediately to log user in automatically
            self.accept()

    def init_login_view(self):
        self.login_widget = QWidget()
        layout = QVBoxLayout(self.login_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("StudyFlow EduAI")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Sign in to your learning account")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        self.remember_cb = QCheckBox("Remember Me")
        layout.addWidget(self.remember_cb)
        
        login_btn = QPushButton("Login")
        login_btn.setObjectName("Primary")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        # Links
        links_layout = QHBoxLayout()
        reg_link = QPushButton("Create Account")
        reg_link.setStyleSheet("background: transparent; border: none; text-decoration: underline; color: #6366f1;")
        reg_link.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        reset_link = QPushButton("Forgot Password?")
        reset_link.setStyleSheet("background: transparent; border: none; text-decoration: underline; color: #94a3b8;")
        reset_link.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        
        links_layout.addWidget(reg_link)
        links_layout.addWidget(reset_link)
        layout.addLayout(links_layout)

    def init_register_view(self):
        self.register_widget = QWidget()
        layout = QVBoxLayout(self.register_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("Create Account")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("Choose Username")
        layout.addWidget(self.reg_user)
        
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Enter Email Address")
        layout.addWidget(self.reg_email)
        
        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Create Password")
        self.reg_pass.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.reg_pass)
        
        self.reg_role = QComboBox()
        self.reg_role.addItems(["Student", "Educator"])
        layout.addWidget(self.reg_role)
        
        register_btn = QPushButton("Sign Up")
        register_btn.setObjectName("Primary")
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)
        
        back_btn = QPushButton("Back to Login")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)

    def init_reset_view(self):
        self.reset_widget = QWidget()
        layout = QVBoxLayout(self.reset_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("Reset Password")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.reset_user = QLineEdit()
        self.reset_user.setPlaceholderText("Confirm Username")
        layout.addWidget(self.reset_user)
        
        self.reset_email = QLineEdit()
        self.reset_email.setPlaceholderText("Confirm Registered Email")
        layout.addWidget(self.reset_email)
        
        self.reset_new_pass = QLineEdit()
        self.reset_new_pass.setPlaceholderText("New Password")
        self.reset_new_pass.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.reset_new_pass)
        
        reset_btn = QPushButton("Update Password")
        reset_btn.setObjectName("Primary")
        reset_btn.clicked.connect(self.handle_reset)
        layout.addWidget(reset_btn)
        
        back_btn = QPushButton("Cancel")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)

    def handle_login(self):
        u = self.username_input.text().strip()
        p = self.password_input.text().strip()
        rem = self.remember_cb.isChecked()
        
        if not u or not p:
            QMessageBox.warning(self, "Invalid Inputs", "Please enter both username and password.")
            return
            
        user_data = AuthService.authenticate(u, p, remember_me=rem)
        if user_data:
            self.user = user_data
            self.accept()
        else:
            QMessageBox.critical(self, "Failed", "Could not verify credentials. Check details and try again.")

    def handle_register(self):
        u = self.reg_user.text().strip()
        e = self.reg_email.text().strip()
        p = self.reg_pass.text().strip()
        role = UserRole.STUDENT if self.reg_role.currentText() == "Student" else UserRole.EDUCATOR
        
        if not u or not e or not p:
            QMessageBox.warning(self, "Invalid Inputs", "Please fill in all columns.")
            return
            
        success, msg = AuthService.register_user(u, e, p, role)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.stack.setCurrentIndex(0)
            self.username_input.setText(u)
        else:
            QMessageBox.critical(self, "Registration Failed", msg)

    def handle_reset(self):
        u = self.reset_user.text().strip()
        e = self.reset_email.text().strip()
        p = self.reset_new_pass.text().strip()
        
        if not u or not e or not p:
            QMessageBox.warning(self, "Invalid Inputs", "Please fill in all columns.")
            return
            
        success, msg = AuthService.reset_password(u, e, p)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.stack.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "Reset Failed", msg)
