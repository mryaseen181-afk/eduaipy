import flet as ft
from eduai.services.auth_service import AuthService
from eduai.app.views.login_view import LoginView
from eduai.app.views.dashboard_view import DashboardView
from eduai.app.views.courses_view import CoursesView
from eduai.app.views.ai_tutor_view import AITutorView
from eduai.app.views.quiz_view import QuizView
from eduai.app.views.educator_view import EducatorView

class MainApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "StudyFlow EduAI"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 10
        
        # User session state
        self.user = None
        
        # Views dictionary
        self.views = {}
        
        # Setup view container
        self.content_area = ft.Container(expand=True)
        
        self.init_app()

    def init_app(self):
        # Check remember me session
        saved = AuthService.get_saved_session()
        if saved:
            self.user = saved
            self.show_main_layout()
        else:
            self.show_login_layout()

    def show_login_layout(self):
        self.page.clean()
        self.page.navigation_bar = None
        
        login_view = LoginView(self.page, on_login_success=self.on_login)
        self.page.add(
            ft.Container(
                content=login_view,
                alignment=ft.alignment.center,
                expand=True
            )
        )
        self.page.update()

    def on_login(self, user_data):
        self.user = user_data
        self.show_main_layout()

    def show_main_layout(self):
        self.page.clean()
        
        # Setup views
        self.views = {
            "dashboard": DashboardView(self.user, self.page, self),
            "courses": CoursesView(self.user, self.page),
            "ai_tutor": AITutorView(self.user, self.page),
            "quiz": QuizView(self.user, self.page),
            "educator": EducatorView(self.user, self.page),
            "settings": self.build_settings_view()
        }
        
        # Navigation Bar for mobile feel
        nav_destinations = []
        if self.user["role"] == "student":
            nav_destinations.append(ft.NavigationDestination(icon=ft.icons.DASHBOARD_ROUNDED, label="Home"))
        else:
            nav_destinations.append(ft.NavigationDestination(icon=ft.icons.CHALKBOARD_ROUNDED, label="Teacher Panel"))
            
        nav_destinations.extend([
            ft.NavigationDestination(icon=ft.icons.MENU_BOOK_ROUNDED, label="Courses"),
            ft.NavigationDestination(icon=ft.icons.SMART_TOY_ROUNDED, label="EduAI Chat"),
            ft.NavigationDestination(icon=ft.icons.QUIZ_ROUNDED, label="Practice"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS_ROUNDED, label="Settings")
        ])

        self.page.navigation_bar = ft.NavigationBar(
            destinations=nav_destinations,
            on_change=self.on_nav_change,
            selected_index=0,
            bgcolor=ft.colors.SURFACE_VARIANT
        )
        
        # Main layout wrapper
        self.page.add(
            ft.Column(
                [
                    # Top header row
                    ft.Row(
                        [
                            ft.Icon(ft.icons.GRADUATION_CAP_ROUNDED, color=ft.colors.INDIGO_400, size=28),
                            ft.Text("StudyFlow", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400),
                            ft.VerticalDivider(),
                            ft.Text(f"Logged: {self.user['username']}", size=11, color=ft.colors.GREY_400),
                            ft.Container(expand=True),
                            ft.IconButton(ft.icons.DARK_MODE_ROUNDED, on_click=self.toggle_theme, icon_size=18)
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Divider(height=1),
                    self.content_area
                ],
                expand=True
            )
        )
        
        # Load initial view
        self.switch_to_view(0)

    def on_nav_change(self, e):
        idx = e.control.selected_index
        self.switch_to_view(idx)

    def switch_to_view(self, idx):
        # Index translation
        keys = []
        if self.user["role"] == "student":
            keys = ["dashboard", "courses", "ai_tutor", "quiz", "settings"]
        else:
            keys = ["educator", "courses", "ai_tutor", "quiz", "settings"]
            
        active_key = keys[idx]
        self.content_area.content = self.views[active_key]
        
        # Force refresh view data if dashboard
        if active_key == "dashboard" and hasattr(self.views["dashboard"], "refresh_data"):
            self.views["dashboard"].refresh_data()
        elif active_key == "educator" and hasattr(self.views["educator"], "load_student_data"):
            self.views["educator"].load_student_data()
            
        self.page.update()

    def toggle_theme(self, e):
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            e.control.icon = ft.icons.LIGHT_MODE_ROUNDED
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            e.control.icon = ft.icons.DARK_MODE_ROUNDED
        self.page.update()

    def build_settings_view(self):
        profile_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Application Settings", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Username: {self.user['username']}", size=13),
                        ft.Text(f"Email: {self.user['email']}", size=13),
                        ft.Text(f"Status: Verified {self.user['role'].upper()} Profile", size=13),
                        ft.Divider(),
                        ft.ElevatedButton(
                            "Log Out",
                            icon=ft.icons.LOGOUT_ROUNDED,
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.RED_600,
                            on_click=self.handle_logout
                        )
                    ],
                    spacing=8
                ),
                padding=15
            )
        )
        return ft.Container(content=profile_card, padding=10)

    def handle_logout(self, e):
        AuthService.clear_session()
        self.user = None
        self.show_login_layout()

def start_flet_app():
    ft.app(target=MainApp)
