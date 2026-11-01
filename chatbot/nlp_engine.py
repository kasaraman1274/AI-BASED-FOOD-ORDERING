import json
import os
import random
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .multilingual import detect_language, t, get_quick_replies

# Ensure required NLTK data is downloaded safely
import nltk.pathsec
nltk.pathsec.ALLOW_PROXIED_FETCH = True

for _res in ('tokenizers/punkt_tab', 'tokenizers/punkt', 'corpora/stopwords'):
    try:
        nltk.data.find(_res)
    except LookupError:
        try:
            nltk.download(_res.split('/')[-1])
        except Exception:
            pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_PATH = os.path.join(BASE_DIR, 'chatbot', 'dataset', 'intents.json')

with open(INTENTS_PATH, 'r', encoding='utf-8') as file:
    intents_data = json.load(file)

def preprocess_intents():
    corpus = []
    tags = []
    for intent in intents_data['intents']:
        for pattern in intent['patterns']:
            corpus.append(pattern.lower())
            tags.append(intent['tag'])
    return corpus, tags

CORPUS, TAGS = preprocess_intents()

# Initialize Vectorizer with Unicode support: handles Devanagari script (Hindi), Spanish accents, and English
vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', ngram_range=(1, 2), stop_words=None)
X = vectorizer.fit_transform(CORPUS)

# Multilingual number mappings
MULTILINGUAL_NUMBERS = {
    # English
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'a': 1, 'an': 1, 'single': 1, 'couple': 2, 'pair': 2,
    # Hindi (Devanagari & Latin)
    'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पाँच': 5, 'पांच': 5,
    'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'paanch': 5,
    '१': 1, '२': 2, '३': 3, '४': 4, '५': 5,
    # Spanish
    'uno': 1, 'una': 1, 'un': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
    'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10
}

def extract_quantity(text):
    """Extract numeric or worded quantity in English, Hindi, or Spanish."""
    text_lower = text.lower()
    
    # 1. Standard digits
    digit_match = re.search(r'\b(\d+)\b', text_lower)
    if digit_match:
        qty = int(digit_match.group(1))
        if 1 <= qty <= 50:
            return qty
            
    # 2. Devanagari digits (१, २, ३...)
    devanagari_digits = {'०': 0, '१': 1, '२': 2, '३': 3, '४': 4, '५': 5, '६': 6, '७': 7, '८': 8, '९': 9}
    for char, val in devanagari_digits.items():
        if char in text:
            return val

    # 3. Word numbers
    for word, val in MULTILINGUAL_NUMBERS.items():
        if re.search(r'(?u)\b' + re.escape(word) + r'\b', text_lower):
            return val
            
    return 1

def extract_price_limit(text):
    """Extract budget constraint in English, Hindi, or Spanish."""
    text_lower = text.lower()
    # Matches: 'under 500', 'below 800', '500 se kam', 'menos de 500', 'menos que 600', 'máximo 800'
    match = re.search(r'(?:under|below|less than|max|budget(?: of)?|menos de|menos que|máximo|se kam|kam me)\s*₹?\s*(\d+)', text_lower)
    if match:
        return float(match.group(1))
    # Alternative: '500 रुपये से कम'
    match_hi = re.search(r'(\d+)\s*(?:रुपये|rupaye|rs)?\s*(?:से कम|se kam)', text_lower)
    if match_hi:
        return float(match_hi.group(1))
    return None

