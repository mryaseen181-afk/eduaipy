import time
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QTextEdit, QPushButton, QLabel, QFrame, QLineEdit, QSplitter, 
    QMessageBox, QInputDialog, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from eduai.database.connection import SessionLocal
from eduai.database.models import Course, Chapter, Topic, UserNote
from eduai.services.progress_service import ProgressService
from eduai.utils.file_handler import FileHandler

class CourseViewer(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.current_topic_id = None
        
        # Session timer fields
        self.session_start_time = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_label)
        self.elapsed_seconds = 0

        self.setup_ui()
        self.load_course_tree()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Splitter to allow resizing left/right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANEL: Search and Course Tree
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search courses, topics, terms...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Course Syllabus Navigator")
        self.tree.itemClicked.connect(self.handle_tree_item_clicked)
        left_layout.addWidget(self.tree)
        
        splitter.addWidget(left_panel)
        
        # RIGHT PANEL: Notes display and actions
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Topic Header & Timer
        header_layout = QHBoxLayout()
        self.topic_title_lbl = QLabel("Select a Topic to Start Learning")
        self.topic_title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #6366f1;")
        self.timer_lbl = QLabel("Timer: 00:00")
        self.timer_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #10b981;")
        
        header_layout.addWidget(self.topic_title_lbl, 3)
        header_layout.addWidget(self.timer_lbl, 1, alignment=Qt.AlignRight)
        right_layout.addLayout(header_layout)
        
        # Action Buttons row
        action_layout = QHBoxLayout()
        self.bookmark_btn = QPushButton("Bookmark")
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        
        self.complete_btn = QPushButton("Mark Completed")
        self.complete_btn.clicked.connect(self.mark_completed)
        self.complete_btn.setObjectName("Primary")
        
        self.download_btn = QPushButton("Download Notes")
        self.download_btn.clicked.connect(self.download_notes)
        
        self.highlight_btn = QPushButton("Highlight Text")
        self.highlight_btn.clicked.connect(self.highlight_notes)
        
        action_layout.addWidget(self.bookmark_btn)
        action_layout.addWidget(self.highlight_btn)
        action_layout.addWidget(self.download_btn)
        action_layout.addWidget(self.complete_btn)
        right_layout.addLayout(action_layout)
        
        # Notes text view (supports HTML/Markdown style formatting)
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        right_layout.addWidget(self.notes_display)
        
        # Personal Notes Box
        personal_box = QFrame()
        personal_box.setObjectName("Card")
        pb_layout = QVBoxLayout(personal_box)
        pb_layout.setContentsMargins(10, 10, 10, 10)
        pb_layout.addWidget(QLabel("<b>My Personal Study Notes (Autosaved)</b>"))
        
        self.personal_notes_edit = QTextEdit()
        self.personal_notes_edit.setPlaceholderText("Write your own reminders, keys, formulas or summaries here...")
        self.personal_notes_edit.textChanged.connect(self.save_personal_notes)
        self.personal_notes_edit.setFixedHeight(100)
        pb_layout.addWidget(self.personal_notes_edit)
        right_layout.addWidget(personal_box)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_course_tree(self):
        self.tree.clear()
        db = SessionLocal()
        try:
            courses = db.query(Course).all()
            for course in courses:
                course_item = QTreeWidgetItem(self.tree)
                course_item.setText(0, f"📚 {course.title} ({course.class_level} - {course.subject})")
                course_item.setData(0, Qt.UserRole, {"type": "course", "id": course.id})
                
                for chapter in course.chapters:
                    chap_item = QTreeWidgetItem(course_item)
                    chap_item.setText(0, f"📖 Chapter: {chapter.title}")
                    chap_item.setData(0, Qt.UserRole, {"type": "chapter", "id": chapter.id})
                    
                    for topic in chapter.topics:
                        topic_item = QTreeWidgetItem(chap_item)
                        topic_item.setText(0, f"📄 {topic.title}")
                        topic_item.setData(0, Qt.UserRole, {"type": "topic", "id": topic.id})
            self.tree.expandAll()
        finally:
            db.close()

    def perform_search(self):
        query = self.search_input.text().strip().lower()
        if not query:
            self.load_course_tree()
            return
            
        self.tree.clear()
        db = SessionLocal()
        try:
            # Search courses, chapters, topics
            topics = db.query(Topic).join(Chapter).join(Course).filter(
                (Topic.title.like(f"%{query}%")) | 
                (Topic.content_notes.like(f"%{query}%")) | 
                (Chapter.title.like(f"%{query}%")) | 
                (Course.title.like(f"%{query}%"))
            ).all()
            
            if not topics:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "No search results match query.")
                return
                
            for topic in topics:
                topic_item = QTreeWidgetItem(self.tree)
                topic_item.setText(0, f"📄 {topic.title} (in {topic.chapter.course.title})")
                topic_item.setData(0, Qt.UserRole, {"type": "topic", "id": topic.id})
        finally:
            db.close()

    def handle_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data or data.get("type") != "topic":
            return
            
        topic_id = data.get("id")
        self.load_topic(topic_id)

    def load_topic(self, topic_id):
        # Stop and save previous session if active
        self.save_current_study_session()
        
        self.current_topic_id = topic_id
        
        db = SessionLocal()
        try:
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            if not topic:
                return
                
            self.topic_title_lbl.setText(f"Topic: {topic.title}")
            
            # Fetch user note status (bookmarks, highlights, personal notes)
            user_note = db.query(UserNote).filter(
                UserNote.user_id == self.user['id'],
                UserNote.topic_id == topic_id
            ).first()
            
            notes_html = topic.content_notes.replace("\n", "<br>")
            
            if user_note:
                self.bookmark_btn.setText("Bookmarked ★" if user_note.bookmarked else "Bookmark")
                self.complete_btn.setText("Lesson Completed ✓" if user_note.is_completed else "Mark Completed")
                self.personal_notes_edit.blockSignals(True)
                self.personal_notes_edit.setText(user_note.personal_notes or "")
                self.personal_notes_edit.blockSignals(False)
                
                # Apply saved highlights to the HTML notes if exists
                import json
                try:
                    highlights = json.loads(user_note.highlights_json or "[]")
                    for h_text in highlights:
                        notes_html = notes_html.replace(h_text, f"<span style='background-color: yellow; color: black;'>{h_text}</span>")
                except Exception:
                    pass
            else:
                self.bookmark_btn.setText("Bookmark")
                self.complete_btn.setText("Mark Completed")
                self.personal_notes_edit.blockSignals(True)
                self.personal_notes_edit.clear()
                self.personal_notes_edit.blockSignals(False)
                
            self.notes_display.setHtml(notes_html)
            
            # Start timer
            self.elapsed_seconds = 0
            self.session_start_time = time.time()
            self.timer.start(1000)
            
        finally:
            db.close()

    def update_timer_label(self):
        self.elapsed_seconds += 1
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        self.timer_lbl.setText(f"Timer: {mins:02d}:{secs:02d}")

    def save_current_study_session(self):
        if self.current_topic_id and self.elapsed_seconds > 5:
            # Save session
            ProgressService.record_study_session(self.user['id'], self.current_topic_id, self.elapsed_seconds)
        self.timer.stop()
        self.elapsed_seconds = 0
        self.timer_lbl.setText("Timer: 00:00")

    def toggle_bookmark(self):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user['id'],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            if not un:
                un = UserNote(user_id=self.user['id'], topic_id=self.current_topic_id, bookmarked=True)
                db.add(un)
            else:
                un.bookmarked = not un.bookmarked
                
            db.commit()
            self.bookmark_btn.setText("Bookmarked ★" if un.bookmarked else "Bookmark")
        finally:
            db.close()

    def mark_completed(self):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user['id'],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            if not un:
                un = UserNote(user_id=self.user['id'], topic_id=self.current_topic_id, is_completed=True)
                db.add(un)
            else:
                if un.is_completed:
                    QMessageBox.information(self, "Completed", "You have already completed this topic.")
                    return
                un.is_completed = True
                
            db.commit()
            self.complete_btn.setText("Lesson Completed ✓")
            
            # Award XP for completion
            ProgressService.award_xp(self.user['id'], 30)
            QMessageBox.information(self, "Well Done! 🎉", "Topic completed successfully! +30 XP awarded.")
        finally:
            db.close()

    def download_notes(self):
        if not self.current_topic_id:
            QMessageBox.warning(self, "Error", "Please select a topic first.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Notes", "", "Text Files (*.txt);;Markdown (*.md)")
        if not filepath:
            return
            
        db = SessionLocal()
        try:
            t = db.query(Topic).filter(Topic.id == self.current_topic_id).first()
            if t:
                content = t.content_notes + f"\n\nPersonal Notes:\n{self.personal_notes_edit.toPlainText()}"
                success = FileHandler.export_notes_to_txt(filepath, t.title, content)
                if success:
                    QMessageBox.information(self, "Exported", "Study material exported successfully!")
                else:
                    QMessageBox.critical(self, "Failed", "Could not export study material.")
        finally:
            db.close()

    def save_personal_notes(self):
        if not self.current_topic_id:
            return
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user['id'],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            text = self.personal_notes_edit.toPlainText()
            if not un:
                un = UserNote(user_id=self.user['id'], topic_id=self.current_topic_id, personal_notes=text)
                db.add(un)
            else:
                un.personal_notes = text
            db.commit()
        finally:
            db.close()

    def highlight_notes(self):
        # Quick check for selected text in display
        cursor = self.notes_display.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            QMessageBox.warning(self, "Highlight", "Please highlight/select text in the notes viewer using your cursor first.")
            return
            
        if not self.current_topic_id:
            return
            
        import json
        db = SessionLocal()
        try:
            un = db.query(UserNote).filter(
                UserNote.user_id == self.user['id'],
                UserNote.topic_id == self.current_topic_id
            ).first()
            
            if not un:
                un = UserNote(user_id=self.user['id'], topic_id=self.current_topic_id)
                db.add(un)
                db.commit()
                db.refresh(un)
                
            highlights = json.loads(un.highlights_json or "[]")
            if selected_text not in highlights:
                highlights.append(selected_text)
                un.highlights_json = json.dumps(highlights)
                db.commit()
            
            # Reload view to apply highlight stylesheet
            self.load_topic(self.current_topic_id)
        finally:
            db.close()

    def closeEvent(self, event):
        self.save_current_study_session()
        super().closeEvent(event)
