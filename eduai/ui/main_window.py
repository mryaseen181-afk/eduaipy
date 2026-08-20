from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QStackedWidget, QLabel, QFrame, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from eduai.config import THEME_DARK, THEME_LIGHT
from eduai.database.models import UserRole
from eduai.services.auth_service import AuthService
from eduai.ui.student_dashboard import StudentDashboard
from eduai.ui.educator_dashboard import EducatorDashboard
from eduai.ui.course_viewer import CourseViewer
from eduai.ui.ai_assistant_view import AIAssistantView
from eduai.ui.practice_arena import PracticeArena

class MainWindow(QMainWindow):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.is_dark = True
        self.setWindowTitle(f"StudyFlow EduAI Suite — [{self.user['role'].upper()}]")
        self.resize(1150, 720)

        # Style setting default
        self.setStyleSheet(THEME_DARK)
        
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. SIDEBAR NAVIGATION
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)
        
        logo = QLabel("StudyFlow")
        logo.setObjectName("Header")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        sidebar_layout.addWidget(logo)
        
        # Nav Buttons list
        self.nav_buttons = []
        
        # Student-only Home
        if self.user['role'] == "student":
            self.add_nav_button("🏠 Dashboard", 0, sidebar_layout)
            self.add_nav_button("📚 My Courses", 1, sidebar_layout)
            self.add_nav_button("🤖 EduAI Chatbot", 2, sidebar_layout)
            self.add_nav_button("🎯 Practice Arena", 3, sidebar_layout)
        else:
            # Educator Home
            self.add_nav_button("🎓 Teacher Panel", 4, sidebar_layout)
            self.add_nav_button("📚 Browse Content", 1, sidebar_layout)
            self.add_nav_button("🤖 EduAI Chatbot", 2, sidebar_layout)
            self.add_nav_button("🎯 Practice Arena", 3, sidebar_layout)
            
        self.add_nav_button("⚙️ Settings & System", 5, sidebar_layout)
        
        sidebar_layout.addStretch()
        
        role_tag = QLabel(f"Logged: {self.user['username']}\nRole: {self.user['role'].upper()}")
        role_tag.setObjectName("Subtitle")
        role_tag.setStyleSheet("font-size: 11px; margin-bottom: 10px;")
        sidebar_layout.addWidget(role_tag)
        
        layout.addWidget(sidebar, 1)
        
        # 2. MAIN STACKED WIDGETS CONTENT
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 5)
        
        # Initialize views
        self.student_dash = None
        if self.user['role'] == "student":
            self.student_dash = StudentDashboard(self.user, main_window=self)
            self.stack.addWidget(self.student_dash) # Index 0
        else:
            self.stack.addWidget(QWidget()) # Empty index 0
            
        self.course_viewer = CourseViewer(self.user)
        self.ai_assistant = AIAssistantView(self.user)
        self.practice_arena = PracticeArena(self.user)
        self.educator_dash = None
        
        if self.user['role'] == "educator":
            self.educator_dash = EducatorDashboard(self.user)
            # Add to index 4
            self.stack.addWidget(self.course_viewer) # 1
            self.stack.addWidget(self.ai_assistant) # 2
            self.stack.addWidget(self.practice_arena) # 3
            self.stack.addWidget(self.educator_dash) # 4
        else:
            self.stack.addWidget(self.course_viewer) # 1
            self.stack.addWidget(self.ai_assistant) # 2
            self.stack.addWidget(self.practice_arena) # 3
            self.stack.addWidget(QWidget()) # Empty index 4
            
        # Add Settings Panel view (Index 5)
        self.init_settings_view()
        self.stack.addWidget(self.settings_widget)
        
        # Set default active index
        if self.user['role'] == "student":
            self.switch_tab(0)
        else:
            self.switch_tab(4)

    def add_nav_button(self, name, target_idx, layout):
        btn = QPushButton(name)
        btn.setObjectName("NavButton")
        btn.clicked.connect(lambda: self.switch_tab(target_idx))
        layout.addWidget(btn)
        self.nav_buttons.append((btn, target_idx))

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        
        # Update nav button styles to show active state
        for btn, idx in self.nav_buttons:
            if idx == index:
                btn.setObjectName("NavButtonActive")
            else:
                btn.setObjectName("NavButton")
            # Refresh stylesheet to apply QSS rules
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def init_settings_view(self):
        self.settings_widget = QWidget()
        layout = QVBoxLayout(self.settings_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header = QLabel("⚙️ Application Settings")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        profile_card = QFrame()
        profile_card.setObjectName("Card")
        pc_layout = QVBoxLayout(profile_card)
        pc_layout.addWidget(QLabel(f"<b>Username:</b> {self.user['username']}"))
        pc_layout.addWidget(QLabel(f"<b>Email Address:</b> {self.user['email']}"))
        pc_layout.addWidget(QLabel(f"<b>Account Status:</b> Verified {self.user['role'].upper()} Profile"))
        layout.addWidget(profile_card)
        
        theme_card = QFrame()
        theme_card.setObjectName("Card")
        tc_layout = QVBoxLayout(theme_card)
        tc_layout.addWidget(QLabel("<b>Appearance Theme Selection</b>"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode Theme", "Light Mode Theme"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        tc_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_card)
        
        logout_btn = QPushButton("Log out from Session")
        logout_btn.setObjectName("Primary")
        logout_btn.setStyleSheet("background-color: #e11d48;")
        logout_btn.clicked.connect(self.handle_logout)
        layout.addWidget(logout_btn)
        
        layout.addStretch()

    def change_theme(self, index):
        if index == 0:
            self.setStyleSheet(THEME_DARK)
            self.is_dark = True
        else:
            self.setStyleSheet(THEME_LIGHT)
            self.is_dark = False
            
        # Update dashboard graphs theme
        if self.student_dash:
            self.student_dash.update_charts_theme(self.is_dark)

    def handle_logout(self):
        confirm = QMessageBox.question(self, "Logout", "Are you sure you want to log out?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            AuthService.clear_session()
            QMessageBox.information(self, "Logged Out", "You have successfully logged out. The app will restart.")
            
            # Restart Application login dialog flow
            import sys
            from PySide6.QtWidgets import QApplication
            
            # Close this window
            self.close()
            
            # Restart
            from eduai.ui.login_dialog import LoginDialog
            login = LoginDialog()
            if login.exec() == login.Accepted and login.user:
                self.__init__(login.user)
                self.show()
            else:
                QApplication.quit()
