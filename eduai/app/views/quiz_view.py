import time
import flet as ft
from eduai.services.ai_service import AIService
from eduai.services.progress_service import ProgressService
from eduai.database.connection import SessionLocal
from eduai.database.models import Quiz, QuizResult, Question

class QuizView(ft.UserControl):
    def __init__(self, user, page: ft.Page):
        super().__init__()
        self.user = user
        self.page = page
        
        # State variables
        self.quiz_questions = []
        self.current_q_idx = 0
        self.user_answers = {} # index -> answer_str
        self.marked_for_review = set()
        
        self.is_exam_mode = False
        self.timer_seconds = 0
        self.timer_active = False

        # Panels setup
        self.generator_panel = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)
        self.active_test_panel = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)
        self.report_panel = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)
        
        self.main_container = ft.Container(content=self.generator_panel, expand=True)

        self.init_generator()

    def init_generator(self):
        self.subject_dropdown = ft.Dropdown(
            label="Subject Category",
            options=[
                ft.dropdown.Option("Mathematics"),
                ft.dropdown.Option("Physics"),
                ft.dropdown.Option("Chemistry"),
                ft.dropdown.Option("Biology")
            ],
            value="Mathematics",
            width=280
        )
        self.chapter_field = ft.TextField(
            label="Chapter / Topic",
            placeholder="e.g. Newtonian Laws, Algebra...",
            width=280
        )
        self.diff_dropdown = ft.Dropdown(
            label="Difficulty",
            options=[
                ft.dropdown.Option("Easy"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("Hard")
            ],
            value="Medium",
            width=280
        )
        self.num_questions_field = ft.TextField(
            label="Number of Questions",
            value="5",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=280
        )

        self.generator_panel.controls.extend([
            ft.Text("🎯 StudyFlow Practice Arena", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400),
            ft.Text("Setup parameters to create customized AI learning quizzes.", size=11, color=ft.colors.GREY_400),
            self.subject_dropdown,
            self.chapter_field,
            self.diff_dropdown,
            self.num_questions_field,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Generate Practice Quiz",
                        icon=ft.icons.PLAY_ARROW_ROUNDED,
                        bgcolor=ft.colors.INDIGO_500,
                        color=ft.colors.WHITE,
                        on_click=lambda e: self.start_quiz(exam_mode=False)
                    ),
                    ft.ElevatedButton(
                        "Start Timed Exam ⏱️",
                        icon=ft.icons.ALARM_ROUNDED,
                        bgcolor=ft.colors.RED_600,
                        color=ft.colors.WHITE,
                        on_click=lambda e: self.start_quiz(exam_mode=True)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
        ])

    def start_quiz(self, exam_mode):
        subject = self.subject_dropdown.value
        chapter = self.chapter_field.value.strip() or "General Mechanics"
        difficulty = self.diff_dropdown.value
        num_q = int(self.num_questions_field.value or "5")
        
        self.main_container.content = ft.Column(
            [ft.ProgressRing(color=ft.colors.INDIGO_500), ft.Text("Generating your AI quiz questions...", size=12)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.page.update()
        
        def fetch():
            try:
                self.quiz_questions = AIService.generate_ai_quiz(subject, chapter, difficulty, num_q)
                self.user_answers = {}
                self.marked_for_review.clear()
                self.current_q_idx = 0
                self.is_exam_mode = exam_mode
                
                # Active UI Setup
                self.setup_active_quiz_panel(chapter, difficulty)
                self.main_container.content = self.active_test_panel
                
                if self.is_exam_mode:
                    self.timer_seconds = len(self.quiz_questions) * 1.5 * 60
                    self.timer_active = True
                    self.page.run_thread(self.run_quiz_timer)
                    
                self.load_question(0)
            except Exception as e:
                self.main_container.content = self.generator_panel
                self.show_snack(f"Quiz Setup Failed: {str(e)}")
            self.page.update()
            
        self.page.run_thread(fetch)

    def run_quiz_timer(self):
        while self.timer_active:
            if self.timer_seconds <= 0:
                self.timer_active = False
                self.show_snack("Time limit reached! Submitting quiz paper.")
                self.submit_quiz_action(None)
                break
            time.sleep(1)
            self.timer_seconds -= 1
            # Update timer text
            mins = self.timer_seconds // 60
            secs = self.timer_seconds % 60
            self.timer_label.value = f"Time: {mins:02d}:{secs:02d}"
            self.page.update()

    def setup_active_quiz_panel(self, chapter, difficulty):
        self.active_test_panel.controls.clear()
        
        self.quiz_title_label = ft.Text(f"Quiz: {chapter}", size=14, weight=ft.FontWeight.BOLD)
        self.timer_label = ft.Text("Time: 00:00", size=12, color=ft.colors.RED_400, weight=ft.FontWeight.BOLD, visible=self.is_exam_mode)
        
        self.question_label = ft.Text(size=13, weight=ft.FontWeight.BOLD)
        self.options_group = ft.RadioGroup(content=ft.Column(spacing=6))
        self.fill_input = ft.TextField(label="Your Answer", placeholder="Type your answer here...", visible=False)
        
        self.nav_index_row = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=6)
        
        self.active_test_panel.controls.extend([
            ft.Row([self.quiz_title_label, self.timer_label], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.question_label,
            self.options_group,
            self.fill_input,
            ft.Divider(),
            ft.Row(
                [
                    ft.TextButton("Previous", on_click=lambda e: self.load_question(self.current_q_idx - 1)),
                    ft.TextButton("Mark Review", on_click=self.toggle_review),
                    ft.TextButton("Next", on_click=lambda e: self.load_question(self.current_q_idx + 1))
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            self.nav_index_row,
            ft.ElevatedButton(
                "Submit Quiz Paper",
                width=300,
                bgcolor=ft.colors.EMERALD_500,
                color=ft.colors.WHITE,
                on_click=self.submit_quiz_action
            )
        ])

    def load_question(self, index):
        if index < 0 or index >= len(self.quiz_questions):
            return
            
        self.save_input()
        self.current_q_idx = index
        q = self.quiz_questions[index]
        
        # Load labels
        self.question_label.value = f"Question {index + 1}: {q.get('question_text')}"
        
        # Render navigators
        self.nav_index_row.controls.clear()
        for idx in range(len(self.quiz_questions)):
            color = ft.colors.INDIGO_600 if idx == index else ft.colors.RED_500 if idx in self.marked_for_review else ft.colors.GREY_800 if idx in self.user_answers else ft.colors.GREY_900
            self.nav_index_row.controls.append(
                ft.Container(
                    content=ft.Text(str(idx + 1), size=10, weight=ft.FontWeight.BOLD),
                    bgcolor=color,
                    width=28,
                    height=28,
                    border_radius=6,
                    alignment=ft.alignment.center,
                    on_click=lambda e, i=idx: self.load_question(i)
                )
            )
            
        # Display answers panel
        q_type = q.get("question_type", "mcq")
        if q_type == "mcq" or q_type == "tf":
            self.options_group.visible = True
            self.fill_input.visible = False
            
            # Load radio buttons options
            self.options_group.content.controls.clear()
            for opt in q.get("options", []):
                self.options_group.content.controls.append(
                    ft.Radio(value=opt, label=opt)
                )
            self.options_group.value = self.user_answers.get(index, None)
        else:
            self.options_group.visible = False
            self.fill_input.visible = True
            self.fill_input.value = self.user_answers.get(index, "")
            
        self.page.update()

    def save_input(self):
        if not self.quiz_questions or self.current_q_idx >= len(self.quiz_questions):
            return
            
        q = self.quiz_questions[self.current_q_idx]
        q_type = q.get("question_type", "mcq")
        if q_type == "mcq" or q_type == "tf":
            if self.options_group.value:
                self.user_answers[self.current_q_idx] = self.options_group.value
        else:
            text = self.fill_input.value.strip()
            if text:
                self.user_answers[self.current_q_idx] = text

    def toggle_review(self, e):
        if self.current_q_idx in self.marked_for_review:
            self.marked_for_review.remove(self.current_q_idx)
        else:
            self.marked_for_review.add(self.current_q_idx)
        self.load_question(self.current_q_idx)

    def submit_quiz_action(self, e):
        self.timer_active = False
        self.save_input()
        
        # Loader
        self.main_container.content = ft.Column([ft.ProgressRing(), ft.Text("Scoring results...")], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.page.update()
        
        db = SessionLocal()
        try:
            db_quiz = Quiz(title=self.quiz_title_label.value, difficulty=self.diff_dropdown.value)
            db.add(db_quiz)
            db.commit()
            db.refresh(db_quiz)
            
            correct_count = 0
            total = len(self.quiz_questions)
            
            report_controls = []
            
            for idx, q in enumerate(self.quiz_questions):
                user_ans = self.user_answers.get(idx, "[Unanswered]").strip().lower()
                corr_ans = q.get("correct_answer", "").strip().lower()
                is_correct = user_ans == corr_ans
                
                if is_correct:
                    correct_count += 1
                    
                color = ft.colors.GREEN_400 if is_correct else ft.colors.RED_400
                icon = ft.icons.CHECK_CIRCLE_ROUNDED if is_correct else ft.icons.CANCEL_ROUNDED
                
                report_controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row([ft.Icon(icon, color=color, size=16), ft.Text(f"Q{idx + 1}: {q.get('question_text')}", size=12, weight=ft.FontWeight.BOLD)], spacing=6),
                                ft.Text(f"Your Ans: {self.user_answers.get(idx, '[Unanswered]')} | Correct: {q.get('correct_answer')}", size=11, color=ft.colors.GREY_350),
                                ft.Text(f"Explanation: {q.get('explanation')}", size=11, color=ft.colors.GREY_400)
                            ],
                            spacing=3
                        ),
                        bgcolor=ft.colors.with_opacity(0.05, color),
                        padding=10,
                        border_radius=10,
                        border=ft.border.all(1, ft.colors.with_opacity(0.1, color))
                    )
                )
                
            # Log results in DB
            xp_reward = correct_count * 15
            ProgressService.award_xp(self.user["id"], xp_reward)
            
            q_res = QuizResult(
                user_id=self.user["id"],
                quiz_id=db_quiz.id,
                score=correct_count,
                total_questions=total,
                details_json=str(self.user_answers)
            )
            db.add(q_res)
            db.commit()
            
            self.report_panel.controls.clear()
            self.report_panel.controls.extend([
                ft.Text("Quiz Evaluation Completed! 📊", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.EMERALD_400),
                ft.Text(f"Score: {correct_count}/{total} ({round((correct_count/total)*100, 1)}%) — Reward: +{xp_reward} XP! 🎉", size=13, weight=ft.FontWeight.BOLD),
                ft.Column(report_controls, spacing=8),
                ft.ElevatedButton("Back to Arena", on_click=self.reset_to_generator, bgcolor=ft.colors.GREY_800, color=ft.colors.WHITE)
            ])
            self.main_container.content = self.report_panel
        except Exception as e:
            self.main_container.content = self.generator_panel
            self.show_snack(f"Submission Error: {str(e)}")
        finally:
            db.close()
            self.page.update()

    def reset_to_generator(self, e):
        self.main_container.content = self.generator_panel
        self.page.update()

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        return self.main_container
