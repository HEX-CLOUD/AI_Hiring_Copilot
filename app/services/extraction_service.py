import re


class ExtractionService:

    SKILLS = [
        "Python",
        "C++",
        "C",
        "Java",
        "JavaScript",
        "SQL",
        "FastAPI",
        "Streamlit",
        "Docker",
        "Git",
        "GitHub",
        "Linux",
        "TensorFlow",
        "Keras",
        "Scikit-learn",
        "OpenCV",
        "NumPy",
        "Pandas",
        "LangChain",
        "LangGraph",
        "CrewAI",
        "PostgreSQL",
        "MongoDB",
        "ChromaDB",
        "RAG"
    ]

    @staticmethod
    def extract_email(text: str):
        match = re.search(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text
        )
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str):
        match = re.search(
            r"(\+91[- ]?)?[6-9]\d{9}",
            text
        )
        return match.group(0) if match else None

    @staticmethod
    def extract_name(text: str):
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if len(line) > 3:
                return line

        return None

    @staticmethod
    def extract_skills(text: str):

        found_skills = []

        text_lower = text.lower()

        for skill in ExtractionService.SKILLS:

            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills