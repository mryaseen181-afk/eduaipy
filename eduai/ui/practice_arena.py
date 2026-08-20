import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, 
    QSpinBox, QPushButton, QStackedWidget, QRadioButton, QButtonGroup, 
    QMessageBox, QLineEdit, QListWidget, QListWidgetItem, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from eduai.services.ai_service import AIService
from eduai.services.progress_service import ProgressService
from eduai.database.connection import SessionLocal
from eduai.database.models import Course, Quiz, Question, QuestionType, QuizResult

class PracticeArena(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        
        # State variables
        self.quiz_questions = []
        self.current_q_idx = 0
        self.user_answers = {}  # index -> selected answer string
        self.marked_for_review = set() # set of question indices
        
        # Exam timer state
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_timer)
        self.remaining_seconds = 0
        self.is_exam_mode = False

        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # View 1: Main Quiz Generator & Mode selection
        self.init_generator_view()
        # View 2: Active Test Panel
        self.init_test_view()
        # View 3: Score & Detailed Analysis Report
        self.init_report_view()
        
        self.stack.addWidget(self.gen_widget)
        self.stack.addWidget(self.test_widget)
        self.stack.addWidget(self.report_widget)

    def init_generator_view(self):
        self.gen_widget = QWidget()
        layout = QVBoxLayout(self.gen_widget)
        
        header = QLabel("🎯 StudyFlow Practice Arena")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        sub = QLabel("Select parameters to generate custom AI practice quizzes or load Timed Prep Exams.")
        sub.setObjectName("Subtitle")
        layout.addWidget(sub)
        
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel("<b>Subject:</b>"))
        self.subject_box = QComboBox()
        self.subject_box.addItems(["Mathematics", "Physics", "Chemistry", "Biology"])
        form_layout.addWidget(self.subject_box)
        
        form_layout.addWidget(QLabel("<b>Chapter / Topic:</b>"))
        self.chapter_input = QLineEdit()
        self.chapter_input.setPlaceholderText("e.g. Newton's Laws, Quadratic Equations...")
        form_layout.addWidget(self.chapter_input)
        
        form_layout.addWidget(QLabel("<b>Difficulty:</b>"))
        self.diff_box = QComboBox()
        self.diff_box.addItems(["Easy", "Medium", "Hard"])
        form_layout.addWidget(self.diff_box)
        
        form_layout.addWidget(QLabel("<b>Number of Questions:</b>"))
        self.num_spin = QSpinBox()
        self.num_spin.setRange(2, 20)
        self.num_spin.setValue(5)
        form_layout.addWidget(self.num_spin)
        
        layout.addWidget(form_frame)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        ai_quiz_btn = QPushButton("Generate AI Practice Quiz")
        ai_quiz_btn.setObjectName("Primary")
        ai_quiz_btn.clicked.connect(lambda: self.start_quiz_session(exam_mode=False))
        
        exam_btn = QPushButton("Start Timed Exam Mode ⏱️")
        exam_btn.setStyleSheet("background-color: #e11d48; color: white; font-weight: bold; border-radius: 8px; padding: 10px;")
        exam_btn.clicked.connect(lambda: self.start_quiz_session(exam_mode=True))
        
        btn_layout.addWidget(ai_quiz_btn)
        btn_layout.addWidget(exam_btn)
        layout.addLayout(btn_layout)

    def init_test_view(self):
        self.test_widget = QWidget()
        layout = QVBoxLayout(self.test_widget)
        
        # Test Header Info
        header_row = QHBoxLayout()
        self.test_title_lbl = QLabel("Active Quiz Session")
        self.test_title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #6366f1;")
        
        self.test_timer_lbl = QLabel("Timer: --:--")
        self.test_timer_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #e11d48;")
        
        header_row.addWidget(self.test_title_lbl)
        header_row.addWidget(self.test_timer_lbl, alignment=Qt.AlignRight)
        layout.addLayout(header_row)
        
        # Question Display Card
        self.q_card = QFrame()
        self.q_card.setObjectName("Card")
        self.q_layout = QVBoxLayout(self.q_card)
        
        self.q_text = QLabel("Question content goes here...")
        self.q_text.setWordWrap(True)
        self.q_text.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.q_layout.addWidget(self.q_text)
        
        # Multiple Choice Options or Text inputs stack
        self.options_container = QWidget()
        self.options_layout = QVBoxLayout(self.options_container)
        self.q_layout.addWidget(self.options_container)
        
        # Fill in blank field
        self.fill_blank_input = QLineEdit()
        self.fill_blank_input.setPlaceholderText("Type your answer here...")
        self.q_layout.addWidget(self.fill_blank_input)
        
        layout.addWidget(self.q_card)
        
        # Navigation controls
        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.load_prev_question)
        
        self.review_btn = QPushButton("Mark for Review")
        self.review_btn.clicked.connect(self.toggle_review_flag)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.load_next_question)
        
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.review_btn)
        nav_row.addWidget(self.next_btn)
        layout.addLayout(nav_row)
        
        # Navigator index layout (e.g. 1 2 3 4 5)
        self.index_container = QWidget()
        self.index_layout = QHBoxLayout(self.index_container)
        layout.addWidget(self.index_container)
        
        # Submit Button
        self.submit_btn = QPushButton("Submit Exam Paper")
        self.submit_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 10px;")
        self.submit_btn.clicked.connect(self.submit_quiz)
        layout.addWidget(self.submit_btn)

    def init_report_view(self):
        self.report_widget = QWidget()
        layout = QVBoxLayout(self.report_widget)
        
        header = QLabel("📊 Performance Scorecard")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        self.score_lbl = QLabel("Score: 0/0 (0%)")
        self.score_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        layout.addWidget(self.score_lbl)
        
        # Detailed feedback text
        self.feedback_display = QListWidget()
        layout.addWidget(self.feedback_display)
        
        # Actions
        btn_layout = QHBoxLayout()
        retry_btn = QPushButton("Back to Arena")
        retry_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_layout.addWidget(retry_btn)
        
        layout.addLayout(btn_layout)

    def start_quiz_session(self, exam_mode=False):
        subject = self.subject_box.currentText()
        chapter = self.chapter_input.text().strip()
        diff = self.diff_box.currentText()
        num_q = self.num_spin.value()
        
        if not chapter:
            chapter = "General Core Mechanics"
            
        # UI prompt loading
        self.test_title_lbl.setText(f"AI Quiz: {chapter} ({diff})")
        
        # Clear states
        self.quiz_questions = []
        self.user_answers = {}
        self.marked_for_review.clear()
        self.current_q_idx = 0
        
        # Fetch from AI Service
        try:
            self.quiz_questions = AIService.generate_ai_quiz(subject, chapter, diff, num_q)
        except Exception as e:
            QMessageBox.critical(self, "Quiz Error", f"Failed to generate quiz: {str(e)}")
            return
            
        self.is_exam_mode = exam_mode
        if self.is_exam_mode:
            # 1.5 minutes per question
            self.remaining_seconds = int(num_q * 1.5 * 60)
            self.update_timer_label()
            self.timer.start(1000)
            self.test_timer_lbl.show()
        else:
            self.timer.stop()
            self.test_timer_lbl.hide()
            
        self.stack.setCurrentIndex(1)
        self.setup_navigator_index()
        self.load_question(0)

    def tick_timer(self):
        if self.remaining_seconds <= 0:
            self.timer.stop()
            QMessageBox.warning(self, "Timeout", "Time is up! Your quiz will be submitted automatically.")
            self.submit_quiz()
        else:
            self.remaining_seconds -= 1
            self.update_timer_label()

    def update_timer_label(self):
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.test_timer_lbl.setText(f"Time Remaining: {mins:02d}:{secs:02d}")

    def setup_navigator_index(self):
        # Clear layouts
        while self.index_layout.count():
            item = self.index_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for idx in range(len(self.quiz_questions)):
            btn = QPushButton(str(idx + 1))
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked=False, i=idx: self.load_question(i))
            self.index_layout.addWidget(btn)

    def load_question(self, index):
        # Save active input response from previous question
        self.save_active_response()
        
        self.current_q_idx = index
        q = self.quiz_questions[index]
        
        # Highlight active index button
        for i in range(self.index_layout.count()):
            btn = self.index_layout.itemAt(i).widget()
            if btn:
                # Styles
                style = ""
                if i == index:
                    style = "background-color: #6366f1; color: white;"
                elif i in self.marked_for_review:
                    style = "background-color: #e11d48; color: white;"
                elif i in self.user_answers:
                    style = "background-color: #475569; color: white;"
                btn.setStyleSheet(style)
                
        self.q_text.setText(f"<b>Question {index + 1}:</b> {q.get('question_text')}")
        
        # Clear options layout
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        q_type = q.get("question_type", "mcq")
        
        if q_type == "mcq" or q_type == "tf":
            self.options_container.show()
            self.fill_blank_input.hide()
            
            self.opt_button_group = QButtonGroup(self)
            opts = q.get("options", [])
            for opt_val in opts:
                rb = QRadioButton(opt_val)
                self.opt_button_group.addButton(rb)
                self.options_layout.addWidget(rb)
                
                # Pre-select if answered before
                if self.user_answers.get(index) == opt_val:
                    rb.setChecked(True)
        else:
            # Fill in blank
            self.options_container.hide()
            self.fill_blank_input.show()
            self.fill_blank_input.setText(self.user_answers.get(index, ""))
            
        # Review button title
        self.review_btn.setText("Remove Review Flag" if index in self.marked_for_review else "Mark for Review")

    def save_active_response(self):
        if not self.quiz_questions or self.current_q_idx >= len(self.quiz_questions):
            return
            
        q = self.quiz_questions[self.current_q_idx]
        q_type = q.get("question_type", "mcq")
        
        if q_type == "mcq" or q_type == "tf":
            selected = self.opt_button_group.checkedButton()
            if selected:
                self.user_answers[self.current_q_idx] = selected.text()
        else:
            text = self.fill_blank_input.text().strip()
            if text:
                self.user_answers[self.current_q_idx] = text

    def load_prev_question(self):
        if self.current_q_idx > 0:
            self.load_question(self.current_q_idx - 1)

    def load_next_question(self):
        if self.current_q_idx < len(self.quiz_questions) - 1:
            self.load_question(self.current_q_idx + 1)

    def toggle_review_flag(self):
        if self.current_q_idx in self.marked_for_review:
            self.marked_for_review.remove(self.current_q_idx)
        else:
            self.marked_for_review.add(self.current_q_idx)
        self.load_question(self.current_q_idx)

    def submit_quiz(self):
        self.timer.stop()
        self.save_active_response()
        
        # Calculate scores
        correct_count = 0
        total = len(self.quiz_questions)
        
        self.feedback_display.clear()
        
        # Generate new DB entry for Quiz record
        db = SessionLocal()
        try:
            # Create a mock database Quiz mapping if topic exists
            db_quiz = Quiz(title=self.test_title_lbl.text(), difficulty=self.diff_box.currentText())
            db.add(db_quiz)
            db.commit()
            db.refresh(db_quiz)
            
            explanation_txt_list = []
            
            for idx, q in enumerate(self.quiz_questions):
                user_ans = self.user_answers.get(idx, "[Unanswered]")
                corr_ans = q.get("correct_answer")
                is_correct = str(user_ans).strip().lower() == str(corr_ans).strip().lower()
                
                if is_correct:
                    correct_count += 1
                
                feedback_str = (
                    f"Q{idx + 1}: {q.get('question_text')}\n"
                    f"Your Answer: {user_ans} | Correct: {corr_ans}\n"
                    f"Explanation: {q.get('explanation')}\n"
                )
                explanation_txt_list.append(feedback_str)
                
                item = QListWidgetItem()
                prefix = "✅" if is_correct else "❌"
                item.setText(f"{prefix} Q{idx + 1}: {q.get('question_text')}\n   Your answer: {user_ans} (Correct: {corr_ans})\n   Explanation: {q.get('explanation')}")
                self.feedback_display.addItem(item)
                
            # Log results in DB
            pct = (correct_count / total) * 100 if total > 0 else 0
            
            q_res = QuizResult(
                user_id=self.user['id'],
                quiz_id=db_quiz.id,
                score=correct_count,
                total_questions=total,
                details_json=json.dumps(self.user_answers)
            )
            db.add(q_res)
            
            # Award XP: 15 XP per correct answer
            xp_reward = correct_count * 15
            ProgressService.award_xp(self.user['id'], xp_reward)
            
            db.commit()
            
            self.score_lbl.setText(f"Score: {correct_count}/{total} ({round(pct, 1)}%) — Reward: +{xp_reward} XP! 🎉")
            self.stack.setCurrentIndex(2)
        except Exception as e:
            QMessageBox.critical(self, "Submit Error", f"Could not record quiz results: {str(e)}")
            db.rollback()
        finally:
            db.close()
