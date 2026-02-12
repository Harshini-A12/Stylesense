# StyleSense - AI-Powered Fashion Styling Web Application

## Overview

StyleSense is a premium, AI-powered fashion styling web application that provides personalized outfit recommendations based on facial image analysis, skin tone detection, and user preferences.

## Features

✨ **AI-Powered Styling**
- Advanced skin tone detection using OpenCV
- Personalized outfit recommendations via Groq AI (LLaMA 3.3 70B)
- Hairstyle suggestions
- Custom color palette generation

🎨 **Comprehensive Recommendations**
- Complete outfit breakdown (Top, Bottom, Shoes, Accessories)
- Occasion-specific styling
- Budget-conscious recommendations
- Color theory explanations

🛍️ **Smart Shopping Integration**
- Direct shopping links to:
  - Amazon India
  - Myntra
  - Zara
  - Ajio
  - Nykaa Fashion
- Keyword-based product search
- Easy sharing via WhatsApp, Instagram, and more

👤 **User Management**
- Secure authentication
- Email validation
- Strong password requirements
- Styling history tracking

## Tech Stack

### Frontend
- HTML5
- CSS3 (Premium fashion-inspired design)
- Vanilla JavaScript

### Backend
- Python 3.8+
- Flask web framework

### AI & ML
- Groq API (LLaMA 3.3 70B Versatile)
- OpenCV for image processing
- NumPy for numerical operations

### Database
- JSON file-based storage

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Groq API key (get it from https://console.groq.com)

### Step 1: Clone or Download

Download all project files to a directory named `stylesense`.

### Step 2: Install Dependencies

```bash
cd stylesense
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Edit the `.env` file and add your Groq API key:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
SECRET_KEY=your_secret_flask_key_here
```

To get a Groq API key:
1. Visit https://console.groq.com
2. Sign up or login
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into the .env file

### Step 4: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### 1. Sign Up
- Navigate to the signup page
- Enter a valid email address
- Create a strong password (minimum 8 characters with uppercase, lowercase, numbers, and special characters)
- Confirm your password

### 2. Login
- Use your registered email and password to login

### 3. Create Your Style Profile
- Upload a clear facial photo (for skin tone detection)
- Select your gender
- Enter your age
- Choose the occasion/event
- Select your budget range
- Optionally add preferred colors

### 4. Get Recommendations
- Click "Generate My Perfect Style"
- AI will analyze your features and preferences
- Receive personalized outfit, hairstyle, and color recommendations

### 5. Shop Your Look
- Click on shopping keywords to search on your favorite platforms
- Share your style via WhatsApp, Instagram, or copy the link

## Project Structure

```
stylesense/
│
├── app.py                 # Main Flask application
├── .env                   # Environment variables (API keys)
├── requirements.txt       # Python dependencies
├── database.json          # User data and styling history
│
├── templates/
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   ├── dashboard.html    # Styling input form
│   └── result.html       # Recommendations display
│
└── static/
    ├── style.css         # Premium CSS styling
    └── uploads/          # User uploaded images
```

## Design Philosophy

StyleSense embraces a **luxurious, elegant, and fashion-forward** aesthetic:

- **Color Palette**: Beige, cream, pastels, muted pinks, soft browns
- **Accent Colors**: Brown, sage green, rose, terracotta
- **Typography**: Playfair Display (headings), Montserrat (body), Cormorant Garamond (brand)
- **Effects**: Smooth gradients, soft shadows, floating animations
- **Layout**: Spacious, clean, card-based design

## Security Features

- Password hashing using Werkzeug
- Email format validation
- Strong password requirements
- Session management
- Secure file uploads (16MB limit)

## API Integration

### Groq AI
- Model: llama-3.3-70b-versatile
- Purpose: Generate fashion recommendations
- Temperature: 0.7 for creative yet relevant suggestions

### Skin Tone Detection
- Uses OpenCV for HSV color space analysis
- Classifies into: Fair, Medium, Olive, Deep
- Fallback to center region analysis if needed

## Customization

### Adding New Occasions
Edit `dashboard.html` and add options to the occasion dropdown:

```html
<option value="Your New Occasion">Your New Occasion</option>
```

### Adding Shopping Platforms
1. Update the AI prompt in `app.py` to include the new platform
2. Add a new platform card in `result.html`
3. Add the appropriate URL structure for search

### Changing Color Scheme
Edit CSS variables in `static/style.css`:

```css
:root {
  --bg-primary: #FAF8F5;
  --accent-brown: #8B6F47;
  /* ... other variables */
}
```

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: OpenCV installation fails
**Solution**: Try installing with specific version:
```bash
pip install opencv-python-headless==4.8.1.78
```

### Issue: Groq API errors
**Solution**: 
1. Verify your API key is correct in `.env`
2. Check your API quota at https://console.groq.com
3. Ensure you have internet connection

### Issue: Image upload fails
**Solution**: 
- Check file size (max 16MB)
- Ensure `static/uploads/` directory exists
- Verify file format (JPG, PNG, WEBP)

### Issue: Skin tone detection not working
**Solution**: 
- Use a clear, well-lit facial photo
- Ensure face is centered in the image
- Avoid heavy filters or makeup that alters skin tone

## Production Deployment

For production deployment:

1. **Change Debug Mode**: Set `debug=False` in `app.py`
2. **Use Production Server**: Replace Flask's built-in server with Gunicorn or uWSGI
3. **HTTPS**: Use SSL/TLS certificates
4. **Environment Variables**: Use proper secret management
5. **Database**: Consider migrating to PostgreSQL or MongoDB
6. **File Storage**: Use cloud storage (S3, GCS) for uploaded images
7. **Rate Limiting**: Add API rate limiting for security

## License

This project is created for educational and demonstration purposes.

## Support

For issues, questions, or suggestions:
- Review this README thoroughly
- Check the troubleshooting section
- Ensure all dependencies are correctly installed
- Verify API keys are properly configured

## Credits

- **AI Model**: Groq (LLaMA 3.3 70B Versatile)
- **Image Processing**: OpenCV
- **Web Framework**: Flask
- **Design**: Premium fashion-inspired aesthetic

---

**StyleSense** - Where AI Meets Fashion ✨

Discover your perfect style with cutting-edge artificial intelligence.
