import os
import json
import datetime
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from eduai.database.connection import SessionLocal, init_db
from eduai.database.models import User, UserRole, Course, Chapter, Topic, Quiz, Question, QuestionType, QuizResult, UserNote, UserAchievement, Notification
from eduai.services.auth_service import AuthService
from eduai.services.ai_service import AIService
from eduai.services.progress_service import ProgressService

app = FastAPI(title="StudyFlow EduAI")

# Setup template engine
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# DB Session Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get current user helper
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "xp": user.xp,
        "level": user.level,
        "streak_count": user.streak_count
    }

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
def index(request: Request, user = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: str = Form(None),
    db: Session = Depends(get_db)
):
    user_data = AuthService.authenticate(username.strip(), password.strip())
    if user_data:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        # Keep cookie session
        max_age = 30 * 24 * 60 * 60 if remember_me else None  # 30 days if remember me
        response.set_cookie(key="user_id", value=str(user_data["id"]), max_age=max_age)
        return response
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.post("/register")
def register_action(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    role_enum = UserRole.STUDENT if role == "student" else UserRole.EDUCATOR
    success, msg = AuthService.register_user(username.strip(), email.strip(), password.strip(), role_enum)
    if success:
        return templates.TemplateResponse("login.html", {"request": request, "success": msg, "error": None})
    return templates.TemplateResponse("login.html", {"request": request, "error": msg})

@app.post("/reset")
def reset_action(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    new_password: str = Form(...)
):
    success, msg = AuthService.reset_password(username.strip(), email.strip(), new_password.strip())
    if success:
        return templates.TemplateResponse("login.html", {"request": request, "success": msg, "error": None})
    return templates.TemplateResponse("login.html", {"request": request, "error": msg})

@app.get("/logout")
def logout_action():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="user_id")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login")
    
    # Update active streak
    ProgressService.update_streak_and_activity(user["id"])
    
    # Fetch notifications
    notifs = db.query(Notification).filter(Notification.user_id == user["id"]).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Recommendations
    recs = ProgressService.get_smart_recommendations(user["id"])
    
    # Badges
    badges = db.query(UserAchievement).filter(UserAchievement.user_id == user["id"]).all()
    
    # Charts data
    study_data = ProgressService.get_study_time_data(user["id"])
    quiz_data = ProgressService.get_quiz_performance_data(user["id"])

    # Level progress calculation
    current_level_base = (user["level"] - 1) * 100
    level_progress = user["xp"] - current_level_base

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "notifs": notifs,
        "recs": recs,
        "badges": badges,
        "study_data": json.dumps(study_data),
        "quiz_data": json.dumps(quiz_data),
        "level_progress": min(100, level_progress)
    })

@app.get("/courses", response_class=HTMLResponse)
def courses_page(request: Request, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login")
    
    courses = db.query(Course).all()
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "user": user,
        "courses": courses,
        "current_topic": None,
        "user_note": None
    })

