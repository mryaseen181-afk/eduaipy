import time
import flet as ft
from eduai.services.progress_service import ProgressService
from eduai.database.connection import SessionLocal
from eduai.database.models import Course, Chapter, Topic, UserNote

class CoursesView(ft.Container):
    def __init__(self, user, page: ft.Page):
        super().__init__()
        self.user = user
        self.page = page
        self.current_topic_id = None
        self.expand = True
        
        # Session timer fields
        self.elapsed_seconds = 0
        self.session_active = False
        
        # UI controls references
        self.tree_col = ft.Column(spacing=5, scroll=ft.ScrollMode.ADAPTIVE)
        self.topic_title = ft.Text("Select a Topic to Start Learning", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400)
        self.timer_txt = ft.Text("Timer: 00:00", size=12, color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD)
        
        self.notes_body = ft.Markdown(
            value="Select a course from the navigator on the left to read notes.",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            expand=True
        )
        
        self.personal_notes = ft.TextField(
            label="My Personal Study Notes (Autosaved)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            placeholder="Type your study summaries, key terms, or formula sheets...",
            on_change=self.debounce_save_notes
        )
        
        self.bookmark_btn = ft.IconButton(icon=ft.icons.STAR_BORDER_ROUNDED, on_click=self.toggle_bookmark)
        self.complete_btn = ft.ElevatedButton("Mark Completed", on_click=self.mark_completed, bgcolor=ft.colors.INDIGO_500, color=ft.colors.WHITE)
        self.download_btn = ft.IconButton(icon=ft.icons.DOWNLOAD_ROUNDED, on_click=self.download_notes)
        self.highlight_btn = ft.IconButton(icon=ft.icons.HIGHLIGHT_ALT_ROUNDED, on_click=self.highlight_notes)
        
        self.notes_actions_row = ft.Row([self.bookmark_btn, self.highlight_btn, self.download_btn, self.complete_btn], spacing=10, visible=False)
        self.notes_editor_container = ft.Container(content=self.personal_notes, visible=False)
        
        self.load_courses()
        self.content = self.build_layout()
        
        # Setup background thread timer
        self.timer_running = True
        self.page.run_thread(self.run_timer)

    def load_courses(self):
        self.tree_col.controls.clear()
        db = SessionLocal()
        try:
            courses = db.query(Course).all()
            for c in courses:
                chapters_controls = []
                for chap in c.chapters:
                    topics_controls = []
                    for topic in chap.topics:
                        topics_controls.append(
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.ARTICLE_ROUNDED, size=18),
                                title=ft.Text(topic.title, size=12, weight=ft.FontWeight.SEMI_BOLD),
                                on_click=lambda e, t_id=topic.id: self.load_topic(t_id),
                                dense=True
                            )
                        )
                    # Collapsible Chapter
                    chapters_controls.append(
                        ft.ExpansionTile(
                            title=ft.Text(chap.title, size=13, weight=ft.FontWeight.BOLD),
                            leading=ft.Icon(ft.icons.BOOK_ROUNDED, size=18),
                            controls=topics_controls,
                            initially_expanded=False
                        )
                    )
                # Collapsible Course Syllabus
                self.tree_col.controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(c.title, size=14, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400),
                        subtitle=ft.Text(f"{c.class_level} • {c.subject}", size=10, color=ft.colors.GREY_400),
                        controls=chapters_controls,
                        initially_expanded=True
                    )
                )
        finally:
            db.close()

    def load_topic(self, topic_id):
        self.save_study_session()
        self.current_topic_id = topic_id
        
        db = SessionLocal()
        try:
            t = db.query(Topic).filter(Topic.id == topic_id).first()
            if not t:
                return
                
            self.topic_title.value = t.title
            
            # Formatted markdown body
            self.notes_body.value = t.content_notes
            
            # Query note history
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user["id"],
                UserNote.topic_id == topic_id
            ).first()
            
            if un:
                self.bookmark_btn.icon = ft.icons.STAR_ROUNDED if un.bookmarked else ft.icons.STAR_BORDER_ROUNDED
                self.bookmark_btn.icon_color = ft.colors.AMBER_400 if un.bookmarked else None
                self.complete_btn.text = "Completed ✓" if un.is_completed else "Mark Completed"
                self.personal_notes.value = un.personal_notes or ""
            else:
                self.bookmark_btn.icon = ft.icons.STAR_BORDER_ROUNDED
                self.bookmark_btn.icon_color = None
                self.complete_btn.text = "Mark Completed"
                self.personal_notes.value = ""
                
            self.notes_actions_row.visible = True
            self.notes_editor_container.visible = True
            
            # Reset timer
            self.elapsed_seconds = 0
            self.session_active = True
            self.update_timer_display()
            
            self.page.update()
        finally:
            db.close()

    def update_timer_display(self):
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        self.timer_txt.value = f"Timer: {mins:02d}:{secs:02d}"

    def save_study_session(self):
        if self.current_topic_id and self.elapsed_seconds > 5:
            ProgressService.record_study_session(self.user["id"], self.current_topic_id, self.elapsed_seconds)
        self.session_active = False
        self.elapsed_seconds = 0
        self.timer_txt.value = "Timer: 00:00"

    def toggle_bookmark(self, e):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user["id"],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            if not un:
                un = UserNote(user_id=self.user["id"], topic_id=self.current_topic_id, bookmarked=True)
                db.add(un)
            else:
                un.bookmarked = not un.bookmarked
                
            db.commit()
            self.bookmark_btn.icon = ft.icons.STAR_ROUNDED if un.bookmarked else ft.icons.STAR_BORDER_ROUNDED
            self.bookmark_btn.icon_color = ft.colors.AMBER_400 if un.bookmarked else None
            self.page.update()
        finally:
            db.close()

    def mark_completed(self, e):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user["id"],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            if not un:
                un = UserNote(user_id=self.user["id"], topic_id=self.current_topic_id, is_completed=True)
                db.add(un)
            else:
                if un.is_completed:
                    return
                un.is_completed = True
                
            db.commit()
            self.complete_btn.text = "Completed ✓"
            
            # Award XP
            ProgressService.award_xp(self.user["id"], 30)
            self.show_snack("Topic completed successfully! +30 XP awarded. 🎉")
            self.page.update()
        finally:
            db.close()

    def debounce_save_notes(self, e):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user["id"],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            text = self.personal_notes.value
            if not un:
                un = UserNote(user_id=self.user["id"], topic_id=self.current_topic_id, personal_notes=text)
                db.add(un)
            else:
                un.personal_notes = text
            db.commit()
        finally:
            db.close()

    def highlight_notes(self, e):
        # In Flet native mobile, highlights can be simulated by inputting a highlighted term
        # Let's show a prompt dialog to enter a key term to highlight
        def close_dialog(e):
            dialog.open = False
            self.page.update()
            
        def apply_highlight(e):
            term = highlight_input.value.strip()
            if term and self.current_topic_id:
                import json
                db = SessionLocal()
                try:
                    un = db.query(UserNote).filter(UserNote.user_id == self.user["id"], UserNote.topic_id == self.current_topic_id).first()
                    if not un:
                        un = UserNote(user_id=self.user["id"], topic_id=self.current_topic_id)
                        db.add(un)
                        db.commit()
                        db.refresh(un)
                    highlights = json.loads(un.highlights_json or "[]")
                    if term not in highlights:
                        highlights.append(term)
                        un.highlights_json = json.dumps(highlights)
                        db.commit()
                    self.show_snack(f"Added highlight rule for: '{term}'")
                finally:
                    db.close()
            dialog.open = False
            self.page.update()

        highlight_input = ft.TextField(label="Text to Highlight", placeholder="e.g. Newton, inertia, force...")
        dialog = ft.AlertDialog(
            title=ft.Text("Highlight Study Term"),
            content=highlight_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Highlight", on_click=apply_highlight)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def download_notes(self, e):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            t = db.query(Topic).filter(Topic.id == self.current_topic_id).first()
            if t:
                import os
                download_dir = os.path.expanduser("~")
                filepath = os.path.join(download_dir, f"StudyFlow_{t.title}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"=== STUDYFLOW: {t.title.upper()} ===\n\n{t.content_notes}")
                self.show_snack(f"Saved notes directly to: {filepath}")
        finally:
            db.close()

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def run_timer(self):
        while self.timer_running:
            if self.session_active:
                self.elapsed_seconds += 1
                self.update_timer_display()
                try:
                    self.page.update()
                except Exception:
                    break
            time.sleep(1)

    def clean_up(self):
        self.timer_running = False
        self.save_study_session()

    def build_layout(self):
        # Two-column layout (Left: Syllabus tree scroll, Right: Reader panel scroll)
        return ft.Row(
            [
                # Tree Navigator Pane
                ft.Container(
                    content=self.tree_col,
                    width=260,
                    bgcolor=ft.colors.GREY_900,
                    padding=10,
                    border_radius=12
                ),
                
                # Reading view Pane
                ft.Container(
                    content=ft.Column(
                        [
                            # Topic Header details
                            ft.Row(
                                [
                                    self.topic_title,
                                    self.timer_txt
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Divider(height=1),
                            
                            # Actions row
                            self.notes_actions_row,
                            
                            # Study Notes Scroll container
                            ft.Container(
                                content=self.notes_body,
                                expand=True
                            ),
                            
                            # Editor
                            self.notes_editor_container
                        ],
                        spacing=12,
                        expand=True
                    ),
                    expand=True,
                    padding=10
                )
            ],
            spacing=10,
            expand=True
        )
