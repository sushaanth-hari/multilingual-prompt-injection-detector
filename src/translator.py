from langdetect import detect
from deep_translator import GoogleTranslator

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang  # returns 'en', 'fr', 'hi', 'ta', etc.
    except:
        return "unknown"

def translate_to_english(text: str) -> str:
    try:
        lang = detect_language(text)
        if lang == "en" or lang == "unknown":
            return text  # already English
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except:
        return text  # if translation fails, return original

def get_language_info(text: str) -> dict:
    lang = detect_language(text)
    translated = translate_to_english(text)
    return {
        "original_text": text,
        "detected_language": lang,
        "translated_text": translated
    }