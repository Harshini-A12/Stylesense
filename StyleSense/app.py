"""
StyleSense - AI-Powered Fashion Styling Web Application
A premium GenAI-powered fashion recommendation system
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import cv2
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from groq import Groq
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'stylesense-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Groq client
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Database file path
DATABASE_FILE = 'database.json'


# ====================================
# DATABASE FUNCTIONS
# ====================================

def load_database():
    """Load database from JSON file"""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    return {"users": [], "styling_history": []}


def save_database(data):
    """Save database to JSON file"""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_user(email):
    """Get user by email"""
    db = load_database()
    for user in db['users']:
        if user['email'] == email:
            return user
    return None


def create_user(email, password):
    """Create new user"""
    db = load_database()
    
    # Check if user already exists
    if get_user(email):
        return False
    
    # Add new user
    db['users'].append({
        'email': email,
        'password': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    })
    
    save_database(db)
    return True


def save_styling_history(email, styling_data):
    """Save styling result to history"""
    db = load_database()
    
    db['styling_history'].append({
        'email': email,
        'date': datetime.now().isoformat(),
        'occasion': styling_data.get('occasion', 'N/A'),
        'skin_tone': styling_data.get('skin_tone', 'N/A'),
        'gender': styling_data.get('gender', 'N/A'),
        'age': styling_data.get('age', 'N/A'),
        'budget': styling_data.get('budget', 'N/A'),
        'result': styling_data.get('result', {})
    })
    
    save_database(db)


# ====================================
# SKIN TONE DETECTION
# ====================================

def detect_skin_tone(image_path):
    """
    Detect skin tone from facial image
    Returns: Fair, Medium, Olive, or Deep
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to HSV for better skin detection
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # Define skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Create mask for skin pixels
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Extract skin pixels
        skin_pixels = img[mask > 0]
        
        if len(skin_pixels) == 0:
            # Fallback: use center region
            h, w = img.shape[:2]
            center_region = img[h//3:2*h//3, w//3:2*w//3]
            avg_color = np.mean(center_region, axis=(0, 1))
        else:
            # Calculate average RGB value
            avg_color = np.mean(skin_pixels, axis=0)
        
        # Calculate brightness
        brightness = np.mean(avg_color)
        
        # Classify skin tone based on brightness
        if brightness > 200:
            return "Fair"
        elif brightness > 150:
            return "Medium"
        elif brightness > 100:
            return "Olive"
        else:
            return "Deep"
            
    except Exception as e:
        print(f"Error detecting skin tone: {e}")
        return "Medium"  # Default fallback


# ====================================
# OCCASION-SPECIFIC KEYWORD BUILDER
# ====================================

def build_occasion_keywords(occasion, gender='Female'):
    """
    Return curated, occasion-specific shopping keywords for each platform.
    Used as fallback AND for post-processing validation.
    """
    gender_lower = gender.lower() if gender else 'female'
    is_male = gender_lower in ('male', 'man', 'men')
    
    # Occasion-specific keyword maps
    occasion_keywords = {
        'Business': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} formal blazer",
                f"{'mens' if is_male else 'womens'} business suit",
                f"{'mens formal shirt' if is_male else 'womens structured dress'}",
                f"{'mens formal trousers' if is_male else 'womens formal trousers'}",
                f"{'mens oxford shoes' if is_male else 'womens formal pumps'}",
            ],
            'myntra': [
                f"{'men-blazers' if is_male else 'women-blazers'}",
                f"{'men-formal-shirts' if is_male else 'women-formal-tops'}",
                f"{'men-formal-trousers' if is_male else 'women-formal-trousers'}",
                f"{'men-formal-shoes' if is_male else 'women-formal-shoes'}",
                f"{'men-suits' if is_male else 'women-dresses'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} blazer",
                f"{'mens' if is_male else 'womens'} formal trousers",
                f"{'mens' if is_male else 'womens'} office shirt",
                f"{'mens' if is_male else 'womens'} structured dress",
                f"{'mens' if is_male else 'womens'} formal shoes",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} formal blazer",
                f"{'men' if is_male else 'women'} business wear",
                f"{'men' if is_male else 'women'} office outfit",
                f"{'men' if is_male else 'women'} formal trousers",
                f"{'men' if is_male else 'women'} formal shoes",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} formal wear",
                f"{'men' if is_male else 'women'} office blazer",
                f"{'men' if is_male else 'women'} business dress",
                f"{'men' if is_male else 'women'} formal trousers",
                f"{'men' if is_male else 'women'} workwear outfit",
            ],
        },
        'Formal': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} formal suit",
                f"{'mens tuxedo' if is_male else 'womens evening gown'}",
                f"{'mens formal shirt' if is_male else 'womens cocktail dress'}",
                f"{'mens dress shoes' if is_male else 'womens formal heels'}",
                f"formal accessories {'men' if is_male else 'women'}",
            ],
            'myntra': [
                f"{'men-suits' if is_male else 'women-gowns'}",
                f"{'men-formal-shirts' if is_male else 'women-dresses'}",
                f"{'men-formal-shoes' if is_male else 'women-heels'}",
                f"{'men-ties' if is_male else 'women-clutches'}",
                f"{'men-formal-trousers' if is_male else 'women-evening-dresses'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} formal suit",
                f"{'mens' if is_male else 'womens'} evening wear",
                f"{'mens' if is_male else 'womens'} dress shoes",
                f"{'mens' if is_male else 'womens'} formal shirt",
                f"{'mens' if is_male else 'womens'} formal accessories",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} formal suit",
                f"{'men' if is_male else 'women'} evening dress",
                f"{'men' if is_male else 'women'} formal shoes",
                f"{'men' if is_male else 'women'} formal accessories",
                f"{'men' if is_male else 'women'} formal wear",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} formal dress",
                f"{'men' if is_male else 'women'} evening gown",
                f"{'men' if is_male else 'women'} formal heels",
                f"{'men' if is_male else 'women'} formal accessories",
                f"{'men' if is_male else 'women'} formal outfit",
            ],
        },
        'Casual': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} casual t-shirt",
                f"{'mens' if is_male else 'womens'} casual jeans",
                f"{'mens' if is_male else 'womens'} sneakers",
                f"{'mens' if is_male else 'womens'} casual watch",
                f"{'mens' if is_male else 'womens'} casual outfit",
            ],
            'myntra': [
                f"{'men-tshirts' if is_male else 'women-tops-t-shirts'}",
                f"{'men-jeans' if is_male else 'women-jeans'}",
                f"{'men-casual-shoes' if is_male else 'women-casual-shoes'}",
                f"{'men-watches' if is_male else 'women-watches'}",
                f"{'men-shorts' if is_male else 'women-skirts'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} casual shirt",
                f"{'mens' if is_male else 'womens'} jeans",
                f"{'mens' if is_male else 'womens'} sneakers",
                f"{'mens' if is_male else 'womens'} casual jacket",
                f"{'mens' if is_male else 'womens'} casual outfit",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} casual wear",
                f"{'men' if is_male else 'women'} casual t-shirt",
                f"{'men' if is_male else 'women'} casual jeans",
                f"{'men' if is_male else 'women'} sneakers",
                f"{'men' if is_male else 'women'} casual accessories",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} casual top",
                f"{'men' if is_male else 'women'} casual bottom",
                f"{'men' if is_male else 'women'} casual dress",
                f"{'men' if is_male else 'women'} casual shoes",
                f"{'men' if is_male else 'women'} casual outfit",
            ],
        },
        'Party': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} party wear",
                f"{'mens party shirt' if is_male else 'womens party dress'}",
                f"{'mens' if is_male else 'womens'} party shoes",
                f"{'mens' if is_male else 'womens'} party accessories",
                f"{'mens party blazer' if is_male else 'womens sequin dress'}",
            ],
            'myntra': [
                f"{'men-party-wear' if is_male else 'women-party-wear'}",
                f"{'men-blazers-coats' if is_male else 'women-dresses'}",
                f"{'men-party-shoes' if is_male else 'women-heels'}",
                f"{'men-sunglasses' if is_male else 'women-clutches'}",
                f"{'men-shirts' if is_male else 'women-jumpsuits'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} party outfit",
                f"{'mens' if is_male else 'womens'} party shirt",
                f"{'mens' if is_male else 'womens'} party shoes",
                f"{'mens' if is_male else 'womens'} party blazer",
                f"{'mens' if is_male else 'womens'} party accessories",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} party wear",
                f"{'men' if is_male else 'women'} party outfit",
                f"{'men' if is_male else 'women'} party shoes",
                f"{'men' if is_male else 'women'} party dress",
                f"{'men' if is_male else 'women'} party accessories",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} party dress",
                f"{'men' if is_male else 'women'} party wear",
                f"{'men' if is_male else 'women'} party heels",
                f"{'men' if is_male else 'women'} party accessories",
                f"{'men' if is_male else 'women'} party outfit",
            ],
        },
        'Wedding': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} wedding outfit",
                f"{'mens sherwani' if is_male else 'womens lehenga'}",
                f"{'mens wedding shoes' if is_male else 'womens wedding heels'}",
                f"{'mens wedding accessories' if is_male else 'womens bridal jewelry'}",
                f"{'mens kurta pajama' if is_male else 'womens saree'}",
            ],
            'myntra': [
                f"{'men-sherwanis' if is_male else 'women-lehenga-choli'}",
                f"{'men-kurtas' if is_male else 'women-sarees'}",
                f"{'men-ethnic-shoes' if is_male else 'women-ethnic-shoes'}",
                f"{'men-ethnic-wear' if is_male else 'women-ethnic-wear'}",
                f"{'men-nehru-jackets' if is_male else 'women-dupatta-shawl'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} wedding suit",
                f"{'mens' if is_male else 'womens'} wedding outfit",
                f"{'mens' if is_male else 'womens'} formal wedding",
                f"{'mens' if is_male else 'womens'} wedding shoes",
                f"{'mens' if is_male else 'womens'} wedding accessories",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} wedding wear",
                f"{'men sherwani' if is_male else 'women lehenga'}",
                f"{'men' if is_male else 'women'} wedding ethnic",
                f"{'men' if is_male else 'women'} wedding shoes",
                f"{'men' if is_male else 'women'} wedding accessories",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} wedding outfit",
                f"{'men' if is_male else 'women'} wedding ethnic wear",
                f"{'men' if is_male else 'women'} wedding accessories",
                f"{'men' if is_male else 'women'} wedding shoes",
                f"{'men' if is_male else 'women'} wedding jewelry",
            ],
        },
        'Date Night': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} date night outfit",
                f"{'mens casual blazer' if is_male else 'womens bodycon dress'}",
                f"{'mens loafers' if is_male else 'womens heels'}",
                f"{'mens cologne' if is_male else 'womens perfume'}",
                f"{'mens smart casual' if is_male else 'womens date dress'}",
            ],
            'myntra': [
                f"{'men-casual-shirts' if is_male else 'women-dresses'}",
                f"{'men-blazers-coats' if is_male else 'women-tops'}",
                f"{'men-loafers' if is_male else 'women-heels'}",
                f"{'men-perfumes' if is_male else 'women-perfumes'}",
                f"{'men-smart-casual' if is_male else 'women-date-night-dresses'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} date outfit",
                f"{'mens' if is_male else 'womens'} smart casual",
                f"{'mens' if is_male else 'womens'} evening shirt",
                f"{'mens' if is_male else 'womens'} slim fit",
                f"{'mens' if is_male else 'womens'} date night",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} date outfit",
                f"{'men' if is_male else 'women'} smart casual",
                f"{'men' if is_male else 'women'} date night dress",
                f"{'men' if is_male else 'women'} evening wear",
                f"{'men' if is_male else 'women'} date accessories",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} date night outfit",
                f"{'men' if is_male else 'women'} evening dress",
                f"{'men' if is_male else 'women'} date night heels",
                f"{'men' if is_male else 'women'} date accessories",
                f"{'men' if is_male else 'women'} date perfume",
            ],
        },
        'Festival': {
            'amazon_india': [
                f"{'mens' if is_male else 'womens'} festival outfit",
                f"{'mens kurta' if is_male else 'womens anarkali suit'}",
                f"{'mens ethnic shoes' if is_male else 'womens juttis'}",
                f"{'mens festival accessories' if is_male else 'womens ethnic jewelry'}",
                f"{'mens ethnic wear' if is_male else 'womens festive saree'}",
            ],
            'myntra': [
                f"{'men-kurtas' if is_male else 'women-kurtas-kurtis'}",
                f"{'men-ethnic-wear' if is_male else 'women-ethnic-wear'}",
                f"{'men-ethnic-shoes' if is_male else 'women-ethnic-shoes'}",
                f"{'men-nehru-jackets' if is_male else 'women-sarees'}",
                f"{'men-ethnic-bottomwear' if is_male else 'women-lehenga-choli'}",
            ],
            'zara': [
                f"{'mens' if is_male else 'womens'} festive outfit",
                f"{'mens' if is_male else 'womens'} embroidered shirt",
                f"{'mens' if is_male else 'womens'} festive wear",
                f"{'mens' if is_male else 'womens'} colorful outfit",
                f"{'mens' if is_male else 'womens'} celebration wear",
            ],
            'ajio': [
                f"{'men' if is_male else 'women'} festive wear",
                f"{'men' if is_male else 'women'} ethnic wear",
                f"{'men' if is_male else 'women'} festival outfit",
                f"{'men' if is_male else 'women'} traditional wear",
                f"{'men' if is_male else 'women'} festive accessories",
            ],
            'nykaa_fashion': [
                f"{'men' if is_male else 'women'} festival outfit",
                f"{'men' if is_male else 'women'} ethnic wear",
                f"{'men' if is_male else 'women'} festive dress",
                f"{'men' if is_male else 'women'} festival accessories",
                f"{'men' if is_male else 'women'} festive jewelry",
            ],
        },
    }
    
    # Normalise occasion name for lookup
    occasion_key = occasion.strip().title() if occasion else 'Casual'
    
    # Return matched keywords or a sensible default
    if occasion_key in occasion_keywords:
        return occasion_keywords[occasion_key]
    
    # For custom occasions, default to casual
    return occasion_keywords.get('Casual', occasion_keywords['Casual'])


