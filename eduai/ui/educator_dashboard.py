from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QComboBox, QFrame, QScrollArea, QTableWidget, 
    QTableWidgetItem, QMessageBox, QTabWidget, QListWidget
)
from PySide6.QtCore import Qt
from eduai.database.connection import SessionLocal
from eduai.database.models import Course, Chapter, Topic, User, UserRole, Quiz, Question, QuestionType

class EducatorDashboard(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        header = QLabel(f"Educator Dashboard — Welcome, {self.user['username']}! 🎓")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        main_layout.addWidget(header)
        
        # Tabs for management
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.init_course_tab()
        self.init_lesson_tab()
        self.init_quiz_tab()
        self.init_students_tab()
        
        self.tabs.addTab(self.course_widget, "Course Builder")
        self.tabs.addTab(self.lesson_widget, "Add Lessons")
        self.tabs.addTab(self.quiz_widget, "Add Quizzes")
        self.tabs.addTab(self.students_widget, "Student Statistics")

    def init_course_tab(self):
        self.course_widget = QWidget()
        layout = QVBoxLayout(self.course_widget)
        
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        form_layout = QVBoxLayout(form_frame)
        form_layout.addWidget(QLabel("<b>Create and Publish a New Course Syllabus</b>"))
        
        self.c_title = QLineEdit()
        self.c_title.setPlaceholderText("e.g. Mechanics in Physics, Trigonometry Foundations")
        form_layout.addWidget(QLabel("Course Title:"))
        form_layout.addWidget(self.c_title)
        
        self.c_class = QComboBox()
        self.c_class.addItems(["Class 9", "Class 10", "Class 11", "Class 12"])
        form_layout.addWidget(QLabel("Target Class level:"))
        form_layout.addWidget(self.c_class)
        
        self.c_sub = QComboBox()
        self.c_sub.addItems(["Mathematics", "Physics", "Chemistry", "Biology"])
        form_layout.addWidget(QLabel("Subject Category:"))
        form_layout.addWidget(self.c_sub)
        
        self.c_desc = QTextEdit()
        self.c_desc.setPlaceholderText("Write details about target metrics and chapters...")
        self.c_desc.setFixedHeight(120)
        form_layout.addWidget(QLabel("Course Description:"))
        form_layout.addWidget(self.c_desc)
        
        pub_btn = QPushButton("Publish Course Syllabus")
        pub_btn.setObjectName("Primary")
        pub_btn.clicked.connect(self.create_course)
        form_layout.addWidget(pub_btn)
        
        layout.addWidget(form_frame)

    def init_lesson_tab(self):
        self.lesson_widget = QWidget()
        layout = QVBoxLayout(self.lesson_widget)
        
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        form_layout = QVBoxLayout(form_frame)
        form_layout.addWidget(QLabel("<b>Upload Lessons / Study Notes to Existing Syllabus</b>"))
        
        self.l_course_box = QComboBox()
        form_layout.addWidget(QLabel("Select Target Course:"))
        form_layout.addWidget(self.l_course_box)
        
        self.l_chap_title = QLineEdit()
        self.l_chap_title.setPlaceholderText("e.g. Chapter 1: Introduction to Calculus")
        form_layout.addWidget(QLabel("Chapter Name (Created if not exists):"))
        form_layout.addWidget(self.l_chap_title)
        
        self.l_topic_title = QLineEdit()
        self.l_topic_title.setPlaceholderText("e.g. Limits and Continuity")
        form_layout.addWidget(QLabel("Topic / Lesson Name:"))
        form_layout.addWidget(self.l_topic_title)
        
        self.l_content = QTextEdit()
        self.l_content.setPlaceholderText("Write core study notes and material details...")
        self.l_content.setFixedHeight(150)
        form_layout.addWidget(QLabel("Lesson Study Notes (HTML/Markdown allowed):"))
        form_layout.addWidget(self.l_content)
        
        pub_btn = QPushButton("Publish Topic Lesson Notes")
        pub_btn.setObjectName("Primary")
        pub_btn.clicked.connect(self.create_lesson)
        form_layout.addWidget(pub_btn)
        
        layout.addWidget(form_frame)
        self.tabs.currentChanged.connect(self.refresh_dropdowns)

    def init_quiz_tab(self):
        self.quiz_widget = QWidget()
        layout = QVBoxLayout(self.quiz_widget)
        
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        form_layout = QVBoxLayout(form_frame)
        form_layout.addWidget(QLabel("<b>Add Practice Questions to Topic Syllabi</b>"))
        
        self.q_topic_box = QComboBox()
        form_layout.addWidget(QLabel("Select Lesson/Topic:"))
        form_layout.addWidget(self.q_topic_box)
        
        self.q_text = QLineEdit()
        self.q_text.setPlaceholderText("Write quiz question prompt...")
        form_layout.addWidget(QLabel("Question text:"))
        form_layout.addWidget(self.q_text)
        
        self.q_type = QComboBox()
        self.q_type.addItems(["Multiple Choice (MCQ)", "True / False"])
        self.q_type.currentIndexChanged.connect(self.toggle_mcq_opts)
        form_layout.addWidget(QLabel("Question Type:"))
        form_layout.addWidget(self.q_type)
        
        # MCQ options frame
        self.opts_frame = QFrame()
        opts_layout = QVBoxLayout(self.opts_frame)
        opts_layout.setContentsMargins(0, 0, 0, 0)
        self.opt_a = QLineEdit()
        self.opt_a.setPlaceholderText("Option A")
        self.opt_b = QLineEdit()
        self.opt_b.setPlaceholderText("Option B")
        self.opt_c = QLineEdit()
        self.opt_c.setPlaceholderText("Option C")
        self.opt_d = QLineEdit()
        self.opt_d.setPlaceholderText("Option D")
        opts_layout.addWidget(self.opt_a)
        opts_layout.addWidget(self.opt_b)
        opts_layout.addWidget(self.opt_c)
        opts_layout.addWidget(self.opt_d)
        form_layout.addWidget(self.opts_frame)
        
        self.q_ans = QLineEdit()
        self.q_ans.setPlaceholderText("Type correct answer exactly matching option string...")
        form_layout.addWidget(QLabel("Correct answer:"))
        form_layout.addWidget(self.q_ans)
        
        self.q_exp = QLineEdit()
        self.q_exp.setPlaceholderText("Explain why this answer is correct...")
        form_layout.addWidget(QLabel("Answer explanation (Step-by-step summary):"))
        form_layout.addWidget(self.q_exp)
        
        pub_btn = QPushButton("Save Question to Topic Quiz")
        pub_btn.setObjectName("Primary")
        pub_btn.clicked.connect(self.create_question)
        form_layout.addWidget(pub_btn)
        
        layout.addWidget(form_frame)

    def init_students_tab(self):
        self.students_widget = QWidget()
        layout = QVBoxLayout(self.students_widget)
        
        layout.addWidget(QLabel("<b>Student Registry & Performance Overview</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Student ID", "Username", "XP score", "Scholar Level"])
        layout.addWidget(self.table)
        
        load_btn = QPushButton("Refresh Student Statistics")
        load_btn.clicked.connect(self.load_student_data)
        layout.addWidget(load_btn)
        
        self.load_student_data()

    def refresh_dropdowns(self, index):
        db = SessionLocal()
        try:
            # Refresh Courses
            self.l_course_box.clear()
            courses = db.query(Course).all()
            for c in courses:
                self.l_course_box.addItem(f"{c.id}: {c.title}", c.id)
                
            # Refresh Topics
            self.q_topic_box.clear()
            topics = db.query(Topic).all()
            for t in topics:
                self.q_topic_box.addItem(f"{t.id}: {t.title} (in {t.chapter.course.title})", t.id)
        finally:
            db.close()

    def toggle_mcq_opts(self, index):
        if index == 1:
            self.opts_frame.hide()
            self.q_ans.setPlaceholderText("Type True or False")
        else:
            self.opts_frame.show()
            self.q_ans.setPlaceholderText("Type correct answer exactly matching option string...")

    def create_course(self):
        t = self.c_title.text().strip()
        desc = self.c_desc.toPlainText().strip()
        cl = self.c_class.currentText()
        sub = self.c_sub.currentText()
        
        if not t or not desc:
            QMessageBox.warning(self, "Invalid Inputs", "Please fill in all course information.")
            return
            
        db = SessionLocal()
        try:
            c = Course(title=t, description=desc, class_level=cl, subject=sub, educator_id=self.user['id'])
            db.add(c)
            db.commit()
            QMessageBox.information(self, "Success", f"Course '{t}' published successfully!")
            self.c_title.clear()
            self.c_desc.clear()
            self.refresh_dropdowns(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create course: {e}")
            db.rollback()
        finally:
            db.close()

    def create_lesson(self):
        course_id = self.l_course_box.currentData()
        chap_name = self.l_chap_title.text().strip()
        topic_name = self.l_topic_title.text().strip()
        notes = self.l_content.toPlainText().strip()
        
        if not course_id or not chap_name or not topic_name or not notes:
            QMessageBox.warning(self, "Invalid Inputs", "Please complete all fields.")
            return
            
        db = SessionLocal()
        try:
            # Find or create Chapter
            chap = db.query(Chapter).filter(Chapter.course_id == course_id, Chapter.title == chap_name).first()
            if not chap:
                # Get max order_index
                from sqlalchemy import func
                max_order = db.query(func.max(Chapter.order_index)).filter(Chapter.course_id == course_id).scalar() or 0
                chap = Chapter(course_id=course_id, title=chap_name, order_index=max_order + 1)
                db.add(chap)
                db.commit()
                db.refresh(chap)
                
            topic = Topic(chapter_id=chap.id, title=topic_name, content_notes=notes)
            db.add(topic)
            db.commit()
            
            QMessageBox.information(self, "Success", f"Lesson '{topic_name}' added to Chapter '{chap_name}'!")
            self.l_topic_title.clear()
            self.l_content.clear()
            self.refresh_dropdowns(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add lesson: {e}")
            db.rollback()
        finally:
            db.close()

    def create_question(self):
        topic_id = self.q_topic_box.currentData()
        q_txt = self.q_text.text().strip()
        q_type_str = "mcq" if self.q_type.currentIndex() == 0 else "tf"
        ans = self.q_ans.text().strip()
        exp = self.q_exp.text().strip()
        
        if not topic_id or not q_txt or not ans:
            QMessageBox.warning(self, "Invalid Inputs", "Please enter target topic, question content, and correct answer.")
            return
            
        db = SessionLocal()
        try:
            # Find or create Quiz for this topic
            quiz = db.query(Quiz).filter(Quiz.topic_id == topic_id).first()
            if not quiz:
                topic = db.query(Topic).filter(Topic.id == topic_id).first()
                quiz = Quiz(topic_id=topic_id, title=f"{topic.title} Study Quiz", difficulty="Medium")
                db.add(quiz)
                db.commit()
                db.refresh(quiz)
                
            opts = []
            if q_type_str == "mcq":
                opts = [self.opt_a.text().strip(), self.opt_b.text().strip(), self.opt_c.text().strip(), self.opt_d.text().strip()]
                if not all(opts):
                    QMessageBox.warning(self, "Options Missing", "Please complete all four option inputs.")
                    return
            else:
                opts = ["True", "False"]
                
            q = Question(
                quiz_id=quiz.id,
                question_text=q_txt,
                question_type=QuestionType.MCQ if q_type_str == "mcq" else QuestionType.TF,
                options_json=json.dumps(opts),
                correct_answer=ans,
                explanation=exp
            )
            db.add(q)
            db.commit()
            QMessageBox.information(self, "Success", "Question successfully added to the study quiz!")
            self.q_text.clear()
            self.q_ans.clear()
            self.q_exp.clear()
            self.opt_a.clear()
            self.opt_b.clear()
            self.opt_c.clear()
            self.opt_d.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create question: {e}")
            db.rollback()
        finally:
            db.close()

    def load_student_data(self):
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            students = db.query(User).filter(User.role == UserRole.STUDENT).all()
            for r_idx, student in enumerate(students):
                self.table.insertRow(r_idx)
                self.table.setItem(r_idx, 0, QTableWidgetItem(str(student.id)))
                self.table.setItem(r_idx, 1, QTableWidgetItem(student.username))
                self.table.setItem(r_idx, 2, QTableWidgetItem(str(student.xp)))
                self.table.setItem(r_idx, 3, QTableWidgetItem(str(student.level)))
        finally:
            db.close()
