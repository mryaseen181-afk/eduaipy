from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class ChatBubble(QWidget):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Inner bubble frame
        bubble = QWidget()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.MarkdownText) # Enable markdown in bubble!
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble_layout.addWidget(label)
        
        # Styles
        if is_user:
            # User bubble: Blue/Indigo background, aligned right
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #6366f1;
                    color: white;
                    border-radius: 12px;
                    border-top-right-radius: 2px;
                }
                QLabel {
                    color: white;
                    font-size: 13px;
                }
            """)
            main_layout.addStretch()
            main_layout.addWidget(bubble)
            main_layout.setStretch(0, 1)
            main_layout.setStretch(1, 0)
        else:
            # AI bubble: Slate background, aligned left
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #334155;
                    color: #f8fafc;
                    border-radius: 12px;
                    border-top-left-radius: 2px;
                }
                QLabel {
                    color: #f8fafc;
                    font-size: 13px;
                }
            """)
            main_layout.addWidget(bubble)
            main_layout.addStretch()
            main_layout.setStretch(0, 0)
            main_layout.setStretch(1, 1)
            
        self.setLayout(main_layout)
