from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, 
    QScrollArea, QListWidget, QListWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from eduai.services.progress_service import ProgressService
from eduai.database.connection import SessionLocal
from eduai.database.models import User, Notification, UserAchievement
from eduai.ui.components.charts import StudyTimeChart, QuizPerformanceChart

class StudentDashboard(QWidget):
    def __init__(self, user, main_window, parent=None):
        super().__init__(parent)
        self.user = user
        self.main_window = main_window
        self.is_dark = True
        
        # Load latest data
        ProgressService.update_streak_and_activity(self.user['id'])
        self.refresh_user_data()

        # Layout
        self.setup_ui()

    def refresh_user_data(self):
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == self.user['id']).first()
            if u:
                self.user['xp'] = u.xp
                self.user['level'] = u.level
                self.user['streak_count'] = u.streak_count
        finally:
            db.close()

    def setup_ui(self):
        # Master layout scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(15)
        
        # Welcome & Streaks Header
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f"Welcome back, {self.user['username']}! 👋")
        welcome_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #6366f1;")
        header_layout.addWidget(welcome_label)
        
        streak_frame = QFrame()
        streak_frame.setObjectName("Card")
        streak_frame.setStyleSheet("background-color: #312e81; border: 1px solid #4338ca;")
        sf_layout = QHBoxLayout(streak_frame)
        sf_layout.setContentsMargins(10, 5, 10, 5)
        streak_label = QLabel(f"🔥 Streak: {self.user['streak_count']} Days")
        streak_label.setStyleSheet("font-weight: bold; color: #f59e0b; font-size: 14px;")
        sf_layout.addWidget(streak_label)
        header_layout.addWidget(streak_frame)
        
        scroll_layout.addLayout(header_layout)

        # Gamification & XP Progress Card
        xp_card = QFrame()
        xp_card.setObjectName("Card")
        xp_layout = QVBoxLayout(xp_card)
        
        level_lbl = QLabel(f"Scholar Level {self.user['level']}")
        level_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #38bdf8;")
        xp_layout.addWidget(level_lbl)
        
        xp_val = self.user['xp']
        current_level_base = (self.user['level'] - 1) * 100
        level_progress = xp_val - current_level_base
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat(f"{xp_val} XP ( {level_progress}/100 to Next Level )")
        self.progress_bar.setValue(min(100, level_progress))
        xp_layout.addWidget(self.progress_bar)
        scroll_layout.addWidget(xp_card)

        # Main Grid Layout (Left: Recommendations & Learning, Right: Charts & Stats)
        grid_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # --- LEFT PANEL ---
        # Continue Learning Card
        continue_card = QFrame()
        continue_card.setObjectName("Card")
        cc_layout = QVBoxLayout(continue_card)
        cc_layout.addWidget(QLabel("<b>Continue Learning</b>"))
        
        desc = QLabel("Pick up right where you left off in your courses.")
        desc.setObjectName("Subtitle")
        cc_layout.addWidget(desc)
        
        resume_btn = QPushButton("Resume Lesson")
        resume_btn.setObjectName("Primary")
        resume_btn.clicked.connect(lambda: self.main_window.switch_tab(1))
        cc_layout.addWidget(resume_btn)
        left_layout.addWidget(continue_card)
        
        # Recommendations Card
        recs_card = QFrame()
        recs_card.setObjectName("Card")
        rc_layout = QVBoxLayout(recs_card)
        rc_layout.addWidget(QLabel("<b>EduAI Smart Recommendations</b>"))
        
        recs = ProgressService.get_smart_recommendations(self.user['id'])
        for r in recs:
            rc_layout.addWidget(QLabel(f"• {r}"))
        left_layout.addWidget(recs_card)
        
        # Achievements Card
        ach_card = QFrame()
        ach_card.setObjectName("Card")
        ac_layout = QVBoxLayout(ach_card)
        ac_layout.addWidget(QLabel("<b>Badges & Achievements</b>"))
        
        db = SessionLocal()
        try:
            badges = db.query(UserAchievement).filter(UserAchievement.user_id == self.user['id']).all()
            if not badges:
                ac_layout.addWidget(QLabel("Complete lessons and quizzes to earn badges!"))
            else:
                for b in badges:
                    ac_layout.addWidget(QLabel(f"🏆 <b>{b.badge_name}</b> - {b.description}"))
        finally:
            db.close()
        left_layout.addWidget(ach_card)

        # --- RIGHT PANEL ---
        # Notifications & Daily Goal Panel
        notif_card = QFrame()
        notif_card.setObjectName("Card")
        nc_layout = QVBoxLayout(notif_card)
        nc_layout.addWidget(QLabel("<b>Study Inbox & Alerts</b>"))
        
        self.notif_list = QListWidget()
        self.notif_list.setFixedHeight(120)
        self.load_notifications()
        nc_layout.addWidget(self.notif_list)
        right_layout.addWidget(notif_card)
        
        # Performance Analytics Charts
        charts_card = QFrame()
        charts_card.setObjectName("Card")
        ch_layout = QVBoxLayout(charts_card)
        ch_layout.addWidget(QLabel("<b>Progress Analytics</b>"))
        
        # Chart 1: Study Time
        study_data = ProgressService.get_study_time_data(self.user['id'])
        self.study_chart = StudyTimeChart(study_data, is_dark=self.is_dark)
        ch_layout.addWidget(QLabel("Study duration by Topic (Minutes)"))
        ch_layout.addWidget(self.study_chart)
        
        # Chart 2: Quiz Score History
        quiz_data = ProgressService.get_quiz_performance_data(self.user['id'])
        self.quiz_chart = QuizPerformanceChart(quiz_data, is_dark=self.is_dark)
        ch_layout.addWidget(QLabel("Recent Quiz scores (%)"))
        ch_layout.addWidget(self.quiz_chart)
        
        right_layout.addWidget(charts_card)

        grid_layout.addLayout(left_layout, 1)
        grid_layout.addLayout(right_layout, 1)
        scroll_layout.addLayout(grid_layout)
        
        # Add scroll to main widget layout
        main_vbox = QVBoxLayout(self)
        main_vbox.addWidget(scroll)
        self.setLayout(main_vbox)

    def load_notifications(self):
        self.notif_list.clear()
        db = SessionLocal()
        try:
            notifs = db.query(Notification).filter(
                Notification.user_id == self.user['id']
            ).order_by(Notification.created_at.desc()).limit(5).all()
            
            # Default announcement if empty
            if not notifs:
                item = QListWidgetItem("📢 Educator: Welcome to StudyFlow EduAI! Start reading courses today.")
                self.notif_list.addItem(item)
            else:
                for n in notifs:
                    prefix = "📢" if n.type == "announcement" else "🔥" if n.type == "streak" else "🔔"
                    item = QListWidgetItem(f"{prefix} {n.title}: {n.message}")
                    self.notif_list.addItem(item)
        finally:
            db.close()

    def update_charts_theme(self, is_dark):
        self.is_dark = is_dark
        db = SessionLocal()
        try:
            study_data = ProgressService.get_study_time_data(self.user['id'])
            self.study_chart.update_chart(study_data, is_dark)
            
            quiz_data = ProgressService.get_quiz_performance_data(self.user['id'])
            self.quiz_chart.update_chart(quiz_data, is_dark)
        finally:
            db.close()