def predict_intent(user_input, preferred_lang=None):
    """
    Predicts the intent of user_input with full multilingual support.
    Detects language (en, hi, es) and provides localized responses.
    """
    clean_input = user_input.strip()
    detected_lang = detect_language(clean_input, fallback_lang=preferred_lang or 'en')

    if not clean_input:
        return {
            "tag": "unknown",
            "score": 0.0,
            "response": t('GREETING', detected_lang),
            "action": None,
            "quick_replies": get_quick_replies('default', detected_lang),
            "entities": {"quantity": 1, "price_limit": None},
            "detected_lang": detected_lang
        }

    user_vec = vectorizer.transform([clean_input.lower()])
    similarities = cosine_similarity(user_vec, X)
    best_match_idx = similarities.argmax()
    best_match_score = float(similarities[0, best_match_idx])
    
    predicted_tag = TAGS[best_match_idx]
    matched_intent = None
    for intent in intents_data['intents']:
        if intent['tag'] == predicted_tag:
            matched_intent = intent
            break

    quantity = extract_quantity(clean_input)
    price_limit = extract_price_limit(clean_input)

    # Keyword safety overrides if similarity is low or ambiguous
    lower_input = clean_input.lower()
    if any(w in lower_input for w in ['pizza', 'पिज़्ज़ा', 'pizzas']):
        if not any(w in lower_input for w in ['add', 'order', 'जोड़ो', 'डालो', 'añadir', 'agregar', 'pedir']):
            predicted_tag = 'pizza'
    elif any(w in lower_input for w in ['burger', 'बर्गर', 'hamburguesa', 'burgers', 'hamburguesas']):
        if not any(w in lower_input for w in ['add', 'order', 'जोड़ो', 'डालो', 'añadir', 'agregar', 'pedir']):
            predicted_tag = 'burger'
    elif any(w in lower_input for w in ['dessert', 'मीठा', 'मिठाई', 'ब्राउनी', 'चीज़केक', 'postre', 'postres', 'pastel']):
        predicted_tag = 'dessert'
    elif any(w in lower_input for w in ['cart', 'कार्ट', 'टोकरी', 'carrito']):
        if any(w in lower_input for w in ['clear', 'empty', 'खाली', 'साफ़', 'vaciar', 'limpiar', 'borrar']):
            predicted_tag = 'clear_cart'
        elif any(w in lower_input for w in ['show', 'view', 'दिखाओ', 'चेक', 'ver', 'abrir']) or predicted_tag == 'cart':
            predicted_tag = 'cart'
    elif any(w in lower_input for w in ['order', 'ऑर्डर', 'pedido']):
        if any(w in lower_input for w in ['kahan', 'where', 'status', 'स्थिति', 'dónde', 'rastrear', 'track']):
            predicted_tag = 'order_status'

    # Fallback if similarity is very low
    if best_match_score < 0.16 and predicted_tag == TAGS[best_match_idx]:
        return {
            "tag": "fallback",
            "score": best_match_score,
            "response": t('FALLBACK', detected_lang),
            "action": None,
            "quick_replies": get_quick_replies('default', detected_lang),
            "entities": {"quantity": quantity, "price_limit": price_limit},
            "detected_lang": detected_lang
        }

    action = matched_intent.get('action') if matched_intent else None
    quick_replies = get_quick_replies('default', detected_lang)

    # Localized default response for general conversation intents
    if predicted_tag == 'greeting':
        resp_text = t('GREETING', detected_lang)
    elif predicted_tag == 'goodbye':
        resp_text = t('GOODBYE', detected_lang)
    elif predicted_tag == 'thanks':
        resp_text = t('THANKS', detected_lang)
    elif predicted_tag == 'delivery_time':
        resp_text = t('DELIVERY_TIME', detected_lang)
    else:
        resp_text = random.choice(matched_intent['responses']) if matched_intent else t('FALLBACK', detected_lang)

    return {
        "tag": predicted_tag,
        "score": best_match_score,
        "response": resp_text,
        "action": action,
        "quick_replies": quick_replies,
        "entities": {
            "quantity": quantity,
            "price_limit": price_limit,
            "raw_text": clean_input
        },
        "detected_lang": detected_lang
    }

def get_response(user_input):
    """Backward compatibility wrapper returning response and action."""
    pred = predict_intent(user_input)
    return {
        "response": pred["response"],
        "action": pred["action"]
    }
