import os

class FileHandler:
    @staticmethod
    def export_notes_to_txt(filepath: str, title: str, content: str) -> bool:
        """
        Exports a topic's notes to a text file.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== STUDYFLOW NOTES: {title.upper()} ===\n\n")
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def export_quiz_results(filepath: str, student_name: str, quiz_title: str, score: float, total: int, explanation_data: str) -> bool:
        """
        Exports quiz summary report.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== STUDYFLOW QUIZ REPORT ===\n")
                f.write(f"Student: {student_name}\n")
                f.write(f"Quiz: {quiz_title}\n")
                f.write(f"Score: {score}/{total} ({round((score/total)*100, 1)}%)\n")
                f.write(f"Date: {os.path.basename(filepath)}\n\n")
                f.write("=== DETAILS & CORRECTIONS ===\n")
                f.write(explanation_data)
            return True
        except Exception:
            return False