# ====================================
# OCCASION GUIDANCE FOR AI PROMPT
# ====================================

def get_occasion_guidance(occasion, gender='Female'):
    """
    Return explicit guidance text that tells the AI exactly what types of
    clothing are appropriate for the given occasion.
    """
    is_male = gender.lower() in ('male', 'man', 'men') if gender else False
    
    guidance = {
        'Business': (
            f"This is a BUSINESS/PROFESSIONAL setting. "
            f"{'He' if is_male else 'She'} needs professional office-appropriate clothing ONLY. "
            f"Recommend items such as: "
            f"{'tailored suits, formal blazers, dress shirts, formal trousers, Oxford shoes, leather belt, tie, briefcase' if is_male else 'structured blazers, formal blouses, tailored trousers, pencil skirts, formal dresses, pointed-toe pumps, leather tote, minimal jewelry'}. "
            f"DO NOT recommend casual wear, ethnic wear, party wear, skirts with casual prints, or any non-professional clothing."
        ),
        'Formal': (
            f"This is a FORMAL EVENT (gala, dinner, ceremony). "
            f"Recommend elegant, sophisticated clothing such as: "
            f"{'tuxedos, formal suits, dress shirts, cufflinks, formal leather shoes, bow tie' if is_male else 'evening gowns, cocktail dresses, silk blouses with formal trousers, stiletto heels, elegant clutch, statement jewelry'}. "
            f"DO NOT recommend casual, sporty, or everyday clothing."
        ),
        'Casual': (
            f"This is a CASUAL setting. "
            f"Recommend comfortable, relaxed but stylish clothing such as: "
            f"{'t-shirts, casual shirts, jeans, chinos, sneakers, casual watch' if is_male else 'casual tops, t-shirts, jeans, skirts, sneakers, crossbody bag, casual jewelry'}. "
            f"Keep it modern and trendy."
        ),
        'Party': (
            f"This is a PARTY/NIGHTLIFE event. "
            f"Recommend bold, statement pieces such as: "
            f"{'party blazers, stylish shirts, slim-fit trousers, loafers or boots, statement watch' if is_male else 'party dresses, sequin tops, jumpsuits, high heels, statement earrings, clutch bag'}. "
            f"Emphasize glamour and fun."
        ),
        'Wedding': (
            f"This is an INDIAN WEDDING event. "
            f"Recommend traditional/ethnic clothing such as: "
            f"{'sherwani, kurta pajama, Nehru jacket, mojari shoes, traditional accessories' if is_male else 'lehenga choli, saree, anarkali suit, ethnic juttis, traditional jewelry, dupatta'}. "
            f"Emphasize rich fabrics, embroidery, and festive colors."
        ),
        'Date Night': (
            f"This is a DATE NIGHT. "
            f"Recommend attractive, smart-casual to semi-formal clothing such as: "
            f"{'smart blazer, well-fitted shirt, slim trousers or dark jeans, loafers, cologne, elegant watch' if is_male else 'flattering dress, stylish top with jeans, heeled boots or pumps, delicate jewelry, perfume, small handbag'}. "
            f"Focus on making a great impression."
        ),
        'Festival': (
            f"This is a FESTIVAL/FESTIVE event. "
            f"Recommend vibrant, ethnic/traditional clothing such as: "
            f"{'kurtas, ethnic jackets, Nehru jackets, ethnic footwear, traditional accessories' if is_male else 'kurtis, anarkali suits, sarees, lehengas, ethnic footwear, traditional jewelry, bangles'}. "
            f"Emphasize color, celebration, and cultural richness."
        ),
    }
    
    occasion_key = occasion.strip().title() if occasion else 'Casual'
    return guidance.get(occasion_key, 
        f"This is for a '{occasion}' event. Recommend clothing specifically appropriate for this type of event. "
        f"Make sure every outfit piece and shopping keyword directly relates to '{occasion}'.")