@app.get("/courses/topic/{topic_id}", response_class=HTMLResponse)
def course_topic_page(topic_id: int, request: Request, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login")
    
    courses = db.query(Course).all()
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    user_note = db.query(UserNote).filter(
        UserNote.user_id == user["id"],
        UserNote.topic_id == topic_id
    ).first()
    
    # Apply highlights
    notes_html = topic.content_notes
    if user_note and user_note.highlights_json:
        try:
            highlights = json.loads(user_note.highlights_json)
            for h_text in highlights:
                notes_html = notes_html.replace(h_text, f"<mark class='bg-yellow-300 text-black px-1 rounded'>{h_text}</mark>")
        except Exception:
            pass

    return templates.TemplateResponse("courses.html", {
        "request": request,
        "user": user,
        "courses": courses,
        "current_topic": topic,
        "notes_html": notes_html,
        "user_note": user_note
    })

# Interactive Actions API
@app.post("/api/topic/{topic_id}/action")
def topic_action_api(
    topic_id: int,
    action: str = Form(...),
    personal_notes: str = Form(None),
    selected_text: str = Form(None),
    seconds: int = Form(0),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    un = db.query(UserNote).filter(
        UserNote.user_id == user["id"],
        UserNote.topic_id == topic_id
    ).first()
    
    if not un:
        un = UserNote(user_id=user["id"], topic_id=topic_id)
        db.add(un)
        db.commit()
        db.refresh(un)
        
    if action == "bookmark":
        un.bookmarked = not un.bookmarked
        db.commit()
        return {"status": "success", "bookmarked": un.bookmarked}
        
    elif action == "complete":
        if not un.is_completed:
            un.is_completed = True
            db.commit()
            ProgressService.award_xp(user["id"], 30)
            return {"status": "success", "completed": True, "xp_awarded": 30}
        return {"status": "success", "completed": True}
        
    elif action == "save_notes":
        un.personal_notes = personal_notes
        db.commit()
        return {"status": "success"}
        
    elif action == "highlight":
        if selected_text:
            try:
                highlights = json.loads(un.highlights_json or "[]")
                if selected_text not in highlights:
                    highlights.append(selected_text)
                    un.highlights_json = json.dumps(highlights)
                    db.commit()
            except Exception:
                pass
        return {"status": "success"}
        
    elif action == "timer":
        if seconds > 5:
            ProgressService.record_study_session(user["id"], topic_id, seconds)
        return {"status": "success"}

@app.get("/ai_tutor", response_class=HTMLResponse)
def ai_tutor_page(request: Request, user = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("ai_tutor.html", {"request": request, "user": user})

@app.post("/api/ai_chat")
async def ai_chat_api(request: Request, user = Depends(get_current_user)):
    if not user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    body = await request.json()
    message = body.get("message")
    history = body.get("history", [])
    
    level = f"Class {user['level'] + 7}"
    response = AIService.get_chat_response(message, history, class_level=level)
    return {"response": response}

@app.post("/api/teach_me")
async def teach_me_api(request: Request, user = Depends(get_current_user)):
    if not user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    body = await request.json()
    topic = body.get("topic")
    level = f"Class {user['level'] + 7}"
    lesson = AIService.generate_teach_me_lesson(topic, class_level=level)
    return lesson

@app.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request, user = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("quiz.html", {"request": request, "user": user})

@app.post("/api/quiz/generate")
async def generate_quiz_api(request: Request, user = Depends(get_current_user)):
    if not user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    body = await request.json()
    subject = body.get("subject", "General")
    chapter = body.get("chapter", "Basic Concept")
    difficulty = body.get("difficulty", "Medium")
    num_questions = body.get("num_questions", 5)
    
    questions = AIService.generate_ai_quiz(subject, chapter, difficulty, num_questions)
    return {"questions": questions}

@app.post("/api/quiz/submit")
async def submit_quiz_api(request: Request, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    body = await request.json()
    answers = body.get("answers") # dict: q_idx -> answer_str
    questions = body.get("questions")
    quiz_title = body.get("title", "Practice Quiz")
    difficulty = body.get("difficulty", "Medium")
    
    correct_count = 0
    total = len(questions)
    detailed_results = []
    
    # Store quiz
    db_quiz = Quiz(title=quiz_title, difficulty=difficulty)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    for idx, q in enumerate(questions):
        user_ans = answers.get(str(idx), "").strip().lower()
        corr_ans = q.get("correct_answer", "").strip().lower()
        is_correct = user_ans == corr_ans
        
        if is_correct:
            correct_count += 1
            
        detailed_results.append({
            "question": q.get("question_text"),
            "user_answer": answers.get(str(idx), "[Unanswered]"),
            "correct_answer": q.get("correct_answer"),
            "explanation": q.get("explanation"),
            "is_correct": is_correct
        })
        
    xp_reward = correct_count * 15
    ProgressService.award_xp(user["id"], xp_reward)
    
    # Save Quiz Result
    q_res = QuizResult(
        user_id=user["id"],
        quiz_id=db_quiz.id,
        score=correct_count,
        total_questions=total,
        details_json=json.dumps(answers)
    )
    db.add(q_res)
    db.commit()
    
    return {
        "score": correct_count,
        "total": total,
        "xp_reward": xp_reward,
        "results": detailed_results
    }

@app.get("/educator", response_class=HTMLResponse)
def educator_page(request: Request, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user or user["role"] != "educator":
        return RedirectResponse(url="/login")
        
    courses = db.query(Course).all()
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    
    return templates.TemplateResponse("educator.html", {
        "request": request,
        "user": user,
        "courses": courses,
        "students": students
    })

@app.post("/educator/course")
def educator_create_course(
    title: str = Form(...),
    description: str = Form(...),
    class_level: str = Form(...),
    subject: str = Form(...),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user or user["role"] != "educator":
        return RedirectResponse(url="/login")
        
    c = Course(title=title, description=description, class_level=class_level, subject=subject, educator_id=user["id"])
    db.add(c)
    db.commit()
    return RedirectResponse(url="/educator", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/educator/lesson")
def educator_create_lesson(
    course_id: int = Form(...),
    chapter_title: str = Form(...),
    topic_title: str = Form(...),
    content_notes: str = Form(...),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user or user["role"] != "educator":
        return RedirectResponse(url="/login")
        
    chap = db.query(Chapter).filter(Chapter.course_id == course_id, Chapter.title == chapter_title).first()
    if not chap:
        from sqlalchemy import func
        max_order = db.query(func.max(Chapter.order_index)).filter(Chapter.course_id == course_id).scalar() or 0
        chap = Chapter(course_id=course_id, title=chapter_title, order_index=max_order + 1)
        db.add(chap)
        db.commit()
        db.refresh(chap)
        
    topic = Topic(chapter_id=chap.id, title=topic_title, content_notes=content_notes)
    db.add(topic)
    db.commit()
    return RedirectResponse(url="/educator", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/educator/question")
def educator_create_question(
    topic_id: int = Form(...),
    question_text: str = Form(...),
    q_type: str = Form(...),
    opt_a: str = Form(None),
    opt_b: str = Form(None),
    opt_c: str = Form(None),
    opt_d: str = Form(None),
    correct_answer: str = Form(...),
    explanation: str = Form(None),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user or user["role"] != "educator":
        return RedirectResponse(url="/login")
        
    quiz = db.query(Quiz).filter(Quiz.topic_id == topic_id).first()
    if not quiz:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        quiz = Quiz(topic_id=topic_id, title=f"{topic.title} Study Quiz", difficulty="Medium")
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
    opts = []
    if q_type == "mcq":
        opts = [opt_a, opt_b, opt_c, opt_d]
    else:
        opts = ["True", "False"]
        
    q = Question(
        quiz_id=quiz.id,
        question_text=question_text,
        question_type=QuestionType.MCQ if q_type == "mcq" else QuestionType.TF,
        options_json=json.dumps(opts),
        correct_answer=correct_answer,
        explanation=explanation
    )
    db.add(q)
    db.commit()
    return RedirectResponse(url="/educator", status_code=status.HTTP_303_SEE_OTHER)
