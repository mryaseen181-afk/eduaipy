import json
import requests
from eduai.config import GEMINI_API_KEY

class AIService:
    @staticmethod
    def _call_gemini_api(prompt: str, system_instruction: str = "") -> str:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            response = requests.post(url, json=payload, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text
            raise Exception(f"API Error (Status {response.status_code}): {response.text}")
        except Exception as e:
            raise RuntimeError(f"AI API request failed: {str(e)}")

    @classmethod
    def get_chat_response(cls, user_message: str, chat_history: list = None, class_level: str = "Class 10") -> str:
        """
        EduAI Chatbot completion logic. Explains terms simply based on student's class level.
        """
        system_instruction = (
            f"You are EduAI, an expert AI tutor for school students. You are helping a student in {class_level}.\n"
            "Format your answers with beautiful markdown, using clear headers, bullet points, and code blocks for code or maths.\n"
            "Keep explanations simple, engaging, encouraging, and age-appropriate."
        )

        history_context = ""
        if chat_history:
            for speaker, msg in chat_history[-6:]:
                history_context += f"{speaker}: {msg}\n"
        
        prompt = f"{history_context}Student: {user_message}\nEduAI:"

        try:
            return cls._call_gemini_api(prompt, system_instruction)
        except Exception:
            # Fallback mock responses
            msg = user_message.lower()
            if "pythagoras" in msg:
                return (
                    "### Pythagoras' Theorem 📐\n\n"
                    "Pythagoras' Theorem is a core rule in geometry for right-angled triangles.\n\n"
                    "**The Formula**:\n"
                    "$$a^2 + b^2 = c^2$$\n"
                    "Where:\n"
                    "- $a$ and $b$ are the shorter sides (legs).\n"
                    "- $c$ is the longest side opposite the right angle (hypotenuse).\n\n"
                    "**Example**:\n"
                    "If a triangle has sides $a = 3$ cm and $b = 4$ cm, find $c$:\n"
                    "$$3^2 + 4^2 = c^2 \\implies 9 + 16 = c^2 \\implies 25 = c^2 \\implies c = 5\\text{ cm}$$\n\n"
                    "Need another example? Just ask!"
                )
            elif "photosynthesis" in msg:
                return (
                    "### Photosynthesis 🍃\n\n"
                    "Photosynthesis is the process plants use to make food using sunlight!\n\n"
                    "**The Chemical Equation**:\n"
                    "$$\\text{Carbon Dioxide} + \\text{Water} + \\text{Light} \\rightarrow \\text{Glucose} + \\text{Oxygen}$$\n\n"
                    "**How it works**:\n"
                    "1. **Chlorophyll** in leaves captures sunlight.\n"
                    "2. Roots absorb **water** from soil.\n"
                    "3. Leaves take in **carbon dioxide** from air.\n"
                    "4. The plant releases **oxygen** as a byproduct (which we breathe!)."
                )
            else:
                return (
                    f"### Hello! I am EduAI, your personal tutor.\n\n"
                    f"I received your question: \"*{user_message}*\"\n\n"
                    f"Since the GEMINI_API_KEY is not configured or reachable, I am running in Offline Sandbox Mode.\n"
                    f"To enable complete AI answers, please create a `.env` file in your workspace root containing:\n"
                    f"`GEMINI_API_KEY=your_real_key_here`"
                )

    @classmethod
    def generate_teach_me_lesson(cls, topic: str, class_level: str = "Class 10") -> dict:
        """
        Creates a custom lesson plan on a specific topic following the 'Teach Me' criteria.
        """
        prompt = (
            f"Generate a mini-lesson about '{topic}' for a {class_level} student.\n"
            "Format the output exactly as a JSON object with these keys:\n"
            "- prerequisites: list of strings (what you need to know first)\n"
            "- explanation: string (simple explanation of the core concept)\n"
            "- analogy: string (real-life analogy or metaphor)\n"
            "- worked_example: string (step-by-step solved problem)\n"
            "- common_mistakes: list of strings (what students often get wrong)\n"
            "- summary: string (final revision points)\n"
            "- quick_quiz: list of 2 MCQ questions. Each quiz element should be an object with keys: "
            "question (string), options (list of strings), correct_index (integer), explanation (string).\n\n"
            "Ensure it is valid JSON and contains only the JSON string, no markdown headers or trailing quotes."
        )

        try:
            raw_res = cls._call_gemini_api(prompt, "You are a helpful education JSON generator.")
            # Strip markdown wrappers if present
            cleaned = raw_res.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            # Fallback mock lesson
            return {
                "prerequisites": [
                    "Basic arithmetic rules",
                    "Understanding variables"
                ],
                "explanation": (
                    f"Analyzing '{topic}' reveals how the primary variables govern the entire system. "
                    "Each component has an independent state that combines to produce the final output."
                ),
                "analogy": (
                    "Think of it like cooking a recipe: if you miss one ingredient or alter the proportions, "
                    "the final taste changes completely."
                ),
                "worked_example": (
                    "Question: Calculate the balanced state.\n"
                    "Step 1: Write down the equilibrium state.\n"
                    "Step 2: Solve for the unknown factor: Output = Input * Efficiency.\n"
                    "Step 3: If Input is 10 units and Efficiency is 85%, the result is 8.5 units."
                ),
                "common_mistakes": [
                    "Forgetting to balance equations or match units.",
                    "Applying rules without checking boundary conditions."
                ],
                "summary": "Remember to write down known parameters, choose the correct formula, and double check calculations.",
                "quick_quiz": [
                    {
                        "question": f"Which of the following is crucial for understanding {topic}?",
                        "options": ["Applying variables correctly", "Ignoring prerequisites", "Guessing values", "Skipping calculation checks"],
                        "correct_index": 0,
                        "explanation": "Prerequisites and correct variable allocation are core to arriving at the right answer."
                    },
                    {
                        "question": "True or False: We should convert units to standard form before solving.",
                        "options": ["True", "False"],
                        "correct_index": 0,
                        "explanation": "Standardized units prevent calculation mismatches."
                    }
                ]
            }

    @classmethod
    def generate_ai_quiz(cls, subject: str, chapter: str, difficulty: str = "Medium", num_questions: int = 5) -> list:
        """
        Generates a custom list of quiz questions on a specific chapter.
        """
        prompt = (
            f"Generate a quiz with {num_questions} questions about '{chapter}' (Subject: {subject}) at a '{difficulty}' level.\n"
            "Include a mix of MCQs, True/False, and Fill-in-the-blank questions.\n"
            "Format the output exactly as a JSON list of objects, where each object has these keys:\n"
            "- question_text: string\n"
            "- question_type: string ('mcq', 'tf', or 'fill_in')\n"
            "- options: list of strings (for 'mcq' type, must have 4 options; for 'tf', must be ['True', 'False']; for 'fill_in', can be empty list)\n"
            "- correct_answer: string (should match the exact correct option or fill-in word)\n"
            "- explanation: string\n\n"
            "Ensure the response is a valid JSON array only, without markdown wrapping."
        )

        try:
            raw_res = cls._call_gemini_api(prompt, "You are a quiz JSON generator.")
            cleaned = raw_res.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            # Fallback mock quiz
            return [
                {
                    "question_text": f"What is the core theme of the chapter '{chapter}'?",
                    "question_type": "mcq",
                    "options": ["System Analysis", "Random guessing", "No main theme", "Historical context only"],
                    "correct_answer": "System Analysis",
                    "explanation": f"The chapter on '{chapter}' mainly details structural system analysis principles."
                },
                {
                    "question_text": f"The main equations in '{chapter}' require standard input variables. (True or False)",
                    "question_type": "tf",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "Consistent variable types are essential to make equations solvable."
                },
                {
                    "question_text": f"Complete the blank: The rate of change in a steady system is always ______.",
                    "question_type": "fill_in",
                    "options": [],
                    "correct_answer": "constant",
                    "explanation": "A steady system by definition does not accelerate, so change rate remains constant."
                }
            ]
