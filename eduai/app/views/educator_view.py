import flet as ft
from eduai.database.connection import SessionLocal
from eduai.database.models import Course, Chapter, Topic, User, UserRole, Quiz, Question, QuestionType

class EducatorView(ft.Container):
    def __init__(self, user, page: ft.Page):
        super().__init__()
        self.user = user
        self.page = page
        self.expand = True
        
        # UI dropdown options fields
        self.c_title = ft.TextField(label="Course Title", placeholder="e.g. Thermodynamics, Linear Algebra")
        self.c_class = ft.Dropdown(
            label="Target Class Level",
            options=[ft.dropdown.Option("Class 9"), ft.dropdown.Option("Class 10"), ft.dropdown.Option("Class 11"), ft.dropdown.Option("Class 12")],
            value="Class 10"
        )
        self.c_sub = ft.Dropdown(
            label="Subject Category",
            options=[ft.dropdown.Option("Mathematics"), ft.dropdown.Option("Physics"), ft.dropdown.Option("Chemistry"), ft.dropdown.Option("Biology")],
            value="Mathematics"
        )
        self.c_desc = ft.TextField(label="Course Summary / Description", multiline=True, min_lines=2, max_lines=4)
        
        # Lesson fields
        self.l_course_dropdown = ft.Dropdown(label="Select Target Course")
        self.l_chapter = ft.TextField(label="Chapter Name")
        self.l_topic = ft.TextField(label="Topic Name")
        self.l_notes = ft.TextField(label="Lesson Study Notes (HTML/Markdown allowed)", multiline=True, min_lines=3, max_lines=6)
        
        # Question fields
        self.q_topic_dropdown = ft.Dropdown(label="Select Lesson/Topic")
        self.q_text = ft.TextField(label="Question Text Prompt")
        self.q_type = ft.Dropdown(
            label="Question Type",
            options=[ft.dropdown.Option("mcq", "Multiple Choice (MCQ)"), ft.dropdown.Option("tf", "True / False")],
            value="mcq",
            on_change=self.toggle_mcq_fields
        )
        self.opt_a = ft.TextField(label="Option A")
        self.opt_b = ft.TextField(label="Option B")
        self.opt_c = ft.TextField(label="Option C")
        self.opt_d = ft.TextField(label="Option D")
        
        self.q_ans = ft.TextField(label="Correct Answer")
        self.q_exp = ft.TextField(label="Answer Correction Detail / Explanation")
        
        self.mcq_fields_col = ft.Column([self.opt_a, self.opt_b, self.opt_c, self.opt_d], spacing=5)

        # Student data grid table
        self.students_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("XP Score")),
                ft.DataColumn(ft.Text("Scholar Level")),
            ],
            rows=[]
        )

        self.refresh_selectors()
        self.content = self.build_layout()

    def refresh_selectors(self):
        db = SessionLocal()
        try:
            # Load Courses selector dropdown
            self.l_course_dropdown.options.clear()
            courses = db.query(Course).all()
            for c in courses:
                self.l_course_dropdown.options.append(ft.dropdown.Option(str(c.id), f"{c.title} ({c.class_level})"))
            if courses:
                self.l_course_dropdown.value = str(courses[0].id)
                
            # Load Topics selector dropdown
            self.q_topic_dropdown.options.clear()
            topics = db.query(Topic).all()
            for t in topics:
                self.q_topic_dropdown.options.append(ft.dropdown.Option(str(t.id), f"{t.title} ({t.chapter.course.title})"))
            if topics:
                self.q_topic_dropdown.value = str(topics[0].id)
        finally:
            db.close()

    def toggle_mcq_fields(self, e):
        self.mcq_fields_col.visible = self.q_type.value == "mcq"
        self.page.update()

    def create_course(self, e):
        title = self.c_title.value.strip()
        desc = self.c_desc.value.strip()
        cl = self.c_class.value
        sub = self.c_sub.value
        
        if not title or not desc:
            self.show_snack("All course columns are required.")
            return
            
        db = SessionLocal()
        try:
            c = Course(title=title, description=desc, class_level=cl, subject=sub, educator_id=self.user["id"])
            db.add(c)
            db.commit()
            self.show_snack(f"Published Course Syllabus: '{title}'")
            self.c_title.value = ""
            self.c_desc.value = ""
            self.refresh_selectors()
            self.page.update()
        except Exception as e:
            self.show_snack(f"Failed to create course: {e}")
            db.rollback()
        finally:
            db.close()

    def create_lesson(self, e):
        course_id = int(self.l_course_dropdown.value)
        chap_name = self.l_chapter.value.strip()
        topic_name = self.l_topic.value.strip()
        notes = self.l_notes.value.strip()
        
        if not course_id or not chap_name or not topic_name or not notes:
            self.show_snack("All lesson columns are required.")
            return
            
        db = SessionLocal()
        try:
            # Find/create Chapter
            chap = db.query(Chapter).filter(Chapter.course_id == course_id, Chapter.title == chap_name).first()
            if not chap:
                from sqlalchemy import func
                max_order = db.query(func.max(Chapter.order_index)).filter(Chapter.course_id == course_id).scalar() or 0
                chap = Chapter(course_id=course_id, title=chap_name, order_index=max_order + 1)
                db.add(chap)
                db.commit()
                db.refresh(chap)
                
            topic = Topic(chapter_id=chap.id, title=topic_name, content_notes=notes)
            db.add(topic)
            db.commit()
            
            self.show_snack(f"Lesson notes '{topic_name}' added to chapter!")
            self.l_topic.value = ""
            self.l_notes.value = ""
            self.refresh_selectors()
            self.page.update()
        except Exception as e:
            self.show_snack(f"Failed to publish lesson: {e}")
            db.rollback()
        finally:
            db.close()

    def create_question(self, e):
        topic_id = int(self.q_topic_dropdown.value)
        q_txt = self.q_text.value.strip()
        q_type_val = self.q_type.value
        ans = self.q_ans.value.strip()
        exp = self.q_exp.value.strip()
        
        if not topic_id or not q_txt or not ans:
            self.show_snack("Topic, question prompt, and correct answer are required.")
            return
            
        db = SessionLocal()
        try:
            quiz = db.query(Quiz).filter(Quiz.topic_id == topic_id).first()
            if not quiz:
                topic = db.query(Topic).filter(Topic.id == topic_id).first()
                quiz = Quiz(topic_id=topic_id, title=f"{topic.title} Study Quiz", difficulty="Medium")
                db.add(quiz)
                db.commit()
                db.refresh(quiz)
                
            import json
            opts = []
            if q_type_val == "mcq":
                opts = [self.opt_a.value.strip(), self.opt_b.value.strip(), self.opt_c.value.strip(), self.opt_d.value.strip()]
                if not all(opts):
                    self.show_snack("All four MCQ options are required.")
                    return
            else:
                opts = ["True", "False"]
                
            q = Question(
                quiz_id=quiz.id,
                question_text=q_txt,
                question_type=QuestionType.MCQ if q_type_val == "mcq" else QuestionType.TF,
                options_json=json.dumps(opts),
                correct_answer=ans,
                explanation=exp
            )
            db.add(q)
            db.commit()
            
            self.show_snack("Question saved to topic quiz!")
            self.q_text.value = ""
            self.q_ans.value = ""
            self.q_exp.value = ""
            self.opt_a.value = ""
            self.opt_b.value = ""
            self.opt_c.value = ""
            self.opt_d.value = ""
            self.page.update()
        except Exception as e:
            self.show_snack(f"Failed to add question: {e}")
            db.rollback()
        finally:
            db.close()

    def load_student_data(self):
        self.students_table.rows.clear()
        db = SessionLocal()
        try:
            students = db.query(User).filter(User.role == UserRole.STUDENT).all()
            for s in students:
                self.students_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(s.id), font_family="Consolas")),
                            ft.DataCell(ft.Text(s.username, weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(str(s.xp))),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(f"Lvl {s.level}", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.EMERALD_400),
                                    bgcolor=ft.colors.with_opacity(0.1, ft.colors.EMERALD_400),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=4
                                )
                            )
                        ]
                    )
                )
        finally:
            db.close()

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def build_layout(self):
        self.load_student_data()
        
        # Tabs for management
        return ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(
                    text="Course Builder",
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Create Syllabus Outlines", size=14, weight=ft.FontWeight.BOLD),
                                self.c_title,
                                self.c_class,
                                self.c_sub,
                                self.c_desc,
                                ft.ElevatedButton("Publish Course", bgcolor=ft.colors.INDIGO_500, color=ft.colors.WHITE, on_click=self.create_course)
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.ADAPTIVE
                        ),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Add Lessons",
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Upload Lesson study notes", size=14, weight=ft.FontWeight.BOLD),
                                self.l_course_dropdown,
                                self.l_chapter,
                                self.l_topic,
                                self.l_notes,
                                ft.ElevatedButton("Publish Lesson Notes", bgcolor=ft.colors.INDIGO_500, color=ft.colors.WHITE, on_click=self.create_lesson)
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.ADAPTIVE
                        ),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Add Quizzes",
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Add Quiz Questions", size=14, weight=ft.FontWeight.BOLD),
                                self.q_topic_dropdown,
                                self.q_text,
                                self.q_type,
                                self.mcq_fields_col,
                                self.q_ans,
                                self.q_exp,
                                ft.ElevatedButton("Save Question", bgcolor=ft.colors.INDIGO_500, color=ft.colors.WHITE, on_click=self.create_question)
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.ADAPTIVE
                        ),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Student Stats",
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Student registries summary", size=14, weight=ft.FontWeight.BOLD),
                                self.students_table
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.ADAPTIVE
                        ),
                        padding=10
                    )
                )
            ],
            expand=True
        )
