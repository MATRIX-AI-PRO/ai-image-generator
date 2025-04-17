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
    }
    .stButton button:hover {
        background-color: #ff7070;
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
    }
    .drop-zone:hover {
        border-color: #ff4b4b;
    }
    .result-container {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .header img {
        margin-right: 15px;
    }
    .section-title {
        background-color: #2a2a2a;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #2a2a2a;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .image-gallery {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
    }
    .image-card {
        background-color: #2a2a2a;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        transition: transform 0.3s;
    }
    .image-card:hover {
        transform: scale(1.03);
    }
    .tips-box {
        background-color: #2a2a2a;
        border-left: 4px solid #ff4b4b;
        padding: 10px 15px;
        margin-bottom: 15px;
        border-radius: 0 5px 5px 0;
    }
    .metadata-container {
        background-color: #2a2a2a;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
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

        
        # Number of images
        num_images = st.slider("Number of Images to Generate", 1, 4, 2)
        
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
            You need to write a prompt for DALL-E to create realistic, high-quality images.
            Based on the given information, create a detailed, realistic, and aesthetic photo prompt.
            The prompt should be in English and include all necessary details for a realistic photo.
            """
            
            user_prompt = f"""
            Category: {selected_category}
            Idea: {selected_idea}
            Appearance: {selected_ethnicity}
            Style: {selected_style}
            Additional details: {additional_details}
            
            Please create a DALL-E prompt for a realistic, high-quality photo based on this information.
            The prompt should include all necessary details for the photo shoot: composition, lighting, atmosphere, color scheme, etc.
            Start the prompt with "A photorealistic image" and include directives to avoid AI-generated image feel.
            """
            
            try:
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
                st.markdown("#### Generated Realistic Prompt:")
                st.text_area("", realistic_prompt, height=150, key="prompt_result")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error generating prompt: {e}")
        
        # Generate images button
        if st.button("Generate Images") and st.session_state.realistic_prompt:
            try:
                with st.spinner("Generating images..."):
                    width, height = map(int, selected_size.split('x'))
                    
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=st.session_state.realistic_prompt,
                        n=num_images,
                        size=selected_size,
                        quality=selected_quality
                    )
                    
                    images = []
                    for data in response.data:
                        image_url = data.url
                        images.append(image_url)
                    
                    st.session_state.realistic_images = images
                    
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.markdown("#### Generated Realistic Images:")
                    
                    # Show images
                    image_cols = st.columns(min(num_images, 2))
                    for i, image_url in enumerate(st.session_state.realistic_images):
                        col_idx = i % len(image_cols)
                        with image_cols[col_idx]:
                            st.image(image_url, use_column_width=True)
                            if st.button(f"Select This Image #{i+1}", key=f"select_img_{i}"):
                                st.session_state.selected_image = image_url
                                st.session_state.active_tab = 'Cartoon Conversion'
                                st.success(f"Image #{i+1} selected! You can now go to the Cartoon Conversion tab.")
                                st.rerun()  # Reload page
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error generating images: {e}")

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
                        # Prompt for converting realistic image to cartoon style
                        style_prompt = f"""
                        Transform this realistic image into a {selected_cartoon_style} cartoon style. 
                        {style_details[selected_cartoon_style]}. 
                        {additional_style_details}
                        Maintain the same composition, characters, and scene, but fully convert to cartoon style.
                        Make it look professional, high-quality, and authentic to the {selected_cartoon_style} style.
                        """
                        
                        # Convert using DALL-E API
                        response = client.images.edit(
                            model="dall-e-3",
                            image=Image.open(io.BytesIO(requests.get(st.session_state.selected_image).content)),
                            prompt=style_prompt,
                            n=1,
                            size="1024x1024"
                        )
                        
                        cartoon_image_url = response.data[0].url
                        st.session_state.cartoon_images.append({
                            "url": cartoon_image_url,
                            "style": selected_cartoon_style,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.success("Image successfully converted to cartoon style!")
                        st.image(cartoon_image_url, use_column_width=True)
                        
                        # Button to go to Etsy Metadata tab
                        if st.button("Go to Etsy Metadata"):
                            st.session_state.active_tab = 'Etsy Metadata'
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"Error converting image: {e}")
    else:
        st.info("Please first create and select an image from the 'Image Generation' tab.")
        if st.button("Go to Image Generation"):
            st.session_state.active_tab = 'Image Generation'
            st.rerun()
        
    # Previous conversions
    if st.session_state.cartoon_images:
        st.markdown("#### Previous Conversions")
        for i, img_data in enumerate(st.session_state.cartoon_images):
            st.image(img_data["url"], caption=f"{img_data['style']} - {img_data['timestamp']}", width=200)

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
            href = f'<a href="data:application/json;base64,{b64}" download="etsy_metadata.json">Download Metadata File</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        st.info("Please first convert an image to cartoon style in the 'Cartoon Conversion' tab.")
        if st.button("Go to Cartoon Conversion"):
            st.session_state.active_tab = 'Cartoon Conversion'
            st.rerun()

# Main tabs
tab_names = ["Image Generation", "Cartoon Conversion", "Etsy Metadata"]
tabs = st.tabs(tab_names)

# Set active tab
active_tab_index = tab_names.index(st.session_state.active_tab)

# Show tabs
with tabs[0]:
    if st.session_state.active_tab == 'Image Generation':
        show_image_generation()
    else:
        st.button("Switch to This Tab", key="switch_to_tab1", on_click=lambda: setattr(st.session_state, 'active_tab', 'Image Generation') or st.rerun())

with tabs[1]:
    if st.session_state.active_tab == 'Cartoon Conversion':
        show_cartoon_conversion()
    else:
        st.button("Switch to This Tab", key="switch_to_tab2", on_click=lambda: setattr(st.session_state, 'active_tab', 'Cartoon Conversion') or st.rerun())

with tabs[2]:
    if st.session_state.active_tab == 'Etsy Metadata':
        show_etsy_metadata()
    else:
        st.button("Switch to This Tab", key="switch_to_tab3", on_click=lambda: setattr(st.session_state, 'active_tab', 'Etsy Metadata') or st.rerun())

# Footer
st.markdown("---")
st.markdown("© 2025 AI Image Generation Tool | All Rights Reserved.")
