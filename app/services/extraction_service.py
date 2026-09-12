import re


class ExtractionService:

    SKILLS = [
        "Python",
        "C++",
        "C",
        "Java",
        "JavaScript",
        "Node.js",
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

    SKILL_ALIASES = {
        "JavaScript": ["JavaScript", "JS"],
        "PostgreSQL": ["PostgreSQL", "Postgres"],
        "Scikit-learn": ["Scikit-learn", "Scikit learn", "sklearn"],
        "Node.js": ["Node.js", "NodeJS", "Node"],
    }

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
    def _skill_pattern(alias: str):
        boundary_chars = "A-Za-z0-9"

        if alias.lower() == "c":
            boundary_chars = "A-Za-z0-9+.#"

        return (
            rf"(?<![{boundary_chars}])"
            + re.escape(alias.lower())
            + rf"(?![{boundary_chars}])"
        )

    @staticmethod
    def extract_skills(text: str):

        found_skills = []

        text_lower = text.lower()

        for skill in ExtractionService.SKILLS:
            aliases = ExtractionService.SKILL_ALIASES.get(
                skill,
                [skill]
            )

            for alias in aliases:
                pattern = ExtractionService._skill_pattern(alias)

                if re.search(pattern, text_lower):
                    found_skills.append(skill)
                    break

        return list(dict.fromkeys(found_skills))

    @staticmethod
    def extract_years_experience(text: str):
        patterns = [
            r"(\d+)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience",
            r"experience\s*(?:of\s*)?(\d+)\+?\s*(?:years|yrs)",
            r"minimum\s+(\d+)\+?\s*(?:years|yrs)",
            r"at\s+least\s+(\d+)\+?\s*(?:years|yrs)",
        ]

        matches = []

        for pattern in patterns:
            matches.extend(
                int(match)
                for match in re.findall(pattern, text, flags=re.IGNORECASE)
            )

        return min(matches) if matches else None

    @staticmethod
    def extract_requirements(text: str):
        requirements = []

        for line in text.splitlines():
            cleaned = line.strip()

            if not cleaned:
                continue

            cleaned = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", cleaned).strip()

            if not cleaned:
                continue

            lowered = cleaned.lower()
            looks_like_requirement = (
                "experience" in lowered
                or "must" in lowered
                or "required" in lowered
                or "proficient" in lowered
                or "knowledge" in lowered
                or "familiar" in lowered
                or "ability" in lowered
                or bool(ExtractionService.extract_skills(cleaned))
            )

            if looks_like_requirement:
                requirements.append(cleaned)

        return list(dict.fromkeys(requirements))[:12]
