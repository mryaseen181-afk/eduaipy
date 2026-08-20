import flet as ft
from eduai.services.progress_service import ProgressService
from eduai.database.connection import SessionLocal
from eduai.database.models import User, Notification, UserAchievement

class DashboardView(ft.Container):
    def __init__(self, user, page: ft.Page, app_router):
        super().__init__()
        self.user = user
        self.page = page
        self.app_router = app_router
        self.expand = True
        
        # UI controls references
        self.welcome_txt = ft.Text(size=20, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400)
        self.streak_txt = ft.Text(size=13, weight=ft.FontWeight.BOLD, color=ft.colors.AMBER_400)
        
        self.progress_bar = ft.ProgressBar(value=0, color=ft.colors.EMERALD_500, bgcolor=ft.colors.GREY_800, height=8)
        self.xp_details = ft.Text(size=12, color=ft.colors.GREY_400)
        
        self.recs_col = ft.Column(spacing=5)
        self.badges_row = ft.Row(wrap=True, spacing=10)
        self.notif_col = ft.Column(spacing=5)
        
        self.chart_container = ft.Column(spacing=15)

        self.refresh_data()
        self.content = self.build_layout()

    def refresh_data(self):
        # Refresh session user details from database
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == self.user["id"]).first()
            if u:
                self.user["xp"] = u.xp
                self.user["level"] = u.level
                self.user["streak_count"] = u.streak_count
        finally:
            db.close()

        self.welcome_txt.value = f"Welcome back, {self.user['username']}! 👋"
        self.streak_txt.value = f"🔥 Streak: {self.user['streak_count']} Days"
        
        # XP Level progress
        current_level_base = (self.user["level"] - 1) * 100
        level_progress = self.user["xp"] - current_level_base
        self.progress_bar.value = min(1.0, level_progress / 100.0)
        self.xp_details.value = f"Scholar Level {self.user['level']} | {self.user['xp']} total XP ({level_progress}/100 to Next Level)"

        # Load recommendations
        self.recs_col.controls.clear()
        recs = ProgressService.get_smart_recommendations(self.user["id"])
        for r in recs:
            self.recs_col.controls.append(
                ft.Row([ft.Icon(ft.icons.CHEVRON_RIGHT_ROUNDED, color=ft.colors.INDIGO_400, size=16), ft.Text(r, size=12)])
            )

        # Load badges
        self.badges_row.controls.clear()
        db = SessionLocal()
        try:
            badges = db.query(UserAchievement).filter(UserAchievement.user_id == self.user["id"]).all()
            if not badges:
                self.badges_row.controls.append(ft.Text("Complete lessons & quizzes to earn badges!", size=12, color=ft.colors.GREY_500))
            else:
                for b in badges:
                    self.badges_row.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.icons.TROPHY_ROUNDED, color=ft.colors.AMBER_400, size=16),
                                    ft.Text(b.badge_name, size=11, weight=ft.FontWeight.BOLD)
                                ],
                                spacing=4
                            ),
                            bgcolor=ft.colors.SURFACE_VARIANT,
                            padding=ft.padding.all(6),
                            border_radius=8
                        )
                    )
                    
            # Load inbox notifications
            self.notif_col.controls.clear()
            notifs = db.query(Notification).filter(Notification.user_id == self.user["id"]).order_by(Notification.created_at.desc()).limit(3).all()
            if not notifs:
                self.notif_col.controls.append(
                    ft.Text("📢 Welcome to StudyFlow! Head over to 'Courses' to choose a lesson.", size=12, color=ft.colors.GREY_400)
                )
            else:
                for n in notifs:
                    prefix = "📢" if n.type == "announcement" else "🔥" if n.type == "streak" else "🔔"
                    self.notif_col.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(f"{prefix} {n.title}", size=11, weight=ft.FontWeight.BOLD),
                                    ft.Text(n.message, size=11, color=ft.colors.GREY_400)
                                ],
                                spacing=2
                            ),
                            bgcolor=ft.colors.GREY_900,
                            padding=8,
                            border_radius=8,
                            width=320
                        )
                    )
        finally:
            db.close()
            
        self.render_native_charts()

    def render_native_charts(self):
        self.chart_container.controls.clear()
        
        study_time = ProgressService.get_study_time_data(self.user["id"])
        quiz_scores = ProgressService.get_quiz_performance_data(self.user["id"])
        
        # 1. Bar Chart for Study Duration
        if study_time:
            self.chart_container.controls.append(ft.Text("Study Duration by Topic (Minutes)", size=12, weight=ft.FontWeight.BOLD))
            bar_groups = []
            for i, (topic_title, mins) in enumerate(study_time.items()):
                bar_groups.append(
                    ft.BarChartGroup(
                        x=i,
                        bar_rods=[
                            ft.BarChartRod(
                                y=mins,
                                color=ft.colors.INDIGO_400,
                                width=16,
                                border_radius=4
                            )
                        ]
                    )
                )
            self.chart_container.controls.append(
                ft.Container(
                    content=ft.BarChart(
                        bar_groups,
                        left_axis=ft.ChartAxis(labels_size=30),
                        bottom_axis=ft.ChartAxis(labels_size=30),
                        horizontal_grid_lines=ft.ChartGridLines(color=ft.colors.GREY_800, width=1, dash_pattern=[3,3]),
                        expand=True
                    ),
                    height=130,
                    padding=10,
                    bgcolor=ft.colors.GREY_950,
                    border_radius=10
                )
            )
            
        # 2. Line Chart for Quiz history
        if quiz_scores:
            self.chart_container.controls.append(ft.Text("Recent Quiz Scores (%)", size=12, weight=ft.FontWeight.BOLD))
            data_points = []
            for i, score in enumerate(quiz_scores):
                data_points.append(ft.LineChartDataPoint(x=i+1, y=score))
                
            self.chart_container.controls.append(
                ft.Container(
                    content=ft.LineChart(
                        [
                            ft.LineChartData(
                                data_points=data_points,
                                color=ft.colors.EMERALD_400,
                                stroke_width=3,
                                curved=True,
                                below_line_color=ft.colors.with_opacity(0.1, ft.colors.EMERALD_400),
                                below_line_fill=ft.colors.Opacity(0.1)
                            )
                        ],
                        left_axis=ft.ChartAxis(labels_size=30),
                        bottom_axis=ft.ChartAxis(labels_size=30),
                        horizontal_grid_lines=ft.ChartGridLines(color=ft.colors.GREY_800, width=1),
                        expand=True
                    ),
                    height=130,
                    padding=10,
                    bgcolor=ft.colors.GREY_950,
                    border_radius=10
                )
            )

    def build_layout(self):
        # Master scroll column
        return ft.Column(
            [
                # Profile Welcome Card
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        self.welcome_txt,
                                        ft.Text("Keep learning daily to level up!", size=12, color=ft.colors.GREY_400)
                                    ],
                                    spacing=2,
                                    expand=True
                                ),
                                ft.Container(
                                    content=self.streak_txt,
                                    bgcolor=ft.colors.INDIGO_900,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                    border_radius=12,
                                    border=ft.border.all(1, ft.colors.INDIGO_600)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15
                    )
                ),
                
                # Progress XP Bar
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                self.xp_details,
                                self.progress_bar
                            ],
                            spacing=6
                        ),
                        padding=15
                    )
                ),
                
                # Double Pane Column content
                ft.Text("EduAI Smart Recommendations", size=13, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.recs_col,
                    bgcolor=ft.colors.GREY_900,
                    padding=10,
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.GREY_800)
                ),
                
                ft.Text("Inbox Notifications", size=13, weight=ft.FontWeight.BOLD),
                ft.Row(
                    self.notif_col.controls,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
                
                ft.Text("Milestone Badges", size=13, weight=ft.FontWeight.BOLD),
                self.badges_row,
                
                ft.Divider(height=10),
                
                # Charts section
                self.chart_container
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            spacing=10
        )
