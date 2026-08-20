import flet as ft
from eduai.services.ai_service import AIService

class AITutorView(ft.UserControl):
    def __init__(self, user, page: ft.Page):
        super().__init__()
        self.user = user
        self.page = page
        self.chat_history = []
        
        # UI controls references
        self.chat_column = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        self.chat_input = ft.TextField(
            placeholder="Ask EduAI a question...",
            expand=True,
            on_submit=self.handle_send_message
        )
        
        self.teach_input = ft.TextField(
            placeholder="Enter topic (e.g. Gravity, Osmosis)...",
            expand=True,
            on_submit=self.handle_run_teach_me
        )
        self.teach_display = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        
        self.init_chat()

    def init_chat(self):
        self.chat_column.controls.append(
            self.build_chat_bubble(
                "EduAI",
                "Hello! I am EduAI, your personal study tutor. What concept are we learning today?",
                is_user=False
            )
        )

    def build_chat_bubble(self, sender, text, is_user):
        avatar = ft.Container(
            content=ft.Text("ME" if is_user else "AI", size=10, weight=ft.FontWeight.BOLD),
            bgcolor=ft.colors.INDIGO_600 if is_user else ft.colors.GREY_800,
            width=24,
            height=24,
            border_radius=12,
            alignment=ft.alignment.center
        )
        bubble_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"{sender}:", size=10, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400 if is_user else ft.colors.GREY_300),
                    ft.Markdown(text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
                ],
                spacing=3
            ),
            bgcolor=ft.colors.with_opacity(0.1, ft.colors.INDIGO_500) if is_user else ft.colors.GREY_900,
            padding=10,
            border_radius=12,
            expand=False
        )
        
        return ft.Row(
            [avatar, bubble_card] if not is_user else [bubble_card, avatar],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    def handle_send_message(self, e):
        text = self.chat_input.value.strip()
        if not text:
            return
        
        self.chat_input.value = ""
        self.chat_input.disabled = True
        self.page.update()
        
        self.chat_column.controls.append(self.build_chat_bubble(self.user["username"], text, is_user=True))
        self.chat_history.append(("Student", text))
        self.page.update()
        
        self.page.run_thread(self.fetch_ai_response, text)

    def fetch_ai_response(self, query):
        try:
            level = f"Class {self.user['level'] + 7}"
            response = AIService.get_chat_response(query, self.chat_history, class_level=level)
            self.chat_column.controls.append(self.build_chat_bubble("EduAI", response, is_user=False))
            self.chat_history.append(("EduAI", response))
        except Exception as e:
            self.chat_column.controls.append(self.build_chat_bubble("System", f"⚠️ AI Request failed: {str(e)}", is_user=False))
        finally:
            self.chat_input.disabled = False
            self.page.update()

    def handle_run_teach_me(self, e):
        topic = self.teach_input.value.strip()
        if not topic:
            return
        
        self.teach_input.value = ""
        self.teach_input.disabled = True
        self.teach_display.controls.clear()
        self.teach_display.controls.append(ft.ProgressRing(color=ft.colors.EMERALD_500))
        self.page.update()
        
        self.page.run_thread(self.fetch_teach_me_lesson, topic)

    def fetch_teach_me_lesson(self, topic):
        try:
            level = f"Class {self.user['level'] + 7}"
            lesson = AIService.generate_teach_me_lesson(topic, class_level=level)
            
            self.teach_display.controls.clear()
            self.teach_display.controls.append(ft.Text(f"Lesson Plan: {topic.upper()}", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.EMERALD_400))
            
            # 1. Prerequisites
            self.teach_display.controls.append(ft.Text("1. What you need to know first", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400))
            pre_col = ft.Column(spacing=2)
            for pre in lesson.get("prerequisites", []):
                pre_col.controls.append(ft.Text(f"• {pre}", size=11))
            self.teach_display.controls.append(pre_col)
            
            # 2. Explanation
            self.teach_display.controls.append(ft.Text("2. Simple Explanation", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400))
            self.teach_display.controls.append(ft.Text(lesson.get("explanation", ""), size=11))
            
            # 3. Analogy
            self.teach_display.controls.append(ft.Text("3. Real-life Analogy", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400))
            self.teach_display.controls.append(ft.Text(f"\"{lesson.get('analogy', '')}\"", size=11, italic=True))
            
            # 4. Worked Example
            self.teach_display.controls.append(ft.Text("4. Worked Example", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400))
            self.teach_display.controls.append(
                ft.Container(
                    content=ft.Text(lesson.get("worked_example", ""), size=11, font_family="Consolas"),
                    bgcolor=ft.colors.GREY_950,
                    padding=10,
                    border_radius=8
                )
            )
            
            # 5. Pitfalls
            self.teach_display.controls.append(ft.Text("5. Common Student Mistakes", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.RED_400))
            err_col = ft.Column(spacing=2)
            for err in lesson.get("common_mistakes", []):
                err_col.controls.append(ft.Text(f"• {err}", size=11))
            self.teach_display.controls.append(err_col)
            
            # 6. Summary
            self.teach_display.controls.append(ft.Text("6. Quick Revision Summary", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.INDIGO_400))
            self.teach_display.controls.append(ft.Text(lesson.get("summary", ""), size=11))
            
        except Exception as e:
            self.teach_display.controls.clear()
            self.teach_display.controls.append(ft.Text(f"⚠️ Load failed: {str(e)}", size=12, color=ft.colors.RED_400))
        finally:
            self.teach_input.disabled = False
            self.page.update()

    def use_helper_prompt(self, command):
        concept = self.chat_input.value.strip()
        if not concept:
            # show prompt
            self.show_snack("Type a topic concept in the text input box first, then click helper buttons!")
            return
        self.chat_input.value = f"{command} regarding: {concept}"
        self.handle_send_message(None)

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        # Splitter row
        return ft.Row(
            [
                # Chatbot panel
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🤖 EduAI Chatbot Assistant", size=14, weight=ft.FontWeight.BOLD),
                            self.chat_column,
                            ft.Row(
                                [
                                    ft.TextButton("Explain Simply", on_click=lambda e: self.use_helper_prompt("Explain simply")),
                                    ft.TextButton("Give Example", on_click=lambda e: self.use_helper_prompt("Provide daily life examples of")),
                                    ft.TextButton("Summarize", on_click=lambda e: self.use_helper_prompt("Summarize in bullets"))
                                ],
                                spacing=5
                            ),
                            ft.Row(
                                [
                                    self.chat_input,
                                    ft.IconButton(ft.icons.SEND_ROUNDED, on_click=self.handle_send_message)
                                ],
                                spacing=5
                            )
                        ],
                        spacing=8,
                        expand=True
                    ),
                    expand=True,
                    padding=10
                ),
                
                ft.VerticalDivider(),
                
                # Teach Me panel
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🎓 'Teach Me' AI Tutor", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Enter any study concept to receive an interactive lesson", size=10, color=ft.colors.GREY_400),
                            ft.Row(
                                [
                                    self.teach_input,
                                    ft.IconButton(ft.icons.WIZARD_ROUNDED, on_click=self.handle_run_teach_me)
                                ],
                                spacing=5
                            ),
                            self.teach_display
                        ],
                        spacing=8,
                        expand=True
                    ),
                    expand=True,
                    padding=10
                )
            ],
            spacing=10,
            expand=True
        )