# ====================================
# AI STYLING GENERATION
# ====================================

def generate_styling_recommendation(user_data):
    """
    Generate fashion styling recommendation using Groq AI
    """
    
    # Prepare preferred colors string
    preferred_colors = user_data.get('preferred_colors', '')
    if not preferred_colors or preferred_colors.strip() == '':
        preferred_colors = "No specific preference"
    
    occasion = user_data.get('occasion', 'Casual')
    gender = user_data.get('gender', 'Female')
    
    # Get occasion-specific guidance
    occasion_guide = get_occasion_guidance(occasion, gender)
    
    # Create structured prompt with strong occasion enforcement
    prompt = f"""You are a professional fashion stylist and color theory expert.

User Details:
- Skin Tone: {user_data['skin_tone']}
- Gender: {gender}
- Age: {user_data['age']}
- Occasion/Event: {occasion}
- Budget: {user_data['budget']}
- Preferred Colors (optional): {preferred_colors}

=== CRITICAL OCCASION REQUIREMENT ===
{occasion_guide}
Every single item you recommend (top, bottom, shoes, accessories) MUST be appropriate for "{occasion}".
Every shopping keyword MUST be a search term that would return {occasion}-appropriate clothing on that platform.
DO NOT include any clothing items or keywords that are unrelated to "{occasion}".

=== OUTFIT VARIETY RULE ===
DO NOT default to generic "blouse" or "silk blouse" for every occasion.
Use occasion-specific garment names instead:
- Business: blazer, formal shirt, structured dress, power suit, pencil skirt
- Casual: t-shirt, crop top, casual shirt, hoodie, denim jacket
- Party: sequin top, bodycon dress, jumpsuit, off-shoulder top, cocktail dress  
- Wedding: sherwani, lehenga, saree, kurta, anarkali suit
- Formal: tuxedo, evening gown, cocktail dress, formal suit
- Date Night: wrap dress, smart shirt, fitted blazer, midi dress
- Festival: kurta, kurti, ethnic top, embroidered jacket
Be SPECIFIC with the exact garment type - not just "elegant top" or "stylish blouse".
=== END RULES ===

Generate a structured fashion recommendation including:

1. Outfit (ALL items must be appropriate for {occasion}):
   - Top: specific {occasion}-appropriate garment
   - Bottom: specific {occasion}-appropriate garment
   - Shoes: specific {occasion}-appropriate footwear
   - Accessories: specific {occasion}-appropriate accessories

2. Hairstyle recommendation suitable for {occasion}

3. Color palette:
   - Primary
   - Secondary
   - Accent

4. Clear explanation of why these styles and colors suit the user's skin tone, age, occasion, and budget

5. 5 shopping search keywords for EACH platform. Each keyword MUST be a product search term
   that returns {occasion}-appropriate clothing for {gender}:
   - Amazon India (e.g. "{gender.lower()} {occasion.lower()} blazer")
   - Myntra (use hyphenated slug format e.g. "{'men' if gender.lower() == 'male' else 'women'}-formal-blazers")
   - Zara (e.g. "{gender.lower()} {occasion.lower()} outfit")
   - Ajio (e.g. "{'men' if gender.lower() == 'male' else 'women'} {occasion.lower()} wear")
   - Nykaa Fashion (e.g. "{'men' if gender.lower() == 'male' else 'women'} {occasion.lower()} dress")

Ensure recommendations are:
- Modern and trend-aware
- Elegant and personalized
- Suitable for Indian fashion preferences
- STRICTLY matching the "{occasion}" occasion

Format your response as JSON with the following structure:
{{
  "outfit": {{
    "top": "description",
    "bottom": "description",
    "shoes": "description",
    "accessories": "description"
  }},
  "hairstyle": "description",
  "color_palette": {{
    "primary": "color name",
    "secondary": "color name",
    "accent": "color name"
  }},
  "explanation": "detailed explanation",
  "shopping_keywords": {{
    "amazon_india": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "myntra": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "zara": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "ajio": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "nykaa_fashion": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
  }}
}}"""

    try:
        # Call Groq API with lower temperature for more focused results
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional fashion stylist. Always respond with valid JSON only, no additional text. "
                        f"IMPORTANT: The user's occasion is '{occasion}'. Every outfit item and every shopping keyword "
                        f"MUST be specifically appropriate for '{occasion}'. Never suggest items from a different category."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            max_tokens=2048,
        )
        
        # Extract response
        response_text = chat_completion.choices[0].message.content
        
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\s*|\s*```$', '', response_text, flags=re.MULTILINE)
        
        # Parse JSON
        styling_data = json.loads(response_text)
        
        # Post-processing: validate and fix shopping keywords
        styling_data = validate_and_fix_keywords(styling_data, occasion, gender)
        
        return styling_data
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response: {response_text}")
        return get_fallback_styling(occasion, gender)
    except Exception as e:
        print(f"Error generating styling: {e}")
        return get_fallback_styling(occasion, gender)


def validate_and_fix_keywords(styling_data, occasion, gender):
    """
    Post-process AI response to ensure shopping keywords are present and valid.
    If keywords are missing or empty, replace with curated occasion-specific ones.
    """
    fallback_keywords = build_occasion_keywords(occasion, gender)
    platforms = ['amazon_india', 'myntra', 'zara', 'ajio', 'nykaa_fashion']
    
    if 'shopping_keywords' not in styling_data:
        styling_data['shopping_keywords'] = fallback_keywords
        return styling_data
    
    for platform in platforms:
        keywords = styling_data['shopping_keywords'].get(platform, [])
        # If missing, empty, or has placeholder values, replace
        if (not keywords 
            or len(keywords) < 3 
            or any(k.startswith('keyword') for k in keywords)):
            styling_data['shopping_keywords'][platform] = fallback_keywords.get(platform, [])
    
    return styling_data


def get_fallback_styling(occasion='Casual', gender='Female'):
    """Fallback styling recommendation — occasion-aware"""
    is_male = gender.lower() in ('male', 'man', 'men') if gender else False
    
    # Occasion-specific fallback outfits
    occasion_outfits = {
        'Business': {
            "outfit": {
                "top": "Tailored blazer over a crisp formal shirt" if is_male else "Structured blazer with a silk blouse",
                "bottom": "Formal tailored trousers in charcoal" if is_male else "High-waisted tailored trousers or pencil skirt",
                "shoes": "Polished Oxford leather shoes" if is_male else "Pointed-toe leather pumps",
                "accessories": "Leather belt, formal watch, and tie" if is_male else "Leather tote bag, minimal gold jewelry, and a classic watch"
            },
            "hairstyle": "Clean, slicked-back professional look" if is_male else "Sleek low bun or straight blowout",
            "color_palette": {"primary": "Navy Blue", "secondary": "White", "accent": "Charcoal Grey"},
            "explanation": "This professional ensemble projects competence and confidence. Navy and charcoal are power colors suitable for business environments."
        },
        'Formal': {
            "outfit": {
                "top": "Classic black tuxedo jacket with satin lapels" if is_male else "Elegant evening gown or cocktail dress",
                "bottom": "Matching tuxedo trousers" if is_male else "Coordinated if wearing separates",
                "shoes": "Patent leather dress shoes" if is_male else "Stiletto heels in metallic or black",
                "accessories": "Bow tie, cufflinks, and dress watch" if is_male else "Statement earrings, clutch bag, and delicate bracelet"
            },
            "hairstyle": "Neatly groomed and parted" if is_male else "Elegant updo or soft curls",
            "color_palette": {"primary": "Black", "secondary": "Gold", "accent": "Deep Red"},
            "explanation": "Classic formal colors exude sophistication. Black with gold accents is timeless for formal events."
        },
        'Casual': {
            "outfit": {
                "top": "Well-fitted crew-neck t-shirt or casual button-down" if is_male else "Relaxed-fit blouse or stylish casual top",
                "bottom": "Slim-fit jeans or chinos" if is_male else "High-waisted jeans or casual skirt",
                "shoes": "Clean white sneakers" if is_male else "White sneakers or casual flats",
                "accessories": "Casual watch and simple bracelet" if is_male else "Crossbody bag, layered necklaces, and a casual watch"
            },
            "hairstyle": "Textured, relaxed style" if is_male else "Loose waves or a casual ponytail",
            "color_palette": {"primary": "Denim Blue", "secondary": "White", "accent": "Olive Green"},
            "explanation": "Casual yet polished — this look is comfortable for everyday wear while still looking put-together."
        },
        'Party': {
            "outfit": {
                "top": "Slim-fit party blazer or a bold printed shirt" if is_male else "Sequin top or a bold party blouse",
                "bottom": "Dark slim-fit trousers" if is_male else "Mini skirt, bodycon skirt, or party trousers",
                "shoes": "Chelsea boots or suede loafers" if is_male else "Strappy heels or embellished sandals",
                "accessories": "Statement watch, chain bracelet" if is_male else "Statement earrings, clutch, and layered bracelets"
            },
            "hairstyle": "Styled with texture and volume" if is_male else "Glamorous curls or sleek straight style",
            "color_palette": {"primary": "Black", "secondary": "Magenta", "accent": "Silver"},
            "explanation": "Bold and glamorous — this party look ensures you stand out with statement pieces and metallic accents."
        },
        'Wedding': {
            "outfit": {
                "top": "Embroidered sherwani or silk kurta" if is_male else "Designer lehenga choli or silk saree",
                "bottom": "Churidar or fitted pajama" if is_male else "Lehenga skirt or saree drape",
                "shoes": "Traditional mojari or juttis" if is_male else "Embellished juttis or wedge heels",
                "accessories": "Brooch, pocket square, and stole" if is_male else "Kundan jewelry set, bangles, and maang tikka"
            },
            "hairstyle": "Neatly groomed with traditional touch" if is_male else "Elegant bun with floral accessories or braided updo",
            "color_palette": {"primary": "Royal Blue", "secondary": "Gold", "accent": "Maroon"},
            "explanation": "Rich traditional colors with gold accents are perfect for Indian wedding celebrations."
        },
        'Date Night': {
            "outfit": {
                "top": "Smart casual blazer over a fitted shirt" if is_male else "Flattering wrap dress or a chic blouse",
                "bottom": "Dark well-fitted jeans or chinos" if is_male else "High-waisted pants or a midi skirt",
                "shoes": "Suede loafers" if is_male else "Block heels or elegant flats",
                "accessories": "Classic watch and light cologne" if is_male else "Delicate pendant necklace, small clutch, and perfume"
            },
            "hairstyle": "Clean and styled with subtle texture" if is_male else "Soft loose curls or a half-up half-down style",
            "color_palette": {"primary": "Burgundy", "secondary": "Cream", "accent": "Black"},
            "explanation": "Romantic yet confident — burgundy and cream create a warm, approachable look perfect for a date."
        },
        'Festival': {
            "outfit": {
                "top": "Vibrant printed kurta or embroidered silk kurta" if is_male else "Colorful anarkali suit or embroidered kurti",
                "bottom": "Churidar or dhoti style pants" if is_male else "Palazzo pants or lehenga skirt",
                "shoes": "Traditional kolhapuri chappals or juttis" if is_male else "Embroidered juttis or ethnic wedges",
                "accessories": "Ethnic stole and beaded bracelet" if is_male else "Jhumka earrings, bangles, and a bindi"
            },
            "hairstyle": "Well-groomed with traditional styling" if is_male else "Floral braids or decorated bun",
            "color_palette": {"primary": "Saffron Orange", "secondary": "Emerald Green", "accent": "Gold"},
            "explanation": "Vibrant festive colors celebrate the spirit of Indian festivals with rich cultural elements."
        },
    }
    
    occasion_key = occasion.strip().title() if occasion else 'Casual'
    outfit_data = occasion_outfits.get(occasion_key, occasion_outfits['Casual'])
    
    # Add occasion-specific shopping keywords
    outfit_data['shopping_keywords'] = build_occasion_keywords(occasion, gender)
    
    return outfit_data


# ====================================
# VALIDATION FUNCTIONS
# ====================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength:
    - At least 8 characters
    - Contains uppercase and lowercase
    - Contains numbers
    - Contains special characters
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"


# ====================================
# ROUTES
# ====================================

@app.route('/')
def index():
    """Home page"""
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate email
        if not validate_email(email):
            return render_template('signup.html', error="Invalid email format")
        
        # Validate password match
        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return render_template('signup.html', error=message)
        
        # Create user
        if create_user(email, password):
            return redirect(url_for('login', success="Account created successfully! Please login."))
        else:
            return render_template('signup.html', error="Email already registered")
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = get_user(email)
        
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password")
    
    success_msg = request.args.get('success')
    return render_template('login.html', success=success_msg)


@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_email', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Styling dashboard - main interface"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', email=session['user_email'])


@app.route('/generate-styling', methods=['POST'])
def generate_styling():
    """Process styling request and generate recommendations"""
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get form data
        gender = request.form.get('gender')
        age = request.form.get('age')
        occasion = request.form.get('occasion')
        custom_occasion = request.form.get('custom_occasion', '')
        budget = request.form.get('budget')
        preferred_colors = request.form.get('preferred_colors', '')
        
        # Handle custom occasion
        if occasion == 'Custom' and custom_occasion:
            occasion = custom_occasion
        
        # Get uploaded image
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Save uploaded image
        filename = secure_filename(f"{session['user_email']}_{datetime.now().timestamp()}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Detect skin tone
        skin_tone = detect_skin_tone(filepath)
        
        # Prepare user data for AI
        user_data = {
            'skin_tone': skin_tone,
            'gender': gender,
            'age': age,
            'occasion': occasion,
            'budget': budget,
            'preferred_colors': preferred_colors
        }
        
        # Generate styling recommendation
        styling_result = generate_styling_recommendation(user_data)
        
        # Ensure keywords use the curated set if AI returned weak results
        styling_result = validate_and_fix_keywords(styling_result, occasion, gender)
        
        # Save to history
        styling_data = {
            'skin_tone': skin_tone,
            'gender': gender,
            'age': age,
            'occasion': occasion,
            'budget': budget,
            'result': styling_result
        }
        save_styling_history(session['user_email'], styling_data)
        
        # Store in session for result page
        session['last_styling'] = {
            'user_data': user_data,
            'result': styling_result
        }
        
        return jsonify({'success': True, 'redirect': url_for('result')})
        
    except Exception as e:
        print(f"Error in generate_styling: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/result')
def result():
    """Display styling results"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if 'last_styling' not in session:
        return redirect(url_for('dashboard'))
    
    styling = session['last_styling']
    return render_template('result.html', 
                         user_data=styling['user_data'],
                         result=styling['result'])


# ====================================
# RUN APPLICATION
# ====================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
