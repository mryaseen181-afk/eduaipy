import datetime
import json
from sqlalchemy import func
from eduai.database.connection import SessionLocal
from eduai.database.models import User, QuizResult, StudySession, UserNote, UserAchievement, Topic, Notification

class ProgressService:
    @staticmethod
    def get_student_profile(user_id):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            return {
                "xp": user.xp,
                "level": user.level,
                "streak_count": user.streak_count,
                "profile_pic": user.profile_pic,
                "last_active": user.last_active
            }
        finally:
            db.close()

    @staticmethod
    def update_streak_and_activity(user_id):
        """
        Updates streak count. If last active date is yesterday, increment. If today, do nothing. If older, reset to 1.
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            now = datetime.datetime.utcnow()
            today = now.date()
            last_active_date = user.last_active.date()
            
            delta = (today - last_active_date).days
            if delta == 1:
                user.streak_count += 1
                # Trigger streak notification
                notif = Notification(
                    user_id=user_id,
                    title="Streak Extended! 🔥",
                    message=f"Congratulations! You've kept your streak alive. Current streak: {user.streak_count} days.",
                    type="streak"
                )
                db.add(notif)
            elif delta > 1:
                user.streak_count = 1
                notif = Notification(
                    user_id=user_id,
                    title="Streak Reset ❄️",
                    message="You missed a day, so your streak reset to 1. Let's build it back up today!",
                    type="streak"
                )
                db.add(notif)

            user.last_active = now
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    @classmethod
    def award_xp(cls, user_id, amount):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            user.xp += amount
            # Level formula: level = floor(xp / 100) + 1
            new_level = int(user.xp // 100) + 1
            if new_level > user.level:
                user.level = new_level
                # Level up badge
                badge_name = f"Level {new_level} Scholar"
                ach = UserAchievement(
                    user_id=user_id,
                    badge_name=badge_name,
                    description=f"Unlocked by reaching Level {new_level}!"
                )
                db.add(ach)
                
                notif = Notification(
                    user_id=user_id,
                    title="Level Up! 🎉",
                    message=f"Awesome! You reached Level {new_level}. Keep up the great work!",
                    type="general"
                )
                db.add(notif)
                
            db.commit()
            return user.xp, user.level
        except Exception:
            db.rollback()
            return 0, 1
        finally:
            db.close()

    @staticmethod
    def record_study_session(user_id, topic_id, seconds):
        db = SessionLocal()
        try:
            session = StudySession(user_id=user_id, topic_id=topic_id, time_spent=seconds)
            db.add(session)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def get_weak_topics(user_id):
        """
        Calculates weak topics based on quiz scores lower than 60%.
        """
        db = SessionLocal()
        try:
            results = db.query(QuizResult).filter(QuizResult.user_id == user_id).all()
            incorrect_topics = {}
            for r in results:
                # Get the quiz's topic
                quiz = r.quiz
                if not quiz or not quiz.topic:
                    continue
                topic_title = quiz.topic.title
                score_pct = (r.score / r.total_questions) * 100 if r.total_questions > 0 else 0
                if score_pct < 60:
                    incorrect_topics[topic_title] = incorrect_topics.get(topic_title, 0) + 1
            
            # Sort by frequency of failure
            sorted_weak = sorted(incorrect_topics.items(), key=lambda x: x[1], reverse=True)
            return [topic for topic, count in sorted_weak[:3]]
        finally:
            db.close()

    @classmethod
    def get_smart_recommendations(cls, user_id):
        """
        Recommends next lessons based on weak topics, completed lessons, etc.
        """
        db = SessionLocal()
        try:
            weak = cls.get_weak_topics(user_id)
            recs = []
            if weak:
                for w in weak:
                    recs.append(f"You should revise: {w} (scored low in recent quiz)")
            
            # Recommend uncompleted topic in the database
            completed_topic_ids = db.query(UserNote.topic_id).filter(UserNote.user_id == user_id, UserNote.is_completed == True).all()
            completed_ids = [c[0] for c in completed_topic_ids]

            next_topic = db.query(Topic).filter(~Topic.id.in_(completed_ids)).first()
            if next_topic:
                recs.append(f"Start new topic: {next_topic.title} in {next_topic.chapter.course.title}")
            else:
                recs.append("All enrolled course topics completed! Try the Practice Arena.")

            return recs[:3]
        finally:
            db.close()

    @staticmethod
    def get_study_time_data(user_id):
        db = SessionLocal()
        try:
            # Group study time by date or topic
            data = db.query(
                Topic.title,
                func.sum(StudySession.time_spent)
            ).join(StudySession, Topic.id == StudySession.topic_id)\
             .filter(StudySession.user_id == user_id)\
             .group_by(Topic.title).all()
            return {title: round(seconds / 60, 1) for title, seconds in data}
        finally:
            db.close()

    @staticmethod
    def get_quiz_performance_data(user_id):
        db = SessionLocal()
        try:
            # Get list of quiz scores in chronological order
            data = db.query(QuizResult.completed_at, QuizResult.score, QuizResult.total_questions)\
                     .filter(QuizResult.user_id == user_id)\
                     .order_by(QuizResult.completed_at.asc()).all()
            return [round((score / total) * 100, 1) if total > 0 else 0 for _, score, total in data]
        finally:
            db.close()
