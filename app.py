import streamlit as st
import os
import io
import base64
import json
import time
import uuid
from datetime import datetime
from PIL import Image
import openai
from google.cloud import aiplatform
from google.oauth2 import service_account

# Set page config
st.set_page_config(
    page_title="AI Image Studio & Etsy Metadata Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-powered image creation and transformation system"
    }
)

# Load secrets
openai.api_key = st.secrets["openai_api_key"]

# Load Google Cloud credentials from secrets
google_credentials_json = st.secrets["google_credentials"]
credentials = service_account.Credentials.from_service_account_info(
    json.loads(google_credentials_json)
)

# Initialize Vertex AI with credentials
aiplatform.init(credentials=credentials)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e2130;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e57a5 !important;
    }
    .image-card {
        border: 1px solid #4e57a5;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0px;
        background-color: #1e2130;
    }
    .style-button {
        margin: 5px;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .style-button-selected {
        border: 2px solid #4e57a5;
        background-color: #2e3151;
    }
    .style-button-unselected {
        border: 1px solid #31343a;
        background-color: #1e2130;
    }
    .result-container {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0px;
    }
    .download-button {
        background-color: #4e57a5;
        color: white;
        padding: 8px 16px;
        border-radius: 5px;
        text-decoration: none;
        margin-top: 10px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_realistic_image' not in st.session_state:
    st.session_state.current_realistic_image = None
if 'current_cartoon_image' not in st.session_state:
    st.session_state.current_cartoon_image = None
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""
if 'current_cartoon_style' not in st.session_state:
    st.session_state.current_cartoon_style = ""
if 'etsy_metadata' not in st.session_state:
    st.session_state.etsy_metadata = {"description": "", "tags": []}

# Helper functions
def generate_prompt(category, idea, ethnicity, style, custom_notes):
    """Generate a detailed image prompt using GPT-4"""
    try:
        system_message = """You are an expert image prompt engineer. 
        Create a detailed, photorealistic image prompt based on the inputs.
        Start with "A photorealistic image of..." and include details on composition, 
        lighting, atmosphere, camera lens, and angle. Be specific and vivid.
        Avoid mentioning AI-related terms or artifacts."""
        
        user_message = f"""
        Create a detailed image prompt with these elements:
        - Category: {category}
        - Scene/Idea: {idea}
        - Ethnicity/People: {ethnicity}
        - Visual Style: {style}
        - Additional Details: {custom_notes}
        
        Make the prompt detailed enough for a high-quality photorealistic image.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating prompt: {str(e)}")
        return None

def generate_cartoon_prompt(original_prompt, cartoon_style):
    """Generate a cartoon-style prompt based on the original prompt"""
    try:
        system_message = """You are an expert in creating prompts for cartoon-style image generation.
        Your task is to adapt a photorealistic image prompt into a cartoon style while preserving
        the essential elements, composition, and emotion of the original scene."""
        
        user_message = f"""
        Original photorealistic prompt: "{original_prompt}"
        
        Convert this prompt to create a {cartoon_style} style animated version.
        Maintain the same scene, characters, actions, and emotions, but adapt the visual style.
        Start with "A {cartoon_style} style animated scene of..."
        Be specific about the cartoon style's characteristic visual elements.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating cartoon prompt: {str(e)}")
        return None

def generate_image_with_imagen(prompt):
    """Generate an image using Google's Imagen via Vertex AI"""
    try:
        # Initialize the model
        model = aiplatform.models.Model("projects/your-project/locations/us-central1/models/imagegeneration@002")
        
        # Generate the image
        response = model.predict(
            instances=[{"prompt": prompt}],
            parameters={"sampleCount": 1}
        )
        
        # Process the response
        image_data = response.predictions[0]["image"]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to base64 for display
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

def generate_etsy_metadata(image_base64, product_title, product_type, product_price, cartoon_style, original_prompt):
    """Generate Etsy metadata using GPT-4"""
    try:
        system_message = """You are an Etsy SEO expert who creates optimized product listings.
        Generate a compelling product description and 13 SEO-optimized tags for an Etsy listing.
        Each tag must be 20 characters or less. Format the description with markdown for readability."""
        
        user_message = f"""
        Create an Etsy product listing for a digital art print with these details:
        
        - Product Title: {product_title}
        - Product Type: {product_type}
        - Price: {product_price}
        - Art Style: {cartoon_style}
        - Image Description: {original_prompt}
        
        Please provide:
        1. A SEO-optimized product description (300-400 words) with markdown formatting
        2. Exactly 13 Etsy tags, each 20 characters or less
        
        Make the description compelling, highlight the unique aspects of the art style,
        and emphasize the emotional connection to the image.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse the response to separate description and tags
        parts = content.split("Tags:")
        
        description = parts[0].strip()
        if len(parts) > 1:
            tags_text = parts[1].strip()
            # Extract tags from bullet points or commas
            if "•" in tags_text:
                tags = [tag.strip().strip('•').strip() for tag in tags_text.split('\n') if tag.strip()]
            else:
                tags = [tag.strip() for tag in tags_text.split(',')]
            
            # Filter out any empty tags and ensure we have exactly 13
            tags = [tag for tag in tags if tag][:13]
        else:
            tags = []
        
        return {"description": description, "tags": tags}
    except Exception as e:
        st.error(f"Error generating Etsy metadata: {str(e)}")
        return {"description": "", "tags": []}

def save_to_history(realistic_image, cartoon_image, prompt, cartoon_style, cartoon_prompt, etsy_metadata=None):
    """Save the current generation to history"""
    st.session_state.history.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "realistic_image": realistic_image,
        "cartoon_image": cartoon_image,
        "prompt": prompt,
        "cartoon_style": cartoon_style,
        "cartoon_prompt": cartoon_prompt,
        "etsy_metadata": etsy_metadata
    })

def display_image_card(image_base64, title, prompt=None, download_label=None):
    """Display an image in a styled card with optional download button"""
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    
    if image_base64:
        st.markdown(f"""
        <div class="image-card">
            <img src="data:image/png;base64,{image_base64}" style="width: 100%;">
        </div>
        """, unsafe_allow_html=True)
        
        if prompt:
            st.markdown("**Prompt:**")
            st.text_area("", prompt, height=100, key=f"prompt_{title}_{time.time()}")
        
        if download_label:
            # Create download button
            img_bytes = base64.b64decode(image_base64)
            btn = st.download_button(
                label=f"Download {download_label}",
                data=img_bytes,
                file_name=f"{download_label.lower().replace(' ', '_')}_{int(time.time())}.png",
                mime="image/png",
                key=f"download_{title}_{time.time()}"
            )
    else:
        st.markdown("""
        <div class="image-card" style="height: 300px; display: flex; align-items: center; justify-content: center;">
            <p>No image generated yet</p>
        </div>
        """, unsafe_allow_html=True)

# Main app layout
st.title("🎨 AI Image Studio & Etsy Metadata Generator")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🖼️ Realistic Image Generator", 
    "🎭 Cartoon Converter", 
    "🛍️ Etsy Metadata Generator",
    "🕘 Image History"
])

# Tab 1: Realistic Image Generator
with tab1:
    st.header("Create Photorealistic Images")
    
    # Define options
    category_options = [
        "Family & Couple Portraits", 
        "Wedding Portraits", 
        "Birthday Portraits",
        "Graduation Portraits",
        "Professional Portraits",
        "Pet Portraits",
        "Travel Scenes",
        "Holiday & Seasonal",
        "Food & Culinary",
        "Nature & Landscapes"
    ]
    
    idea_options = {
        "Family & Couple Portraits": ["Family Gathering", "Couple Embrace", "Parent and Child", "Siblings", "Extended Family"],
        "Wedding Portraits": ["Wedding Dance", "Bridal Bouquet", "Cake Cutting", "First Kiss", "Wedding Party"],
        "Birthday Portraits": ["Blowing Candles", "Opening Gifts", "Birthday Party", "Birthday Cake", "Birthday Celebration"],
        "Graduation Portraits": ["Cap and Gown", "Diploma Receiving", "Graduation Celebration", "Academic Achievement", "Campus Scene"],
        "Professional Portraits": ["Office Setting", "Business Meeting", "Professional Headshot", "Working Environment", "Team Collaboration"],
        "Pet Portraits": ["Dog Portrait", "Cat Portrait", "Pet with Owner", "Pet Playing", "Pet Outdoors"],
        "Travel Scenes": ["Beach Vacation", "Mountain Hiking", "City Exploration", "Landmark Visit", "Road Trip"],
        "Holiday & Seasonal": ["Christmas Scene", "Halloween Celebration", "Thanksgiving Dinner", "Easter Gathering", "New Year Celebration"],
        "Food & Culinary": ["Gourmet Dish", "Baking Scene", "Family Dinner", "Restaurant Setting", "Food Preparation"],
        "Nature & Landscapes": ["Mountain View", "Beach Sunset", "Forest Path", "Lake Reflection", "Desert Landscape"]
    }
    
    ethnicity_options = ["European", "Asian", "African", "Middle Eastern", "Hispanic/Latino", "South Asian", "East Asian", "Mixed"]
    
    style_options = ["Natural Light", "Studio Portrait", "Vintage", "Modern", "Artistic", "Dramatic", "Minimalist", "Vibrant", "Black & White", "Golden Hour"]
    
    # Create form for inputs
    with st.form(key="realistic_image_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Select Category", category_options)
            
            # Dynamically update idea options based on selected category
            if category in idea_options:
                idea = st.selectbox("Select Scene/Idea", idea_options[category])
            else:
                idea = st.text_input("Enter Scene/Idea")
                
            ethnicity = st.selectbox("Select Ethnicity/People", ethnicity_options)
        
        with col2:
            style = st.selectbox("Select Visual Style", style_options)
            custom_notes = st.text_area("Additional Details/Notes", placeholder="Add any specific details you want to include...")
        
        submit_button = st.form_submit_button("Generate Realistic Image")
    
    # Process form submission
    if submit_button:
        with st.spinner("Generating prompt..."):
            prompt = generate_prompt(category, idea, ethnicity, style, custom_notes)
            
            if prompt:
                st.session_state.current_prompt = prompt
                
                with st.spinner("Generating image..."):
                    image_base64 = generate_image_with_imagen(prompt)
                    
                    if image_base64:
                        st.session_state.current_realistic_image = image_base64
                        st.success("Image generated successfully!")
    
    # Display the generated image
    if st.session_state.current_realistic_image:
        display_image_card(
            st.session_state.current_realistic_image, 
            "Generated Realistic Image", 
            st.session_state.current_prompt,
            "Realistic Image"
        )

# Tab 2: Cartoon Converter
with tab2:
    st.header("Convert to Cartoon Style")
    
    # Check if we have a realistic image to convert
    if st.session_state.current_realistic_image:
        st.markdown("Select a cartoon style to convert your image:")
        
        # Define cartoon styles
        cartoon_styles = ["Pixar 3D", "Studio Ghibli", "Anime", "The Simpsons", "South Park", 
                         "Disney Animation", "Cartoon Network", "Claymation", "Comic Book", "Watercolor Illustration"]
        
        # Create style selection buttons in a grid
        cols = st.columns(5)
        selected_style = st.session_state.current_cartoon_style
        
        for i, style in enumerate(cartoon_styles):
            col_idx = i % 5
            with cols[col_idx]:
                button_class = "style-button style-button-selected" if style == selected_style else "style-button style-button-unselected"
                st.markdown(f"""
                <div class="{button_class}" onclick="document.querySelector('#style_{i}').click()">
                    {style}
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden button to capture the click
                if st.button(style, key=f"style_{i}", help=f"Convert to {style} style"):
                    st.session_state.current_cartoon_style = style
                    st.experimental_rerun()
        
        # Generate cartoon if a style is selected
        if st.session_state.current_cartoon_style:
            if st.button("Generate Cartoon Image"):
                with st.spinner(f"Converting to {st.session_state.current_cartoon_style} style..."):
                    cartoon_prompt = generate_cartoon_prompt(st.session_state.current_prompt, st.session_state.current_cartoon_style)
                    
                    if cartoon_prompt:
                        cartoon_image_base64 = generate_image_with_imagen(cartoon_prompt)
                        
                        if cartoon_image_base64:
                            st.session_state.current_cartoon_image = cartoon_image_base64
                            st.session_state.current_cartoon_prompt = cartoon_prompt
                            
                            # Save to history
                            save_to_history(
                                st.session_state.current_realistic_image,
                                cartoon_image_base64,
                                st.session_state.current_prompt,
                                st.session_state.current_cartoon_style,
                                cartoon_prompt
                            )
                            
                            st.success(f"Image converted to {st.session_state.current_cartoon_style} style!")
        
        # Display images side by side
        if st.session_state.current_cartoon_image:
            col1, col2 = st.columns(2)
            
            with col1:
                display_image_card(
                    st.session_state.current_realistic_image, 
                    "Original Realistic Image", 
                    st.session_state.current_prompt,
                    "Realistic Image"
                )
            
            with col2:
                display_image_card(
                    st.session_state.current_cartoon_image, 
                    f"{st.session_state.current_cartoon_style} Version", 
                    st.session_state.current_cartoon_prompt,
                    "Cartoon Image"
                )
    else:
        st.info("Please generate a realistic image first in the 'Realistic Image Generator' tab.")

# Tab 3: Etsy Metadata Generator
with tab3:
    st.header("Generate Etsy Product Metadata")
    
    # Check if we have a cartoon image
    if st.session_state.current_cartoon_image:
        # Display the cartoon image
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(f"data:image/png;base64,{st.session_state.current_cartoon_image}", caption=f"{st.session_state.current_cartoon_style} Style Image")
        
        with col2:
            # Form for Etsy product details
            with st.form(key="etsy_metadata_form"):
                product_title = st.text_input("Product Title", placeholder="e.g., Custom Digital Portrait in Pixar Style")
                
                product_type_options = ["Digital Download", "Physical Print", "Custom Order", "Print on Demand"]
                product_type = st.selectbox("Product Type", product_type_options)
                
                product_price = st.text_input("Product Price", placeholder="e.g., $25.99")
                
                submit_etsy = st.form_submit_button("Generate Etsy Metadata")
            
            if submit_etsy:
                with st.spinner("Generating Etsy metadata..."):
                    metadata = generate_etsy_metadata(
                        st.session_state.current_cartoon_image,
                        product_title,
                        product_type,
                        product_price,
                        st.session_state.current_cartoon_style,
                        st.session_state.current_prompt
                    )
                    
                    if metadata:
                        st.session_state.etsy_metadata = metadata
                        
                        # Update the history entry with metadata
                        for entry in st.session_state.history:
                            if entry.get("cartoon_image") == st.session_state.current_cartoon_image:
                                entry["etsy_metadata"] = metadata
                                break
                        
                        st.success("Etsy metadata generated successfully!")
        
        # Display generated metadata
        if st.session_state.etsy_metadata and st.session_state.etsy_metadata["description"]:
            st.markdown("## Generated Etsy Metadata")
            
            # Display in a styled container
            st.markdown("""
            <div class="result-container">
                <h3>Product Description</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(st.session_state.etsy_metadata["description"])
            
            # Download button for description
            description_text = st.session_state.etsy_metadata["description"]
            st.download_button(
                label="Download Description",
                data=description_text,
                file_name=f"etsy_description_{int(time.time())}.md",
                mime="text/markdown"
            )
            
            # Display tags
            st.markdown("""
            <div class="result-container">
                <h3>Etsy Tags (13)</h3>
            </div>
            """, unsafe_allow_html=True)
            
            tags = st.session_state.etsy_metadata["tags"]
            
            # Display tags in a grid
            tag_cols = st.columns(3)
            for i, tag in enumerate(tags):
                col_idx = i % 3
                with tag_cols[col_idx]:
                    st.markdown(f"• {tag}")
            
            # Download button for tags
            tags_text = "\n".join([f"• {tag}" for tag in tags])
            st.download_button(
                label="Download Tags",
                data=tags_text,
                file_name=f"etsy_tags_{int(time.time())}.txt",
                mime="text/plain"
            )
    else:
        st.info("Please generate a cartoon image first in the 'Cartoon Converter' tab.")

# Tab 4: Image History
with tab4:
    st.header("Image Generation History")
    
    if not st.session_state.history:
        st.info("No images in history yet. Generate some images to see them here.")
    else:
        # Sort history by timestamp (newest first)
        sorted_history = sorted(st.session_state.history, key=lambda x: x["timestamp"], reverse=True)
        
        for i, entry in enumerate(sorted_history):
            with st.expander(f"Generation {i+1} - {entry['timestamp']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Realistic Image")
                    st.image(f"data:image/png;base64,{entry['realistic_image']}", use_column_width=True)
                    st.markdown(f"**Prompt:** {entry['prompt']}")
                    
                    # Download button
                    img_bytes = base64.b64decode(entry['realistic_image'])
                    st.download_button(
                        label="Download Realistic Image",
                        data=img_bytes,
                        file_name=f"realistic_{i}_{int(time.time())}.png",
                        mime="image/png",
                        key=f"dl_real_{i}"
                    )
                
                with col2:
                    st.markdown(f"### {entry['cartoon_style']} Version")
                    if entry.get('cartoon_image'):
                        st.image(f"data:image/png;base64,{entry['cartoon_image']}", use_column_width=True)
                        st.markdown(f"**Prompt:** {entry.get('cartoon_prompt', 'No prompt available')}")
                        
                        # Download button
                        img_bytes = base64.b64decode(entry['cartoon_image'])
                        st.download_button(
                            label="Download Cartoon Image",
                            data=img_bytes,
                            file_name=f"cartoon_{i}_{int(time.time())}.png",
                            mime="image/png",
                            key=f"dl_cartoon_{i}"
                        )
                    else:
                        st.write("No cartoon version available")
                
                # Show Etsy metadata if available
                if entry.get('etsy_metadata'):
                    st.markdown("### Etsy Metadata")
                    
                    # Description
                    st.markdown("#### Product Description")
                    st.markdown(entry['etsy_metadata']['description'])
                    
                    # Tags
                    st.markdown("#### Tags")
                    tags = entry['etsy_metadata']['tags']
                    tag_cols = st.columns(3)
                    for j, tag in enumerate(tags):
                        col_idx = j % 3
                        with tag_cols[col_idx]:
                            st.markdown(f"• {tag}")
                
                # Buttons to reuse this entry
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Reuse Realistic Image", key=f"reuse_real_{i}"):
                        st.session_state.current_realistic_image = entry['realistic_image']
                        st.session_state.current_prompt = entry['prompt']
                        st.session_state.current_cartoon_image = None
                        st.session_state.current_cartoon_style = ""
                        st.session_state.etsy_metadata = {"description": "", "tags": []}
                        st.experimental_rerun()
                
                with col2:
                    if entry.get('cartoon_image') and st.button("Reuse Cartoon Image", key=f"reuse_cartoon_{i}"):
                        st.session_state.current_realistic_image = entry['realistic_image']
                        st.session_state.current_prompt = entry['prompt']
                        st.session_state.current_cartoon_image = entry['cartoon_image']
                        st.session_state.current_cartoon_style = entry['cartoon_style']
                        st.session_state.current_cartoon_prompt = entry.get('cartoon_prompt', '')
                        st.session_state.etsy_metadata = {"description": "", "tags": []}
                        st.experimental_rerun()
                
                with col3:
                    if entry.get('etsy_metadata') and st.button("Reuse Etsy Metadata", key=f"reuse_etsy_{i}"):
                        st.session_state.current_realistic_image = entry['realistic_image']
                        st.session_state.current_prompt = entry['prompt']
                        st.session_state.current_cartoon_image = entry['cartoon_image']
                        st.session_state.current_cartoon_style = entry['cartoon_style']
                        st.session_state.current_cartoon_prompt = entry.get('cartoon_prompt', '')
                        st.session_state.etsy_metadata = entry['etsy_metadata']
                        st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("### 🎨 AI Image Studio & Etsy Metadata Generator")
st.markdown("Create realistic images, convert them to cartoon styles, and generate Etsy-ready product metadata.")
