import streamlit as st
import json
import base64
import os
import io
from PIL import Image
from openai import OpenAI
import random
from datetime import datetime
import requests
from io import BytesIO
import time

# Session state controls
if 'selected_image' not in st.session_state:
    st.session_state.selected_image = None

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Image Generation'

if 'realistic_images' not in st.session_state:
    st.session_state.realistic_images = []
if 'cartoon_images' not in st.session_state:
    st.session_state.cartoon_images = []
if 'realistic_prompt' not in st.session_state:
    st.session_state.realistic_prompt = ""
if 'cartoon_prompt' not in st.session_state:
    st.session_state.cartoon_prompt = ""
if 'image_history' not in st.session_state:
    st.session_state.image_history = []
if 'image_to_convert' not in st.session_state:
    st.session_state.image_to_convert = None
if 'page_needs_rerun' not in st.session_state:
    st.session_state.page_needs_rerun = False
if 'last_action' not in st.session_state:
    st.session_state.last_action = None

# Page configuration
st.set_page_config(page_title="AI Image Generation Tool", layout="wide")

# Initialize OpenAI API client
client = OpenAI(api_key=st.secrets["openai_api_key"])

# CSS styles
st.markdown("""
<style>
    .main {
        background-color: #121212;
        color: #ffffff;
    }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #ff7070;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.3);
    }
    .drop-zone {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        background-color: #1e1e1e;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .drop-zone:hover {
        border-color: #ff4b4b;
        background-color: #2a2a2a;
    }
    .result-container {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        animation: fadeIn 0.5s ease;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        background: linear-gradient(90deg, #ff4b4b, #ff8f8f);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.3);
    }
    .header img {
        margin-right: 15px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }
    .section-title {
        background-color: #2a2a2a;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        border-left: 4px solid #ff4b4b;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #1a1a1a;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #2a2a2a;
        border-radius: 8px;
        gap: 1px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #ff4b4b, #ff8f8f) !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.3);
    }
    .image-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    .image-card {
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        overflow: hidden;
    }
    .image-card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    .image-card img {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .image-card:hover img {
        transform: scale(1.05);
    }
    .tips-box {
        background-color: #2a2a2a;
        border-left: 4px solid #ff4b4b;
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metadata-container {
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stSelectbox, .stMultiselect {
        margin-bottom: 15px;
    }
    .stSelectbox [data-baseweb="select"] {
        background-color: #2a2a2a;
        border-radius: 8px;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #2a2a2a;
        border-radius: 8px;
        border: 1px solid #3a3a3a;
        color: white;
        padding: 10px 15px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #ff4b4b;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.3);
    }
    .download-btn {
        display: inline-block;
        background: linear-gradient(90deg, #ff4b4b, #ff8f8f);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.3);
    }
    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 75, 75, 0.4);
    }
    .footer {
        margin-top: 50px;
        text-align: center;
        padding: 20px;
        background-color: #1a1a1a;
        border-radius: 10px;
    }
    .progress-container {
        margin: 20px 0;
    }
    .progress-step {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .step-number {
        background-color: #ff4b4b;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        font-weight: bold;
    }
    .step-text {
        flex-grow: 1;
    }
    .loading-animation {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .loading-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ff4b4b;
        margin: 0 5px;
        animation: bounce 1.5s infinite ease-in-out;
    }
    .loading-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    .loading-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    .convert-section {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border-left: 4px solid #ff4b4b;
    }
    .action-btn {
        background: linear-gradient(90deg, #ff4b4b, #ff8f8f);
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: bold;
        border: none;
        margin-top: 10px;
        width: 100%;
    }
    .action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.3);
    }
    .image-comparison {
        display: flex;
        flex-direction: row;
        gap: 20px;
        margin: 20px 0;
    }
    .image-container {
        flex: 1;
        text-align: center;
    }
    .conversion-options {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0;
    }
    .option-card {
        background-color: #2a2a2a;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        flex: 1;
        min-width: 120px;
    }
    .option-card:hover, .option-card.selected {
        background-color: #ff4b4b;
        transform: translateY(-2px);
    }
    .cache-info {
        background-color: #2a2a2a;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 0.9em;
        color: #aaa;
    }
    .notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #ff4b4b;
        color: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("""
<div class="header">
    <img src="https://img.icons8.com/color/48/000000/paint-palette.png" alt="palette icon">
    <h1>AI Image Generation Tool</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("### Realistic Image Generation & Cartoon Conversion Assistant")

# Function to select an image and switch tabs without rerunning
def select_image(image_url, next_tab):
    st.session_state.selected_image = image_url
    st.session_state.active_tab = next_tab
    st.session_state.last_action = f"Görsel seçildi ve {next_tab} sekmesine geçildi"

# Function to set image for conversion without rerunning
def set_image_to_convert(image_url):
    st.session_state.image_to_convert = image_url
    st.session_state.active_tab = 'Cartoon Conversion'
    st.session_state.last_action = "Görsel çizgi filme dönüştürmek üzere seçildi"

# Function to download image
@st.cache_data(ttl=3600)
def download_image(image_url, filename):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        buf = BytesIO()
        image.save(buf, format="PNG")
        byte_im = buf.getvalue()
        return byte_im
    except Exception as e:
        st.error(f"Görsel indirme hatası: {e}")
        return None

# Cache for improved performance
@st.cache_data(ttl=3600)
def generate_ai_prompt(category, idea, ethnicity, style, additional_details):
    """Generate AI prompt with caching for better performance"""
    system_prompt = """
    You are a professional photographer and visual artist.
    You need to write a prompt for OpenAI's image generation to create realistic, high-quality images.
    Based on the given information, create a detailed, realistic, and aesthetic photo prompt.
    The prompt should be in English and include all necessary details for a realistic photo.
    """
    
    user_prompt = f"""
    Category: {category}
    Idea: {idea}
    Appearance: {ethnicity}
    Style: {style}
    Additional details: {additional_details}
    
    Please create a prompt for a realistic, high-quality photo based on this information.
    The prompt should include all necessary details for the photo shoot: composition, lighting, atmosphere, color scheme, etc.
    Start the prompt with "A photorealistic image" and include directives to avoid AI-generated image feel.
    Make sure this is a prompt for a REALISTIC photo, not a cartoon or illustration.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content.strip()

@st.cache_data(ttl=3600)
def generate_cartoon_prompt(style, description, image_url=None):
    """Generate cartoon prompt based on style and description"""
    system_prompt = """
    You are a professional cartoonist and illustrator.
    You need to write a prompt for OpenAI's image generation to convert a realistic photo into a cartoon style.
    The prompt should maintain the essence of the original image while applying the cartoon style.
    """
    
    user_prompt = f"""
    Cartoon Style: {style}
    Description: {description}
    
    Please create a prompt that will convert a realistic photo into a {style} cartoon style.
    The prompt should describe how to maintain the composition and subjects but apply the cartoon style.
    Start with "Convert this realistic photo into a {style} cartoon style" and provide specific details about the style.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content.strip()

# Generate images without rerunning
def generate_realistic_images(prompt, num_images, selected_size, selected_quality):
    """Generate realistic images without rerunning the page"""
    images = []
    progress_placeholder = st.empty()
    
    try:
        for i in range(num_images):
            # Update progress
            progress_placeholder.progress((i) / num_images, text=f"Görsel {i+1}/{num_images} oluşturuluyor...")
            
            # Generate image with enhanced prompt for better realism
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt + " Make sure this is a photorealistic image, not a cartoon or illustration. Use photographic style with realistic lighting and textures.",
                n=1,  # DALL-E 3 only supports n=1
                size=selected_size,
                quality=selected_quality
            )
            
            for data in response.data:
                image_url = data.url
                images.append(image_url)
                # Add to history with timestamp
                st.session_state.image_history.append({
                    "url": image_url,
                    "type": "Realistic",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Clear progress bar after completion
        progress_placeholder.empty()
        
        # Update session state
        st.session_state.realistic_images = images
        st.session_state.last_action = f"{num_images} gerçekçi görsel oluşturuldu"
        
        return images
    
    except Exception as e:
        progress_placeholder.empty()
        st.error(f"Görsel oluşturma hatası: {e}")
        return []

# Convert image to cartoon without rerunning
def convert_to_cartoon(image_url, style, customization, quality):
    """Convert image to cartoon without rerunning the page"""
    try:
        # Generate cartoon prompt based on selected style
        cartoon_prompt = generate_cartoon_prompt(
            style,
            customization
        )
        
        # Store the prompt
        st.session_state.cartoon_prompt = cartoon_prompt
        
        # Use the prompt to generate a cartoon version
        response = client.images.generate(
            model="dall-e-3",
            prompt=cartoon_prompt + f" Based on this realistic image. Make it a high-quality {style} style cartoon.",
            n=1,
            size="1024x1024",
            quality=quality
        )
        
        cartoon_image_url = response.data[0].url
        
        # Add to cartoon images and history
        st.session_state.cartoon_images.append(cartoon_image_url)
        st.session_state.image_history.append({
            "url": cartoon_image_url,
            "type": f"Cartoon ({style})",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        st.session_state.last_action = f"Görsel {style} çizgi film stiline dönüştürüldü"
        
        return cartoon_image_url
    
    except Exception as e:
        st.error(f"Dönüştürme hatası: {str(e)}")
        return None

# Functions for each tab
def show_image_generation():
    """Shows the image generation interface"""
    st.markdown('<div class="section-title"><h3>Gerçekçi Görsel Oluşturma</h3></div>', unsafe_allow_html=True)
    
    # Show notification if there's a last action
    if st.session_state.last_action:
        st.success(st.session_state.last_action)
        # Clear the last action after showing it
        st.session_state.last_action = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category selection - Expanded categories
        category_options = [
            "Family & Couple Portraits",
            "Wedding Portraits",
            "Birthday Portraits",
            "Graduation Portraits",
            "Pet Portraits",
            "Special Moment Portraits",
            "Baby & Child Portraits",
            "Business & Professional Portraits",
            "Holiday & Travel Memories"
        ]
        selected_category = st.selectbox("Kategori Seçin", category_options)
        
        # Idea selection - More ideas added
        idea_options = {
            "Family & Couple Portraits": [
                "Family Portrait", 
                "Couple Portrait", 
                "Anniversary Portrait", 
                "Love Portrait",
                "Couple Holding Hands",
                "Family Hugging",
                "Family Picnic",
                "Couple Walking on Beach"
            ],
            "Wedding Portraits": [
                "Wedding Moment", 
                "Wedding Ceremony", 
                "Wedding Dance", 
                "Bridal Bouquet",
                "Groom Preparation",
                "Bride Preparation",
                "Wedding Cake Cutting",
                "Wedding Photoshoot"
            ],
            "Birthday Portraits": [
                "Birthday Celebration", 
                "Cake Cutting", 
                "Gift Opening", 
                "Party Portrait",
                "Blowing Candles",
                "Birthday Hat",
                "Confetti Moment",
                "Surprise Party"
            ],
            "Graduation Portraits": [
                "Diploma Ceremony", 
                "Cap Throwing", 
                "Graduation Gown", 
                "Achievement Portrait",
                "Graduation Photo",
                "Family Graduation",
                "Campus Memory",
                "Teacher with Graduate"
            ],
            "Pet Portraits": [
                "Dog Portrait", 
                "Cat Portrait", 
                "Pet with Owner", 
                "Cute Moment",
                "Playing Dog",
                "Sleeping Cat",
                "Pet in Costume",
                "Pet Birthday Celebration"
            ],
            "Special Moment Portraits": [
                "Holiday Memory", 
                "Travel Portrait", 
                "Special Day", 
                "Family Gathering",
                "Engagement Moment",
                "Expecting Baby",
                "New Home Memory",
                "Christmas Celebration"
            ],
            "Baby & Child Portraits": [
                "Baby First Steps",
                "Child Birthday",
                "Siblings Portrait",
                "Baby Sleep Moment",
                "First Tooth",
                "Child Playing",
                "First Day of School",
                "Baby Smile"
            ],
            "Business & Professional Portraits": [
                "Office Portrait",
                "Business Meeting",
                "Professional Headshot",
                "Team Work",
                "Presentation Moment",
                "Work Desk",
                "Success Celebration",
                "Professional Attire"
            ],
            "Holiday & Travel Memories": [
                "Beach Vacation",
                "City Tour",
                "Camping Memory",
                "Mountain View",
                "Historical Site Visit",
                "Sunset Memory",
                "Hotel Room",
                "Plane Journey"
            ]
        }
        selected_idea = st.selectbox("Fikir Seçin", idea_options[selected_category])
        
        # Ethnicity/appearance selection - More detailed options
        ethnicity_options = [
            "Mixed/Random",
            "European (Northern)",
            "European (Southern)",
            "East Asian",
            "Southeast Asian",
            "South Asian/Indian",
            "Middle Eastern",
            "African (Northern)",
            "African (Sub-Saharan)",
            "Latin American",
            "Caribbean",
            "Pacific Islander",
            "Native American"
        ]
        selected_ethnicity = st.selectbox("Görünüm/Etnik Köken", ethnicity_options)
        
        # Visual style - More style options
        style_options = [
            "Photographic realism",
            "Soft lighting",
            "Dramatic lighting",
            "Outdoor natural light",
            "Indoor studio",
            "Vintage",
            "Modern",
            "Minimalist",
            "High contrast",
            "Low key",
            "High key",
            "Golden hour",
            "Blue hour",
            "Black and white",
            "Sepia tone"
        ]
        selected_style = st.selectbox("Görsel Stil", style_options)
        
        # Additional details
        additional_details = st.text_area(
            "Ek Detaylar (İsteğe Bağlı)", 
            placeholder="Örn: kızıl saç, mavi gözler, plaj arka planı..."
        )
    
    with col2:
        # Image size
        size_options = ["1024x1024", "1024x1792", "1792x1024"]
        selected_size = st.selectbox("Görsel Boyutu", size_options)
        
        # Image quality
        quality_options_display = ["Standard", "HD"]
        quality_options_api = ["standard", "hd"]
        quality_index = st.selectbox("Görsel Kalitesi", quality_options_display)
        selected_quality = quality_options_api[quality_options_display.index(quality_index)]

        # Number of images - updated with better UX
        num_images = st.slider("Oluşturulacak Görsel Sayısı", 1, 4, 1)
        
        # Progress steps visualization
        st.markdown("""
        <div class="progress-container">
            <h4>Oluşturma Süreci:</h4>
            <div class="progress-step">
                <div class="step-number">1</div>
                <div class="step-text">AI ile detaylı prompt oluştur</div>
            </div>
            <div class="progress-step">
                <div class="step-number">2</div>
                <div class="step-text">OpenAI ile gerçekçi görseller oluştur</div>
            </div>
            <div class="progress-step">
                <div class="step-number">3</div>
                <div class="step-text">Gerçekçi görseli çizgi film stiline dönüştür</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips for better results
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Daha İyi Sonuçlar İçin İpuçları</h4>
            <ul>
                <li>Görünüm detaylarını belirtin</li>
                <li>Daha iyi bir atmosfer için aydınlatma koşullarından bahsedin</li>
                <li>Arka plan bilgisini ekleyin</li>
                <li>Önemliyse kamera açısını belirtin</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate prompt button
        prompt_col1, prompt_col2 = st.columns(2)
        with prompt_col1:
            generate_prompt_btn = st.button("Prompt Oluştur", key="gen_prompt_btn", use_container_width=True)
        
        with prompt_col2:
            generate_images_btn = st.button("Görsel Oluştur", key="gen_img_btn", use_container_width=True, 
                                          disabled=not st.session_state.realistic_prompt)
    
    # Handle prompt generation without page rerun
    if generate_prompt_btn:
        with st.spinner("Prompt oluşturuluyor..."):
            # Add loading animation
            st.markdown("""
            <div class="loading-animation">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Use cached function for better performance
                realistic_prompt = generate_ai_prompt(
                    selected_category, 
                    selected_idea, 
                    selected_ethnicity, 
                    selected_style, 
                    additional_details
                )
                
                st.session_state.realistic_prompt = realistic_prompt
                
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Oluşturulan Prompt:")
                st.text_area("", realistic_prompt, height=150, key="prompt_result")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Prompt oluşturma hatası: {e}")
    
    # Handle image generation without page rerun
    if generate_images_btn and st.session_state.realistic_prompt:
        with st.spinner("Görseller oluşturuluyor..."):
            # Generate images
            images = generate_realistic_images(
                st.session_state.realistic_prompt,
                num_images,
                selected_size,
                selected_quality
            )
            
            if images:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Oluşturulan Gerçekçi Görseller:")
                
                # Show images in a modern gallery
                st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                for i, image_url in enumerate(images):
                    st.markdown('<div class="image-card">', unsafe_allow_html=True)
                    st.image(image_url, use_column_width=True), 
