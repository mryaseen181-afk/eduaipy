import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StudyTimeChart(QWidget):
    def __init__(self, data: dict, parent=None, is_dark=True):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Setup Figure
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        
        self.update_chart(data, is_dark)

    def update_chart(self, data: dict, is_dark):
        self.ax.clear()
        
        # Colors based on theme
        bg_color = "#1e293b" if is_dark else "#ffffff"
        text_color = "#f8fafc" if is_dark else "#0f172a"
        bar_color = "#6366f1" if is_dark else "#4f46e5"
        grid_color = "#334155" if is_dark else "#e2e8f0"
        
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        if not data:
            self.ax.text(0.5, 0.5, "No study time data recorded yet.", 
                         color=text_color, ha='center', va='center', fontsize=11)
            self.ax.set_axis_off()
        else:
            self.ax.set_axis_on()
            topics = list(data.keys())
            minutes = list(data.values())
            
            bars = self.ax.barh(topics, minutes, color=bar_color, height=0.5)
            
            self.ax.set_xlabel("Time Spent (Minutes)", color=text_color, fontweight='bold')
            self.ax.tick_params(colors=text_color)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(grid_color)
            self.ax.spines['bottom'].set_color(grid_color)
            self.ax.grid(axis='x', linestyle='--', alpha=0.5, color=grid_color)
            
            # Annotate values
            self.ax.bar_label(bars, fmt='%.1f min', padding=3, color=text_color)

        self.figure.tight_layout()
        self.canvas.draw()

class QuizPerformanceChart(QWidget):
    def __init__(self, scores: list, parent=None, is_dark=True):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.update_chart(scores, is_dark)

    def update_chart(self, scores: list, is_dark):
        self.ax.clear()
        
        bg_color = "#1e293b" if is_dark else "#ffffff"
        text_color = "#f8fafc" if is_dark else "#0f172a"
        line_color = "#10b981" if is_dark else "#10b981"
        grid_color = "#334155" if is_dark else "#e2e8f0"
        
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        if not scores:
            self.ax.text(0.5, 0.5, "No quizzes completed yet.", 
                         color=text_color, ha='center', va='center', fontsize=11)
            self.ax.set_axis_off()
        else:
            self.ax.set_axis_on()
            x = list(range(1, len(scores) + 1))
            
            self.ax.plot(x, scores, marker='o', color=line_color, linewidth=2, markersize=6)
            self.ax.set_ylabel("Score (%)", color=text_color, fontweight='bold')
            self.ax.set_xlabel("Quiz Number", color=text_color, fontweight='bold')
            self.ax.set_ylim(0, 105)
            
            self.ax.tick_params(colors=text_color)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(grid_color)
            self.ax.spines['bottom'].set_color(grid_color)
            self.ax.grid(linestyle='--', alpha=0.5, color=grid_color)

        self.figure.tight_layout()
        self.canvas.draw()
