import datetime
import enum
import json
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, Enum, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserRole(enum.Enum):
    STUDENT = "student"
    EDUCATOR = "educator"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak_count = Column(Integer, default=1)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    profile_pic = Column(String(100), default="default_avatar.png")

    # Relationships
    quiz_results = relationship("QuizResult", back_populates="student", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="student", cascade="all, delete-orphan")
    user_notes = relationship("UserNote", back_populates="student", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="student", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    class_level = Column(String(20), nullable=False)
    subject = Column(String(50), nullable=False)
    educator_id = Column(Integer, ForeignKey("users.id"))
    
    chapters = relationship("Chapter", back_populates="course", order_by="Chapter.order_index", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=1)

    course = relationship("Course", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter", cascade="all, delete-orphan")

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    title = Column(String(100), nullable=False)
    content_notes = Column(Text)
    video_path = Column(String(255))
    image_path = Column(String(255))
    pdf_path = Column(String(255))

    chapter = relationship("Chapter", back_populates="topics")
    quizzes = relationship("Quiz", back_populates="topic", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="topic", cascade="all, delete-orphan")
    user_notes = relationship("UserNote", back_populates="topic", cascade="all, delete-orphan")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True) # AI generated or generic
    title = Column(String(100), nullable=False)
    difficulty = Column(String(20), default="Medium") # Easy, Medium, Hard
    time_limit = Column(Integer, default=0) # in minutes, 0 means no limit

    topic = relationship("Topic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

class QuestionType(enum.Enum):
    MCQ = "mcq"
    TF = "tf"
    FILL_IN = "fill_in"
    SHORT_ANSWER = "short_answer"

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.MCQ, nullable=False)
    options_json = Column(Text) # JSON string of options for MCQ e.g., ["A", "B", "C", "D"]
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text)

    quiz = relationship("Quiz", back_populates="questions")

class QuizResult(Base):
    __tablename__ = "quiz_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, nullable=False) # raw score
    total_questions = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)
    details_json = Column(Text) # JSON mapping question id to user choice, correctness

    student = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz")

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    time_spent = Column(Integer, default=0) # in seconds
    date = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("User", back_populates="study_sessions")
    topic = relationship("Topic", back_populates="study_sessions")

class UserNote(Base):
    __tablename__ = "user_notes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    bookmarked = Column(Boolean, default=False)
    highlights_json = Column(Text, default="[]") # JSON string containing pairs: [[start_idx, end_idx], ...]
    personal_notes = Column(Text)
    is_completed = Column(Boolean, default=False)

    student = relationship("User", back_populates="user_notes")
    topic = relationship("Topic", back_populates="user_notes")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String(100), nullable=False)
    description = Column(String(255))
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("User", back_populates="achievements")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String(50), default="general") # announcement, assignment, goal, streak

    user = relationship("User", back_populates="notifications")
