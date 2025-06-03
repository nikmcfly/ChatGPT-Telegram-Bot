# resume_detector_improved.py
import re
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class ImprovedResumeDetector:
    def __init__(self):
        # Expanded keywords for better resume detection
        self.resume_keywords = {
            'en': [
                'resume', 'cv', 'curriculum vitae', 'experience', 'education', 
                'skills', 'work history', 'employment', 'qualifications',
                'professional summary', 'career objective', 'achievements',
                'responsibilities', 'references', 'internship', 'projects',
                'certifications', 'languages', 'contact information'
            ],
            'ru': [
                'резюме', 'cv', 'опыт работы', 'образование', 'навыки', 
                'трудовой опыт', 'карьера', 'квалификация', 'достижения',
                'обязанности', 'профессиональные навыки', 'о себе',
                'контактная информация', 'стаж', 'должность', 'компания',
                'сертификаты', 'языки', 'рекомендации', 'портфолио'
            ],
            'kk': [
                'резюме', 'жұмыс тәжірибесі', 'білім', 'дағдылар', 'мансап',
                'біліктілік', 'жетістіктер', 'міндеттер', 'байланыс ақпараты',
                'кәсіби дағдылар', 'өзім туралы', 'тілдер', 'сертификаттар',
                'ұсыныстар', 'жоба', 'тағылымдама'
            ]
        }
        
        # Job titles and positions
        self.job_titles = {
            'en': [
                'manager', 'engineer', 'developer', 'analyst', 'designer',
                'coordinator', 'specialist', 'consultant', 'director',
                'supervisor', 'assistant', 'intern', 'trainee', 'lead'
            ],
            'ru': [
                'менеджер', 'инженер', 'разработчик', 'аналитик', 'дизайнер',
                'координатор', 'специалист', 'консультант', 'директор',
                'руководитель', 'ассистент', 'стажер', 'практикант', 'ведущий'
            ],
            'kk': [
                'менеджер', 'инженер', 'әзірлеуші', 'талдаушы', 'дизайнер',
                'үйлестіруші', 'маман', 'кеңесші', 'директор', 'жетекші',
                'көмекші', 'тағылымдамашы', 'практикант'
            ]
        }
        
        # Educational institutions
        self.education_keywords = {
            'en': ['university', 'college', 'institute', 'school', 'academy',
                   'bachelor', 'master', 'phd', 'degree', 'diploma'],
            'ru': ['университет', 'колледж', 'институт', 'школа', 'академия',
                   'бакалавр', 'магистр', 'аспирантура', 'диплом', 'степень'],
            'kk': ['университет', 'колледж', 'институт', 'мектеп', 'академия',
                   'бакалавр', 'магистр', 'докторантура', 'диплом', 'дәреже']
        }
        
        # Expanded language indicators
        self.language_indicators = {
            'kk': [
                'қазақстан', 'университеті', 'білім', 'жұмыс', 'тәжірибе',
                'мен', 'және', 'үшін', 'бойынша', 'туралы', 'қаласы',
                'облысы', 'ақпан', 'наурыз', 'сәуір', 'мамыр', 'маусым',
                'шілде', 'тамыз', 'қыркүйек', 'қазан', 'қараша', 'желтоқсан'
            ],
            'ru': [
                'россия', 'казахстан', 'университет', 'образование', 'работа', 
                'опыт', 'я', 'и', 'для', 'по', 'о', 'город', 'область',
                'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'
            ],
            'en': [
                'university', 'education', 'experience', 'work', 'skills',
                'i', 'and', 'for', 'the', 'of', 'to', 'in', 'at',
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december'
            ]
        }
    
    def calculate_resume_score(self, text: str) -> Dict[str, float]:
        """Calculate detailed resume detection score"""
        text_lower = text.lower()
        scores = {
            'keyword_score': 0,
            'pattern_score': 0,
            'structure_score': 0,
            'total_score': 0
        }
        
        # 1. Keyword scoring (weighted by language)
        keyword_matches = 0
        total_keywords = 0
        for lang_keywords in self.resume_keywords.values():
            for keyword in lang_keywords:
                total_keywords += 1
                if keyword in text_lower:
                    keyword_matches += 1
        
        scores['keyword_score'] = (keyword_matches / max(total_keywords, 1)) * 100
        
        # 2. Pattern scoring
        patterns = [
            (r'\b(?:phone|телефон|байланыс)[\s:]*[\+\d\s\-\(\)]+', 2),  # Phone with weight
            (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', 2),  # Email
            (r'\b\d{4}\s*[-–]\s*(?:\d{4}|present|настоящее время|қазір)\b', 1.5),  # Date ranges
            (r'\b(?:github|linkedin|portfolio)\s*[:\s]*(?:https?://)?[\w\./\-]+', 1),  # Links
            (r'(?:^|\n)\s*[•·▪▫◦‣⁃]\s*', 1),  # Bullet points
            (r'(?:^|\n)\s*\d+\.\s*', 1),  # Numbered lists
        ]
        
        pattern_weight_sum = 0
        pattern_match_sum = 0
        for pattern, weight in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE))
            if matches > 0:
                pattern_match_sum += min(matches * weight, weight * 3)  # Cap at 3 matches
            pattern_weight_sum += weight * 3
        
        scores['pattern_score'] = (pattern_match_sum / pattern_weight_sum) * 100
        
        # 3. Structure scoring
        structure_indicators = [
            any(keyword in text_lower for keyword in ['education', 'образование', 'білім']),
            any(keyword in text_lower for keyword in ['experience', 'опыт', 'тәжірибе']),
            any(keyword in text_lower for keyword in ['skills', 'навыки', 'дағдылар']),
            len(text) > 200,  # Minimum length
            len(text.split('\n')) > 5,  # Multiple lines
        ]
        
        scores['structure_score'] = (sum(structure_indicators) / len(structure_indicators)) * 100
        
        # Calculate total weighted score
        scores['total_score'] = (
            scores['keyword_score'] * 0.4 +
            scores['pattern_score'] * 0.3 +
            scores['structure_score'] * 0.3
        )
        
        return scores
    
    def is_resume(self, text: str, threshold: float = 40.0) -> bool:
        """Detect if uploaded document is a resume with confidence scoring"""
        scores = self.calculate_resume_score(text)
        
        logger.info(f"Resume detection scores: {scores}")
        
        return scores['total_score'] >= threshold
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect document language with confidence score"""
        text_lower = text.lower()
        
        # Count character frequency for each language
        language_scores = {}
        
        for lang, indicators in self.language_indicators.items():
            score = 0
            word_count = 0
            
            # Count indicator words
            for indicator in indicators:
                count = text_lower.count(indicator)
                if count > 0:
                    # Weight common words less
                    weight = 1.0 if len(indicator) > 3 else 0.5
                    score += count * weight
                    word_count += count
            
            # Normalize by text length
            text_words = len(text.split())
            if text_words > 0:
                language_scores[lang] = (score / text_words) * 100
            else:
                language_scores[lang] = 0
        
        # Find the language with highest score
        if not language_scores:
            return 'ru', 0.0  # Default to Russian with no confidence
        
        best_lang = max(language_scores, key=language_scores.get)
        confidence = language_scores[best_lang]
        
        # If confidence is too low, check for Cyrillic vs Latin characters
        if confidence < 5:
            cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', text))
            latin_count = len(re.findall(r'[a-zA-Z]', text))
            
            if cyrillic_count > latin_count * 2:
                # Likely Russian or Kazakh
                if 'қ' in text_lower or 'ғ' in text_lower or 'ұ' in text_lower:
                    best_lang = 'kk'
                else:
                    best_lang = 'ru'
                confidence = 60.0
            elif latin_count > cyrillic_count * 2:
                best_lang = 'en'
                confidence = 60.0
        
        logger.info(f"Language detection: {best_lang} (confidence: {confidence:.1f}%)")
        
        return best_lang, confidence
    
    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from resume"""
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None
        }
        
        # Email
        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Phone (various formats)
        phone_patterns = [
            r'\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',  # +7 xxx xxx xx xx
            r'\+\d{1,3}\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}',  # +7 (xxx) xxx-xx-xx
            r'\d{11}',  # 7xxxxxxxxxx
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact_info['phone'] = phone_match.group()
                break
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group()
        
        # GitHub
        github_match = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
        if github_match:
            contact_info['github'] = github_match.group()
        
        return contact_info