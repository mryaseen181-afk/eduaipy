import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///eduai_platform.db")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Style configurations
THEME_DARK = """
    QMainWindow, QDialog, QWidget {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QFrame#Sidebar {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    QFrame#Card {
        background-color: #1e293b;
        border-radius: 12px;
        border: 1px solid #334155;
        padding: 16px;
    }
    QLabel {
        color: #f8fafc;
    }
    QLabel#Header {
        font-size: 20px;
        font-weight: bold;
        color: #38bdf8;
    }
    QLabel#Subtitle {
        font-size: 14px;
        color: #94a3b8;
    }
    QPushButton#Primary {
        background-color: #6366f1;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 16px;
        border: none;
    }
    QPushButton#Primary:hover {
        background-color: #4f46e5;
    }
    QPushButton#Secondary {
        background-color: #334155;
        color: #f8fafc;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 16px;
        border: 1px solid #475569;
    }
    QPushButton#Secondary:hover {
        background-color: #475569;
    }
    QPushButton#NavButton {
        background-color: transparent;
        color: #94a3b8;
        text-align: left;
        padding: 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        border: none;
    }
    QPushButton#NavButton:hover {
        background-color: #334155;
        color: #ffffff;
    }
    QPushButton#NavButtonActive {
        background-color: #6366f1;
        color: #ffffff;
        text-align: left;
        padding: 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        border: none;
    }
    QLineEdit, QTextEdit, QComboBox, QListWidget, QTreeWidget {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #f8fafc;
        padding: 8px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QListWidget:focus {
        border: 1px solid #6366f1;
    }
    QRadioButton {
        color: #f8fafc;
        font-size: 14px;
        padding: 4px;
    }
    QProgressBar {
        border: 1px solid #334155;
        border-radius: 6px;
        text-align: center;
        color: white;
        background-color: #0f172a;
        font-weight: bold;
    }
    QProgressBar::chunk {
        background-color: #10b981;
        border-radius: 5px;
    }
    QScrollBar:vertical {
        border: none;
        background: #0f172a;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #334155;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #475569;
    }
    QTabWidget::pane {
        border: 1px solid #334155;
        background: #1e293b;
        border-radius: 8px;
    }
    QTabBar::tab {
        background: #0f172a;
        border: 1px solid #334155;
        padding: 8px 12px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #94a3b8;
    }
    QTabBar::tab:selected {
        background: #1e293b;
        color: #f8fafc;
        border-bottom-color: #1e293b;
    }
"""

THEME_LIGHT = """
    QMainWindow, QDialog, QWidget {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QFrame#Sidebar {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
    QFrame#Card {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 16px;
    }
    QLabel {
        color: #0f172a;
    }
    QLabel#Header {
        font-size: 20px;
        font-weight: bold;
        color: #0284c7;
    }
    QLabel#Subtitle {
        font-size: 14px;
        color: #475569;
    }
    QPushButton#Primary {
        background-color: #4f46e5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 16px;
        border: none;
    }
    QPushButton#Primary:hover {
        background-color: #4338ca;
    }
    QPushButton#Secondary {
        background-color: #e2e8f0;
        color: #0f172a;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 16px;
        border: 1px solid #cbd5e1;
    }
    QPushButton#Secondary:hover {
        background-color: #cbd5e1;
    }
    QPushButton#NavButton {
        background-color: transparent;
        color: #475569;
        text-align: left;
        padding: 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        border: none;
    }
    QPushButton#NavButton:hover {
        background-color: #e2e8f0;
        color: #0f172a;
    }
    QPushButton#NavButtonActive {
        background-color: #4f46e5;
        color: #ffffff;
        text-align: left;
        padding: 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        border: none;
    }
    QLineEdit, QTextEdit, QComboBox, QListWidget, QTreeWidget {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        color: #0f172a;
        padding: 8px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QListWidget:focus {
        border: 1px solid #4f46e5;
    }
    QRadioButton {
        color: #0f172a;
        font-size: 14px;
        padding: 4px;
    }
    QProgressBar {
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        text-align: center;
        color: #0f172a;
        background-color: #e2e8f0;
        font-weight: bold;
    }
    QProgressBar::chunk {
        background-color: #10b981;
        border-radius: 5px;
    }
    QScrollBar:vertical {
        border: none;
        background: #f8fafc;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    QTabWidget::pane {
        border: 1px solid #cbd5e1;
        background: #ffffff;
        border-radius: 8px;
    }
    QTabBar::tab {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 8px 12px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #475569;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #0f172a;
        border-bottom-color: #ffffff;
    }
"""
