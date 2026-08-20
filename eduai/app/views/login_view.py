import flet as ft
from eduai.services.auth_service import AuthService
from eduai.database.models import UserRole

class LoginView(ft.UserControl):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.page = page
        self.on_login_success = on_login_success
        
        # Design text fields with rounded corners
        self.login_user = ft.TextField(
            label="Username",
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.PERSON_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.login_pass = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.LOCK_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.remember_me = ft.Checkbox(
            label="Remember me on this device",
            value=False,
            fill_color=ft.colors.INDIGO_500
        )
        
        self.reg_user = ft.TextField(
            label="Choose Username",
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.PERSON_ADD_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.reg_email = ft.TextField(
            label="Email Address",
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.EMAIL_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.reg_pass = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.LOCK_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.reg_role = ft.Dropdown(
            label="Role",
            width=280,
            border_radius=12,
            options=[
                ft.dropdown.Option("student", "Student"),
                ft.dropdown.Option("educator", "Educator")
            ],
            value="student",
            border_color=ft.colors.INDIGO_600
        )
        
        self.reset_user = ft.TextField(
            label="Confirm Username",
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.PERSON_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.reset_email = ft.TextField(
            label="Registered Email",
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.EMAIL_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )
        self.reset_new_pass = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=280,
            border_radius=12,
            prefix_icon=ft.icons.LOCK_ROUNDED,
            border_color=ft.colors.INDIGO_600
        )

        self.views_container = ft.Container(expand=True)

    def build(self):
        # Set default login view content directly (no update call on unmounted control)
        self.views_container.content = ft.Column(
            [
                self.login_user,
                self.login_pass,
                self.remember_me,
                ft.Container(height=4),
                ft.ElevatedButton(
                    "Sign In",
                    width=280,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.INDIGO_600
                    ),
                    on_click=self.handle_login
                )
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(ft.icons.GRADUATION_CAP_ROUNDED, color=ft.colors.INDIGO_400, size=48),
                        margin=ft.margin.only(bottom=5)
                    ),
                    ft.Text("StudyFlow EduAI", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text("Next-Gen Intelligent Learning Suite", size=12, color=ft.colors.GREY_400),
                    ft.Container(height=8),
                    
                    self.views_container,
                    
                    ft.Row(
                        [
                            ft.TextButton("Login", on_click=self.show_login_form, style=ft.ButtonStyle(color=ft.colors.INDIGO_400)),
                            ft.TextButton("Sign Up", on_click=self.show_register_form, style=ft.ButtonStyle(color=ft.colors.GREY_400)),
                            ft.TextButton("Reset", on_click=self.show_reset_form, style=ft.ButtonStyle(color=ft.colors.GREY_400))
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            bgcolor=ft.colors.GREY_900,
            padding=30,
            border_radius=24,
            border=ft.border.all(1, ft.colors.GREY_800),
            width=340,
            height=460,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            )
        )

    def show_login_form(self, e):
        self.views_container.content = ft.Column(
            [
                self.login_user,
                self.login_pass,
                self.remember_me,
                ft.Container(height=4),
                ft.ElevatedButton(
                    "Sign In",
                    width=280,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.INDIGO_600
                    ),
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
                ft.Container(height=4),
                ft.ElevatedButton(
                    "Create Account",
                    width=280,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.INDIGO_600
                    ),
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
                ft.Container(height=4),
                ft.ElevatedButton(
                    "Update Password",
                    width=280,
                    height=45,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.INDIGO_600
                    ),
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
            self.show_snack("Please enter both username and password.")
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
            self.show_snack("All registration columns are required.")
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
            self.show_snack("All reset columns are required.")
            return
            
        success, msg = AuthService.reset_password(u, em, p)
        self.show_snack(msg)
        if success:
            self.show_login_form(None)

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
