import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eduai.config import DATABASE_URL
from eduai.database.models import Base, Course, Chapter, Topic, User, UserRole, Quiz, Question, QuestionType

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if database is already seeded
        if db.query(Course).first() is None:
            # Seed a default Educator
            educator = db.query(User).filter(User.username == "teacher").first()
            if not educator:
                import bcrypt
                pwd_hash = bcrypt.hashpw("teacher123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                educator = User(
                    username="teacher",
                    email="teacher@eduai.com",
                    password_hash=pwd_hash,
                    role=UserRole.EDUCATOR,
                    xp=100
                )
                db.add(educator)
                db.commit()
                db.refresh(educator)

            # Seed a default Student
            student = db.query(User).filter(User.username == "student").first()
            if not student:
                import bcrypt
                pwd_hash = bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                student = User(
                    username="student",
                    email="student@eduai.com",
                    password_hash=pwd_hash,
                    role=UserRole.STUDENT,
                    xp=250,
                    level=3,
                    streak_count=5,
                    last_active=datetime.datetime.utcnow()
                )
                db.add(student)
                db.commit()
                db.refresh(student)

            # Seed Courses
            c1 = Course(title="Introduction to Algebra", description="Master basic algebraic variables and equations.", class_level="Class 9", subject="Mathematics", educator_id=educator.id)
            c2 = Course(title="Classical Mechanics", description="Learn about gravity, forces, and motion.", class_level="Class 10", subject="Physics", educator_id=educator.id)
            db.add_all([c1, c2])
            db.commit()

            # Seed Chapters
            ch1_1 = Chapter(course_id=c1.id, title="Linear Equations", description="Solving single-variable equations.", order_index=1)
            ch2_1 = Chapter(course_id=c2.id, title="Newton's Laws of Motion", description="Fundamentals of dynamics.", order_index=1)
            db.add_all([ch1_1, ch2_1])
            db.commit()

            # Seed Topics
            t1_1 = Topic(
                chapter_id=ch1_1.id,
                title="Solving for X",
                content_notes=(
                    "In Algebra, we solve for an unknown variable x.\n\n"
                    "**Key Principle**:\n"
                    "Whatever you do to one side of the equation, you must do to the other side to keep it balanced.\n\n"
                    "**Example**:\n"
                    "3x + 5 = 20\n"
                    "Subtract 5 from both sides:\n"
                    "3x = 15\n"
                    "Divide both sides by 3:\n"
                    "x = 5\n\n"
                    "Verify your answer by substituting x back into the original equation: 3(5) + 5 = 20."
                )
            )
            t2_1 = Topic(
                chapter_id=ch2_1.id,
                title="First Law of Motion (Inertia)",
                content_notes=(
                    "Newton's First Law states that an object at rest will remain at rest, and an object in motion "
                    "will continue in motion at a constant velocity, unless acted upon by a net external force.\n\n"
                    "**Inertia**:\n"
                    "This resistance to change in motion is called Inertia. Mass is a measure of inertia. "
                    "A heavier object has more inertia, making it harder to start or stop moving.\n\n"
                    "**Real-life Example**:\n"
                    "When a bus suddenly stops, the passengers jerk forward because their bodies want to keep moving."
                )
            )
            db.add_all([t1_1, t2_1])
            db.commit()

            # Seed Quizzes
            q1 = Quiz(topic_id=t1_1.id, title="Algebra Basics Quiz", difficulty="Easy", time_limit=5)
            q2 = Quiz(topic_id=t2_1.id, title="Newton's First Law Test", difficulty="Medium", time_limit=10)
            db.add_all([q1, q2])
            db.commit()

            # Seed Questions
            ques1 = Question(
                quiz_id=q1.id,
                question_text="Solve for x: 2x - 4 = 10",
                question_type=QuestionType.MCQ,
                options_json=json.dumps(["x = 5", "x = 7", "x = 3", "x = 14"]),
                correct_answer="x = 7",
                explanation="2x - 4 = 10 -> 2x = 14 -> x = 7."
            )
            ques2 = Question(
                quiz_id=q1.id,
                question_text="Algebra was first systematically studied in ancient Greece. (True or False)",
                question_type=QuestionType.TF,
                options_json=json.dumps(["True", "False"]),
                correct_answer="False",
                explanation="Algebra traces its roots back to ancient Babylon and later the Persian mathematician Al-Khwarizmi, who wrote the foundational book on algebra."
            )
            ques3 = Question(
                quiz_id=q2.id,
                question_text="What is another name for Newton's First Law of Motion?",
                question_type=QuestionType.MCQ,
                options_json=json.dumps(["Law of Acceleration", "Law of Action-Reaction", "Law of Inertia", "Law of Gravitation"]),
                correct_answer="Law of Inertia",
                explanation="The first law is commonly referred to as the Law of Inertia because inertia is the tendency of objects to resist changes to their state of motion."
            )
            db.add_all([ques1, ques2, ques3])
            db.commit()

    except Exception as e:
        print(f"Error seeding DB: {e}")
        db.rollback()
    finally:
        db.close()
