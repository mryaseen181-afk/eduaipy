import flet as ft
from eduai.services.auth_service import AuthService
from eduai.database.models import UserRole

class LoginView(ft.UserControl):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.page = page
        self.on_login_success = on_login_success
        
        # Forms state fields
        self.login_user = ft.TextField(label="Username", width=280)
        self.login_pass = ft.TextField(label="Password", password=True, can_reveal_password=True, width=280)
        self.remember_me = ft.Checkbox(label="Remember me on this device", value=False)
        
        self.reg_user = ft.TextField(label="Choose Username", width=280)
        self.reg_email = ft.TextField(label="Enter Email Address", width=280)
        self.reg_pass = ft.TextField(label="Create Password", password=True, can_reveal_password=True, width=280)
        self.reg_role = ft.Dropdown(
            label="Account Role",
            width=280,
            options=[
                ft.dropdown.Option("student", "Student"),
                ft.dropdown.Option("educator", "Educator")
            ],
            value="student"
        )
        
        self.reset_user = ft.TextField(label="Confirm Username", width=280)
        self.reset_email = ft.TextField(label="Confirm Email", width=280)
        self.reset_new_pass = ft.TextField(label="New Password", password=True, can_reveal_password=True, width=280)

        # Main active view switcher
        self.views_container = ft.Container(expand=True)

    def build(self):
        self.show_login_form(None)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        # Logo Header
                        ft.Icon(ft.icons.GRADUATION_CAP_ROUNDED, color=ft.colors.INDIGO_400, size=40),
                        ft.Text("StudyFlow EduAI", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("Sign in to your learning account", size=12, color=ft.colors.GREY_400),
                        ft.Divider(height=1),
                        
                        # Active form panel
                        self.views_container,
                        
                        # Tabs Selector buttons
                        ft.Row(
                            [
                                ft.TextButton("Login", on_click=self.show_login_form),
                                ft.TextButton("Sign Up", on_click=self.show_register_form),
                                ft.TextButton("Reset", on_click=self.show_reset_form)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12
                ),
                padding=20,
                width=320,
                height=420
            )
        )

    def show_login_form(self, e):
        self.views_container.content = ft.Column(
            [
                self.login_user,
                self.login_pass,
                self.remember_me,
                ft.ElevatedButton(
                    "Sign In",
                    width=280,
                    bgcolor=ft.colors.INDIGO_500,
                    color=ft.colors.WHITE,
                    on_click=self.handle_login
                )
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.update()

    def show_register_form(self, e):
        self.views_container.content = ft.Column(
            [
                self.reg_user,
                self.reg_email,
                self.reg_pass,
                self.reg_role,
                ft.ElevatedButton(
                    "Sign Up",
                    width=280,
                    bgcolor=ft.colors.INDIGO_500,
                    color=ft.colors.WHITE,
                    on_click=self.handle_register
                )
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.update()

    def show_reset_form(self, e):
        self.views_container.content = ft.Column(
            [
                self.reset_user,
                self.reset_email,
                self.reset_new_pass,
                ft.ElevatedButton(
                    "Update Password",
                    width=280,
                    bgcolor=ft.colors.INDIGO_500,
                    color=ft.colors.WHITE,
                    on_click=self.handle_reset
                )
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.update()

    def handle_login(self, e):
        u = self.login_user.value.strip()
        p = self.login_pass.value.strip()
        rem = self.remember_me.value
        
        if not u or not p:
            self.show_snack("Please fill in both columns.")
            return
            
        user_data = AuthService.authenticate(u, p, remember_me=rem)
        if user_data:
            self.on_login_success(user_data)
        else:
            self.show_snack("Invalid username or password.")

    def handle_register(self, e):
        u = self.reg_user.value.strip()
        em = self.reg_email.value.strip()
        p = self.reg_pass.value.strip()
        role = UserRole.STUDENT if self.reg_role.value == "student" else UserRole.EDUCATOR
        
        if not u or not em or not p:
            self.show_snack("All columns are required.")
            return
            
        success, msg = AuthService.register_user(u, em, p, role)
        self.show_snack(msg)
        if success:
            self.login_user.value = u
            self.show_login_form(None)

    def handle_reset(self, e):
        u = self.reset_user.value.strip()
        em = self.reset_email.value.strip()
        p = self.reset_new_pass.value.strip()
        
        if not u or not em or not p:
            self.show_snack("All columns are required.")
            return
            
        success, msg = AuthService.reset_password(u, em, p)
        self.show_snack(msg)
        if success:
            self.show_login_form(None)

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
