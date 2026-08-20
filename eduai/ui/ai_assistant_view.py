from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QFrame, QSplitter, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from eduai.services.ai_service import AIService
from eduai.ui.components.chat_bubble import ChatBubble

class AIAssistantView(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.chat_history = []  # List of tuples: (speaker, text)

        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        
        # LEFT: EduAI Chatbot
        chat_panel = QFrame()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        chat_title = QLabel("🤖 EduAI Chatbot Assistant")
        chat_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #6366f1;")
        chat_layout.addWidget(chat_title)
        
        # Scroll Area for bubbles
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.StyledPanel)
        
        self.chat_container = QWidget()
        self.chat_list_layout = QVBoxLayout(self.chat_container)
        self.chat_list_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)
        
        # AI Quick Helper Action Buttons
        helpers_layout = QHBoxLayout()
        helpers = [
            ("Explain Simply", "Explain the concept of [TOPIC] in simple words for a school student."),
            ("Give Example", "Provide 3 daily life examples of [TOPIC]."),
            ("Summarize", "Create a short summary bullet list of [TOPIC]."),
            ("Explain Step-by-Step", "Provide step-by-step mathematical derivation or methodology for [TOPIC]."),
            ("Practice Me", "Generate 2 practice questions about [TOPIC] with explanations.")
        ]
        
        for name, prompt_text in helpers:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked=False, p=prompt_text: self.use_helper_prompt(p))
            helpers_layout.addWidget(btn)
        chat_layout.addLayout(helpers_layout)
        
        # Input Box Row
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask EduAI a question, or highlight text and click helper buttons...")
        self.input_field.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("Send")
        send_btn.setObjectName("Primary")
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)
        
        splitter.addWidget(chat_panel)

        # RIGHT: Teach Me (Personal AI Teacher Tool)
        teach_panel = QFrame()
        teach_layout = QVBoxLayout(teach_panel)
        teach_layout.setContentsMargins(0, 0, 0, 0)
        
        teach_title = QLabel("🎓 'Teach Me' AI Tutor")
        teach_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")
        teach_layout.addWidget(teach_title)
        
        desc = QLabel("Enter any topic to receive a complete, personalized mini-lesson immediately.")
        desc.setObjectName("Subtitle")
        teach_layout.addWidget(desc)
        
        topic_row = QHBoxLayout()
        self.teach_input = QLineEdit()
        self.teach_input.setPlaceholderText("Enter topic name (e.g. Gravity, Quadrilateral, Osmosis)...")
        self.teach_input.returnPressed.connect(self.run_teach_me)
        
        teach_btn = QPushButton("Teach Me!")
        teach_btn.setObjectName("Primary")
        teach_btn.clicked.connect(self.run_teach_me)
        
        topic_row.addWidget(self.teach_input)
        topic_row.addWidget(teach_btn)
        teach_layout.addLayout(topic_row)
        
        # Scrollable output
        self.teach_display = QTextEdit()
        self.teach_display.setReadOnly(True)
        teach_layout.addWidget(self.teach_display)
        
        splitter.addWidget(teach_panel)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Initial greeting from EduAI
        self.add_bubble("Hello! I am EduAI, your personal study assistant. What topic are we learning today?", is_user=False)

    def add_bubble(self, text, is_user):
        bubble = ChatBubble(text, is_user)
        # Add to layout just before the stretch
        self.chat_list_layout.insertWidget(self.chat_list_layout.count() - 1, bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.add_bubble(text, is_user=True)
        self.chat_history.append(("Student", text))
        
        # Fetch AI response
        # Disable input during generation
        self.input_field.setEnabled(False)
        QTimer.singleShot(200, lambda: self.fetch_ai_response(text))

    def fetch_ai_response(self, text):
        try:
            level = f"Class {self.user['level'] + 7}"  # Mock student grade representation
            response = AIService.get_chat_response(text, self.chat_history, class_level=level)
            self.add_bubble(response, is_user=False)
            self.chat_history.append(("EduAI", response))
        except Exception as e:
            self.add_bubble(f"⚠️ Error: Could not connect to EduAI services. {str(e)}", is_user=False)
        finally:
            self.input_field.setEnabled(True)
            self.input_field.setFocus()

    def use_helper_prompt(self, template):
        # Fetch active text from input or query default
        query = self.input_field.text().strip()
        if not query:
            # Prompt user for concept
            concept, ok = QInputDialog.getText(self, "Help Prompt", "Which concept/topic should we analyze?")
            if not ok or not concept.strip():
                return
            query = concept.strip()
            
        filled = template.replace("[TOPIC]", query)
        self.input_field.setText(filled)
        self.send_message()

    def run_teach_me(self):
        topic = self.teach_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Teach Me", "Please type a topic title first.")
            return
            
        self.teach_display.setText("Generating your personalized study lesson plan... Please wait.")
        self.teach_input.setEnabled(False)
        
        # Delay trigger slightly to allow UI refresh
        QTimer.singleShot(200, lambda: self.generate_teach_me_lesson(topic))

    def generate_teach_me_lesson(self, topic):
        try:
            level = f"Class {self.user['level'] + 7}"
            lesson = AIService.generate_teach_me_lesson(topic, class_level=level)
            
            # Format custom HTML structured block
            html = f"""
            <div style="font-family: 'Segoe UI', sans-serif;">
                <h1 style="color: #10b981; border-bottom: 2px solid #10b981;">Lesson Plan: {topic.upper()}</h1>
                
                <h3 style="color: #6366f1;">1. What you need to know first (Prerequisites)</h3>
                <ul>
            """
            for pre in lesson.get("prerequisites", []):
                html += f"<li>{pre}</li>"
            html += f"""
                </ul>
                
                <h3 style="color: #6366f1;">2. Simple Explanation</h3>
                <p>{lesson.get("explanation", "")}</p>
                
                <h3 style="color: #6366f1;">3. Real-life Metaphor / Analogy</h3>
                <p><i>{lesson.get("analogy", "")}</i></p>
                
                <h3 style="color: #6366f1;">4. Worked Example</h3>
                <pre style="background-color: #1e293b; padding: 10px; border-radius: 6px; color: #f8fafc;">
{lesson.get("worked_example", "")}
                </pre>
                
                <h3 style="color: #e11d48;">5. Common Student Mistakes</h3>
                <ul>
            """
            for err in lesson.get("common_mistakes", []):
                html += f"<li>{err}</li>"
            html += f"""
                </ul>
                
                <h3 style="color: #6366f1;">6. Quick Revision Summary</h3>
                <p><b>Key Takeaway:</b> {lesson.get("summary", "")}</p>
            </div>
            """
            self.teach_display.setHtml(html)
        except Exception as e:
            self.teach_display.setText(f"Could not load personal tutor lesson. Error: {str(e)}")
        finally:
            self.teach_input.setEnabled(True)
            self.teach_input.clear()
            self.teach_input.setFocus()
