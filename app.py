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
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("""
<div class="header">
    <img src="https://img.icons8.com/color/48/000000/paint-palette.png" alt="palette icon">
    <h1>AI Image Generation Tool</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("### Realistic Image Generation Assistant")

# Function to select an image and switch tabs
def select_image(image_url, next_tab):
    st.session_state.selected_image = image_url
    st.session_state.active_tab = next_tab
    st.rerun()

# Function to download image
def download_image(image_url, filename):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    buf = BytesIO()
    image.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im

# Functions
def show_image_generation():
    """Shows the image generation interface"""
    st.markdown('<div class="section-title"><h3>Image Generation Settings</h3></div>', unsafe_allow_html=True)
    
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
        selected_category = st.selectbox("Select Category", category_options)
        
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
        selected_idea = st.selectbox("Select Idea", idea_options[selected_category])
        
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
        selected_ethnicity = st.selectbox("Appearance/Ethnicity", ethnicity_options)
        
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
        selected_style = st.selectbox("Visual Style", style_options)
        
        # Additional details
        additional_details = st.text_area(
            "Additional Details (Optional)", 
            placeholder="E.g.: red hair, blue eyes, beach background..."
        )
    
    with col2:
        # Image size
        size_options = ["1024x1024", "1024x1792", "1792x1024"]
        selected_size = st.selectbox("Image Size", size_options)
        
        # Image quality
        quality_options_display = ["Standard", "HD"]
        quality_options_api = ["standard", "hd"]
        quality_index = st.selectbox("Image Quality", quality_options_display)
        selected_quality = quality_options_api[quality_options_display.index(quality_index)]

        # Number of images - updated with better UX
        num_images = st.slider("Number of Images to Generate", 1, 4, 1)
        
        # Progress steps visualization
        st.markdown("""
        <div class="progress-container">
            <h4>Generation Process:</h4>
            <div class="progress-step">
                <div class="step-number">1</div>
                <div class="step-text">Generate detailed prompt using AI</div>
            </div>
            <div class="progress-step">
                <div class="step-number">2</div>
                <div class="step-text">Create realistic images with OpenAI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips for better results
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Tips for Better Results</h4>
            <ul>
                                <li>Be specific about appearance details</li>
                <li>Mention lighting conditions for better mood</li>
                <li>Include background information</li>
                <li>Specify camera angle if important</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate prompt button
        if st.button("Generate Prompts"):
            # GPT prompt generation
            ethnicity_prompt = ""
            if selected_ethnicity != "Mixed/Random":
                ethnicity_prompt = f", {selected_ethnicity} appearance"
            
            system_prompt = """
            You are a professional photographer and visual artist.
            You need to write a prompt for OpenAI's image generation to create realistic, high-quality images.
            Based on the given information, create a detailed, realistic, and aesthetic photo prompt.
            The prompt should be in English and include all necessary details for a realistic photo.
            """
            
            user_prompt = f"""
            Category: {selected_category}
            Idea: {selected_idea}
            Appearance: {selected_ethnicity}
            Style: {selected_style}
            Additional details: {additional_details}
            
            Please create a prompt for a realistic, high-quality photo based on this information.
            The prompt should include all necessary details for the photo shoot: composition, lighting, atmosphere, color scheme, etc.
            Start the prompt with "A photorealistic image" and include directives to avoid AI-generated image feel.
            Make sure this is a prompt for a REALISTIC photo, not a cartoon or illustration.
            """
            
            try:
                with st.spinner("Generating prompt..."):
                    # Add loading animation
                    st.markdown("""
                    <div class="loading-animation">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=300
                    )
                    
                    realistic_prompt = response.choices[0].message.content.strip()
                    st.session_state.realistic_prompt = realistic_prompt
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Prompt:")
                    st.text_area("", realistic_prompt, height=150, key="prompt_result")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating prompt: {e}")
        
        # Generate images button
        if st.button("Generate Images") and st.session_state.realistic_prompt:
            try:
                with st.spinner("Generating realistic images..."):
                    # Add loading animation
                    st.markdown("""
                    <div class="loading-animation">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    images = []
                    # DALL-E 3 supports only 1 image per request, so loop for multiple images
                    for _ in range(num_images):
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=st.session_state.realistic_prompt + " Make sure this is a photorealistic image, not a cartoon or illustration. Use photographic style with realistic lighting and textures.",
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
                    
                    st.session_state.realistic_images = images
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Realistic Images:")
                    
                    # Show images in a modern gallery
                    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                    for i, image_url in enumerate(st.session_state.realistic_images):
                        st.markdown('<div class="image-card">', unsafe_allow_html=True)
                        st.image(image_url, use_column_width=True, caption=f"Realistic Image #{i+1}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Select Image #{i+1}", key=f"select_img_{i}"):
                                select_image(image_url, 'Etsy Metadata')
                        with col2:
                            st.download_button(
                                label="Download",
                                data=download_image(image_url, f"realistic_image_{i+1}.png"),
                                file_name=f"realistic_image_{i+1}.png",
                                mime="image/png",
                                key=f"download_img_{i}"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating images: {str(e)}")
                st.error("Please try a different prompt or check your API key.")

def show_cartoon_generation():
    """Shows the cartoon image generation interface"""
    st.markdown('<div class="section-title"><h3>Cartoon Image Generation Settings</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category selection for cartoon
        category_options = [
            "Family & Couple Cartoons",
            "Wedding Cartoons",
            "Birthday Cartoons",
            "Pet Cartoons",
            "Superhero Cartoons",
            "Fantasy Characters",
            "Funny Moments"
        ]
        selected_category = st.selectbox("Select Cartoon Category", category_options)
        
        # Idea selection for cartoon
        idea_options = {
            "Family & Couple Cartoons": ["Family Cartoon", "Couple Cartoon", "Funny Family Moment"],
            "Wedding Cartoons": ["Wedding Cartoon", "Bride & Groom Cartoon", "Wedding Party"],
            "Birthday Cartoons": ["Birthday Party Cartoon", "Cake Smash Cartoon", "Gift Opening Cartoon"],
            "Pet Cartoons": ["Dog Cartoon", "Cat Cartoon", "Pet with Owner Cartoon"],
            "Superhero Cartoons": ["Superhero Family", "Superhero Couple", "Superhero Pet"],
            "Fantasy Characters": ["Wizard Cartoon", "Fairy Cartoon", "Dragon Rider"],
            "Funny Moments": ["Clumsy Moment", "Funny Dance", "Surprise Reaction"]
        }
        selected_idea = st.selectbox("Select Cartoon Idea", idea_options[selected_category])
        
        # Cartoon style
        cartoon_style_options = [
            "Disney Style",
            "Anime Style",
            "Comic Book Style",
            "Cartoon Network Style",
            "Hand-Drawn Style",
            "Watercolor Cartoon"
        ]
        selected_style = st.selectbox("Cartoon Style", cartoon_style_options)
        
        # Additional details for cartoon
        additional_details = st.text_area(
            "Additional Details for Cartoon (Optional)", 
            placeholder="E.g.: funny expressions, bright colors, specific background..."
        )
    
    with col2:
        # Image size
        size_options = ["1024x1024", "1024x1792", "1792x1024"]
        selected_size = st.selectbox("Cartoon Image Size", size_options)
        
        # Image quality
        quality_options_display = ["Standard", "HD"]
        quality_options_api = ["standard", "hd"]
        quality_index = st.selectbox("Cartoon Image Quality", quality_options_display)
        selected_quality = quality_options_api[quality_options_display.index(quality_index)]

        # Number of images
        num_images = st.slider("Number of Cartoon Images to Generate", 1, 4, 1)
        
        # Tips for better cartoon results
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Tips for Better Cartoon Results</h4>
            <ul>
                <li>Specify the mood or expression (e.g., funny, cute)</li>
                <li>Mention specific cartoon styles or inspirations</li>
                <li>Include background or theme details</li>
                <li>Describe character traits if important</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate cartoon prompt button
        if st.button("Generate Cartoon Prompts"):
            system_prompt = """
            You are a professional cartoonist and illustrator.
            You need to write a prompt for OpenAI's image generation to create vibrant, stylized cartoon images.
            Based on the given information, create a detailed and creative cartoon prompt.
            The prompt should be in English and include all necessary details for a cartoon illustration.
            """
            
            user_prompt = f"""
            Category: {selected_category}
            Idea: {selected_idea}
            Style: {selected_style}
            Additional details: {additional_details}
            
            Please create a prompt for a vibrant, stylized cartoon image based on this information.
            The prompt should include all necessary details: composition, colors, mood, style specifics, etc.
            Start the prompt with "A vibrant cartoon illustration" and ensure it feels like a cartoon, not a realistic photo.
            """
            
            try:
                with st.spinner("Generating cartoon prompt..."):
                    st.markdown("""
                    <div class="loading-animation">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=300
                    )
                    
                    cartoon_prompt = response.choices[0].message.content.strip()
                    st.session_state.cartoon_prompt = cartoon_prompt
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Cartoon Prompt:")
                    st.text_area("", cartoon_prompt, height=150, key="cartoon_prompt_result")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating cartoon prompt: {e}")
        
        # Generate cartoon images button
        if st.button("Generate Cartoon Images") and st.session_state.cartoon_prompt:
            try:
                with st.spinner("Generating cartoon images..."):
                    st.markdown("""
                    <div class="loading-animation">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    images = []
                    for _ in range(num_images):
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=st.session_state.cartoon_prompt + " Ensure this is a stylized cartoon illustration, not a realistic photo. Use vibrant colors and exaggerated features typical of cartoons.",
                            n=1,
                            size=selected_size,
                            quality=selected_quality
                        )
                        
                        for data in response.data:
                            image_url = data.url
                            images.append(image_url)
                            st.session_state.image_history.append({
                                "url": image_url,
                                "type": "Cartoon",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                    
                    st.session_state.cartoon_images = images
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Cartoon Images:")
                    
                    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                    for i, image_url in enumerate(st.session_state.cartoon_images):
                        st.markdown('<div class="image-card">', unsafe_allow_html=True)
                        st.image(image_url, use_column_width=True, caption=f"Cartoon Image #{i+1}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Select Cartoon #{i+1}", key=f"select_cartoon_{i}"):
                                select_image(image_url, 'Etsy Metadata')
                        with col2:
                            st.download_button(
                                label="Download",
                                data=download_image(image_url, f"cartoon_image_{i+1}.png"),
                                file_name=f"cartoon_image_{i+1}.png",
                                mime="image/png",
                                key=f"download_cartoon_{i}"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating cartoon images: {str(e)}")
                st.error("Please try a different prompt or check your API key.")

def show_etsy_metadata():
    """Shows the Etsy metadata interface"""
    st.markdown('<div class="section-title"><h3>Generate Etsy Metadata</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.selected_image:
        st.markdown("#### Selected Image")
        st.image(st.session_state.selected_image, width=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_title = st.text_input("Product Title", "Custom Portrait from Photo")
            product_description = st.text_area(
                "Product Description", 
                """Custom digital portrait created from your photo.
                Completely personalized, delivered as a high-resolution digital file.
                Perfect for printing, instantly downloadable."""
            )
        
        with col2:
            tags = st.text_input(
                "Tags (comma separated)",
                "custom portrait, digital art, personalized gift, family portrait, photo to art"
            )
            price = st.number_input("Price ($)", min_value=5.0, value=19.99, step=1.0)
            delivery_format = st.selectbox(
                "Delivery Format",
                ["Digital Download (JPG & PNG)", "Digital Download + Print", "Print Only"]
            )
        
        # Generate metadata button
        if st.button("Generate Etsy Metadata"):
            with st.spinner("Generating metadata..."):
                st.markdown("""
                <div class="loading-animation">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
                """, unsafe_allow_html=True)
                
                metadata = {
                    "title": product_title,
                    "description": product_description,
                    "tags": tags.split(","),
                    "price": price,
                    "delivery_format": delivery_format,
                    "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "image_url": st.session_state.selected_image
                }
                
                # Show metadata as JSON
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Generated Etsy Metadata:")
                st.json(metadata)
                
                # Download button
                json_str = json.dumps(metadata, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="etsy_metadata.json" class="download-btn">Download Metadata File</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Generate SEO suggestions
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### SEO Suggestions for Etsy:")
                
                seo_suggestions = [
                    "Use all 13 tags allowed by Etsy for maximum visibility",
                    "Include 'custom portrait' in your title for better search matching",
                    "Add 'personalized gift' as it's a high-search term",
                    "Include specific occasions like 'birthday gift' or 'anniversary present'",
                    "Mention 'custom portrait' as it's a popular search term",
                    "Use long-tail keywords like 'family portrait from photo' for better targeting",
                    "Include relevant seasonal keywords during holidays",
                    "Add material terms like 'digital download' or 'printable art'",
                    "Mention turnaround time in your description for better customer expectations",
                    "Use keywords that match what buyers are searching for",
                    "Include variations of your main keywords (portrait, portraits, portraiture)",
                    "Add attributes like 'handmade' or 'custom made' to increase visibility",
                    "Consider using trending keywords related to your product category"
                ]
                
                for suggestion in seo_suggestions:
                    st.markdown(f"• {suggestion}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Marketing tips
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Marketing Tips:")
                
                marketing_tips = [
                    "Offer bundle discounts for multiple portraits",
                    "Create a limited-time promotion for first-time buyers",
                    "Add a portfolio of sample images to showcase your style range",
                    "Include customer testimonials in your description",
                    "Offer rush delivery as an upgrade option",
                    "Create holiday-specific promotions",
                    "Offer different size options at different price points",
                    "Provide before/after examples to show your work quality",
                    "Create gift certificates for customers to purchase for others",
                    "Offer framing options as an additional service",
                    "Create a loyalty program for returning customers"
                ]
                
                for tip in marketing_tips:
                    st.markdown(f"• {tip}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.info("Please first create and select an image from the 'Image Generation' or 'Cartoon Generation' tab.")
        if st.button("Go to Image Generation"):
            st.session_state.active_tab = 'Image Generation'
            st.rerun()

def show_image_history():
    """Shows the history of generated images"""
    st.markdown('<div class="section-title"><h3>Generated Image History</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.image_history:
        st.markdown("#### Previously Generated Images")
        st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
        for i, img_data in enumerate(reversed(st.session_state.image_history[-12:])):
            st.markdown('<div class="image-card">', unsafe_allow_html=True)

