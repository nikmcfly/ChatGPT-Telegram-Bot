# resume_detector.py
import re
from typing import Tuple, Optional

class ResumeDetector:
    def __init__(self):
        # Keywords that indicate this is a resume
        self.resume_keywords = {
            'en': ['resume', 'cv', 'curriculum vitae', 'experience', 'education', 'skills', 'work history', 'employment'],
            'ru': ['резюме', 'cv', 'опыт работы', 'образование', 'навыки', 'трудовой опыт', 'карьера'],
            'kk': ['резюме', 'жұмыс тәжірибесі', 'білім', 'дағдылар', 'мансап']
        }
    
    def is_resume(self, text: str) -> bool:
        """Detect if uploaded document is a resume"""
        text_lower = text.lower()
        
        # Check for resume keywords
        for lang_keywords in self.resume_keywords.values():
            if any(keyword in text_lower for keyword in lang_keywords):
                return True
                
        # Check for typical resume patterns
        patterns = [
            r'\b(phone|email|address|телефон|почта|адрес)\b',
            r'\b\d{4}\s*[-–]\s*\d{4}\b',  # Date ranges like 2020-2023
            r'\b(university|college|университет|колледж)\b',
            r'\b(manager|engineer|developer|менеджер|инженер)\b'
        ]
        
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, text_lower))
        return pattern_matches >= 2
    
    def detect_language(self, text: str) -> str:
        """Detect document language"""
        # Simple keyword-based detection
        kk_indicators = ['қазақстан', 'университеті', 'білім', 'жұмыс', 'тәжірибе']
        ru_indicators = ['россия', 'университет', 'образование', 'работа', 'опыт']
        en_indicators = ['university', 'education', 'experience', 'work', 'skills']
        
        text_lower = text.lower()
        
        kk_score = sum(1 for word in kk_indicators if word in text_lower)
        ru_score = sum(1 for word in ru_indicators if word in text_lower)
        en_score = sum(1 for word in en_indicators if word in text_lower)
        
        if kk_score > max(ru_score, en_score):
            return 'kk'
        elif en_score > ru_score:
            return 'en'
        else:
            return 'ru'  # Default to Russian