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

st.markdown("### Realistic Image Generation and Cartoon Conversion Assistant")

# Function to select an image and switch tabs
def select_image(image_url, next_tab):
    st.session_state.selected_image = image_url
    st.session_state.active_tab = next_tab
    st.rerun()

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
            <div class="progress-step">
                <div class="step-number">3</div>
                <div class="step-text">Convert to cartoon style</div>
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
                with st.spinner("Generating images..."):
                    # Add loading animation
                    st.markdown("""
                    <div class="loading-animation">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Using OpenAI API to generate images
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=st.session_state.realistic_prompt,
                        n=1,  # DALL-E 3 only supports n=1
                        size=selected_size,
                        quality=selected_quality
                    )
                    
                    images = []
                    for data in response.data:
                        image_url = data.url
                        images.append(image_url)
                    
                    st.session_state.realistic_images = images
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Images:")
                    
                    # Show images in a modern gallery
                    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                    for i, image_url in enumerate(st.session_state.realistic_images):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.image(image_url, use_column_width=True, caption=f"Image #{i+1}")
                        with col2:
                            st.markdown("<br><br>", unsafe_allow_html=True)
                            # FIXED: Use a custom function to handle image selection and tab switching
                            if st.button(f"Select Image #{i+1}", key=f"select_img_{i}"):
                                select_image(image_url, 'Cartoon Conversion')
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating images: {str(e)}")
                st.error("Please try a different prompt or check your API key.")

def show_cartoon_conversion():
    """Shows the cartoon conversion interface"""
    st.markdown('<div class="section-title"><h3>Convert to Cartoon Style</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.selected_image:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Selected Realistic Image")
            st.image(st.session_state.selected_image, use_column_width=True)
        
        with col2:
            st.markdown("#### Cartoon Style Selection")
            
            cartoon_style_options = [
                "Pixar 3D",
                "Disney 2D Animation",
                "DreamWorks",
                "Anime",
                "South Park",
                "The Simpsons",
                "Studio Ghibli",
                "Claymation",
                "Comic Book",
                "Watercolor Illustration"
            ]
            
            selected_cartoon_style = st.selectbox("Cartoon Style", cartoon_style_options)
            
            # Style details
            style_details = {
                "Pixar 3D": "3D Pixar animation style with detailed textures, expressive features, and warm lighting",
                "Disney 2D Animation": "Classic Disney 2D animation style with smooth lines, vibrant colors, and expressive characters",
                "DreamWorks": "DreamWorks animation style with exaggerated features, dynamic poses, and rich texturing",
                "Anime": "Japanese anime style with large eyes, simplified features, and vibrant colors",
                "South Park": "South Park style with simple shapes, flat colors, and minimalist design",
                "The Simpsons": "The Simpsons style with yellow skin, overbite, and simplified cartoon features",
                "Studio Ghibli": "Studio Ghibli style with detailed backgrounds, soft colors, and whimsical elements",
                "Claymation": "Claymation style with textured surfaces, slightly imperfect shapes, and warm tones",
                "Comic Book": "Comic book style with bold outlines, flat colors, and action-oriented composition",
                "Watercolor Illustration": "Watercolor illustration style with soft edges, transparent colors, and artistic brush strokes"
            }
            
            st.markdown(f"**Style Details:** {style_details[selected_cartoon_style]}")
            
            additional_style_details = st.text_area(
                "Additional Style Details (Optional)",
                placeholder="E.g.: pastel colors, exaggerated facial expressions..."
            )
            
            # Convert button
            if st.button("Convert to Cartoon Style"):
                try:
                    with st.spinner("Converting image..."):
                        # Add loading animation
                        st.markdown("""
                        <div class="loading-animation">
                            <div class="loading-dot"></div>
                            <div class="loading-dot"></div>
                            <div class="loading-dot"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Prompt for converting realistic image to cartoon style
                        style_prompt = f"""
                        Transform this realistic image into a {selected_cartoon_style} cartoon style. 
                        {style_details[selected_cartoon_style]}. 
                        {additional_style_details}
                        Maintain the same composition, characters, and scene, but fully convert to cartoon style.
                        Make it look professional, high-quality, and authentic to the {selected_cartoon_style} style.
                        """
                        
                        # Generate a new cartoon image based on the description of the realistic image
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=style_prompt,
                            n=1,
                            size="1024x1024",
                            quality="standard"
                        )
                        
                        cartoon_image_url = response.data[0].url
                        st.session_state.cartoon_images.append({
                            "url": cartoon_image_url,
                            "style": selected_cartoon_style,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.success("Image successfully converted to cartoon style!")
                        st.image(cartoon_image_url, use_column_width=True)
                        
                        # FIXED: Button to go to Etsy Metadata tab using the custom function
                        if st.button("Go to Etsy Metadata"):
                            select_image(cartoon_image_url, 'Etsy Metadata')
                        
                except Exception as e:
                    st.error(f"Error converting image: {str(e)}")
                    st.error("Please try a different image or style.")
    else:
        st.info("Please first create and select an image from the 'Image Generation' tab.")
        if st.button("Go to Image Generation"):
            st.session_state.active_tab = 'Image Generation'
            st.rerun()
        
    # Previous conversions
    if st.session_state.cartoon_images:
        st.markdown('<div class="section-title"><h3>Previous Conversions</h3></div>', unsafe_allow_html=True)
        st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
        for i, img_data in enumerate(st.session_state.cartoon_images):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.image(img_data["url"], use_column_width=True, caption=f"{img_data['style']} - {img_data['timestamp']}")
            with col2:
                # FIXED: Button to use this cartoon for Etsy metadata
                if st.button(f"Use for Etsy #{i+1}", key=f"use_etsy_{i}"):
                    select_image(img_data["url"], 'Etsy Metadata')
        st.markdown('</div>', unsafe_allow_html=True)

def show_etsy_metadata():
    """Shows the Etsy metadata interface"""
    st.markdown('<div class="section-title"><h3>Generate Etsy Metadata</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.cartoon_images:
        st.markdown("#### Last Converted Image")
        st.image(st.session_state.cartoon_images[-1]["url"], width=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_title = st.text_input("Product Title", f"Custom {st.session_state.cartoon_images[-1]['style']} Style Portrait")
            product_description = st.text_area(
                "Product Description", 
                f"""Custom {st.session_state.cartoon_images[-1]['style']} style digital portrait created from your real photo.
                Completely personalized, delivered as a high-resolution digital file.
                Perfect for printing, instantly downloadable."""
            )
        
        with col2:
            tags = st.text_input(
                "Tags (comma separated)",
                f"custom portrait, {st.session_state.cartoon_images[-1]['style'].lower()}, digital art, personalized gift, family portrait"
            )
            price = st.number_input("Price ($)", min_value=5.0, value=19.99, step=1.0)
            delivery_format = st.selectbox(
                "Delivery Format",
                ["Digital Download (JPG & PNG)", "Digital Download + Print", "Print Only"]
            )
        
        # Generate metadata button
        if st.button("Generate Etsy Metadata"):
            with st.spinner("Generating metadata..."):
                # Add loading animation
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
                    "style": st.session_state.cartoon_images[-1]["style"],
                    "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "image_url": st.session_state.cartoon_images[-1]["url"]
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
                    f"Include '{st.session_state.cartoon_images[-1]['style']}' in your title for better search matching",
                    "Add 'personalized gift' as it's a high-search term",
                    "Include specific occasions like 'birthday gift' or 'anniversary present'",
                    "Mention 'custom portrait' as it's a popular search term",
                    "Use long-tail keywords like 'family cartoon portrait' for better targeting",
                    "Include relevant seasonal keywords during holidays",
                    "Add material terms like 'digital download' or 'printable art'",
                    "Mention turnaround time in your description for better customer expectations"
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
                    "Offer different size options at different price points"
                ]
                
                for tip in marketing_tips:
                    st.markdown(f"• {tip}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.info("Please first convert an image to cartoon style in the 'Cartoon Conversion' tab.")
        if st.button("Go to Cartoon Conversion"):
            st.session_state.active_tab = 'Cartoon Conversion'
            st.rerun()

# Main tabs
tab_names = ["Image Generation", "Cartoon Conversion", "Etsy Metadata"]
tabs = st.tabs(tab_names)

# Set active tab based on session state
with tabs[0]:
    if st.session_state.active_tab == 'Image Generation':
        show_image_generation()
    else:
        if st.button("Switch to Image Generation", key="switch_to_tab1"):
            st.session_state.active_tab = 'Image Generation'
            st.rerun()

with tabs[1]:
    if st.session_state.active_tab == 'Cartoon Conversion':
        show_cartoon_conversion()
    else:
        if st.button("Switch to Cartoon Conversion", key="switch_to_tab2"):
            st.session_state.active_tab = 'Cartoon Conversion'
            st.rerun()

with tabs[2]:
    if st.session_state.active_tab == 'Etsy Metadata':
        show_etsy_metadata()
    else:
        if st.button("Switch to Etsy Metadata", key="switch_to_tab3"):
            st.session_state.active_tab = 'Etsy Metadata'
            st.rerun()

# App workflow guide
st.markdown('<div class="section-title"><h3>How It Works</h3></div>', unsafe_allow_html=True)
st.markdown("""
1. **Generate Realistic Images**: Start by selecting a category and idea, then generate a realistic image
2. **Convert to Cartoon**: Select your favorite image and convert it to your preferred cartoon style
3. **Create Etsy Metadata**: Generate product details to help sell your custom portraits online
""")

# Footer
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("© 2025 AI Image Generation Tool | All Rights Reserved.")
st.markdown("Powered by OpenAI API")
st.markdown('</div>', unsafe_allow_html=True)
