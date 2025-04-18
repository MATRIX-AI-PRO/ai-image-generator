import streamlit as st
import base64
import io
import json
import os
import time
from datetime import datetime
from PIL import Image
import openai
from google.cloud import aiplatform
from google.oauth2 import service_account
import uuid

# Page configuration and title
st.set_page_config(
    page_title="AI Image Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
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
        background-color: #262730;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e57d4 !important;
    }
    .image-container {
        background-color: #1a1c24;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .download-btn {
        background-color: #4e57d4;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        text-decoration: none;
        display: inline-block;
        margin-top: 10px;
    }
    .metadata-container {
        background-color: #1a1c24;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .image-card {
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
    }
    .style-option {
        cursor: pointer;
        border: 2px solid #333;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin: 5px;
    }
    .style-option.selected {
        border-color: #4e57d4;
        background-color: rgba(78, 87, 212, 0.2);
    }
    .stButton button {
        background-color: #4e57d4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None
if 'cartoon_image' not in st.session_state:
    st.session_state.cartoon_image = None
if 'cartoon_prompt' not in st.session_state:
    st.session_state.cartoon_prompt = None
if 'etsy_description' not in st.session_state:
    st.session_state.etsy_description = None
if 'etsy_tags' not in st.session_state:
    st.session_state.etsy_tags = None

# Authentication setup
def setup_openai():
    """Set up OpenAI API with credentials from Streamlit secrets"""
    openai.api_key = st.secrets["openai_api_key"]

def setup_google_ai():
    """Set up Google Cloud AI Platform with credentials from Streamlit secrets"""
    # Parse the credentials JSON string from secrets
    credentials_dict = json.loads(st.secrets["google_credentials"])
    
    # Create credentials object from the parsed JSON
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    
    # Initialize the AI Platform with the credentials
    aiplatform.init(
        project=credentials_dict["project_id"],
        location="us-central1",
        credentials=credentials
    )
    
    return credentials

# Helper functions
def generate_prompt_with_openai(category, idea, ethnicity, style, extra_notes):
    """Generate detailed image prompt using OpenAI GPT-4"""
    setup_openai()
    
    system_message = """You are an expert image prompt engineer. Create a detailed, photorealistic image prompt 
    based on the provided elements. The prompt should start with 'A photorealistic image of' and include 
    specific details about composition, lighting, atmosphere, and subject features. Make it detailed enough 
    for an AI image generator to create a high-quality, realistic image. Don't include any watermarks, 
    signatures, or text in the image description."""
    
    user_message = f"""
    Create a detailed image prompt based on these elements:
    - Category: {category}
    - Idea: {idea}
    - Ethnicity: {ethnicity}
    - Style: {style}
    - Additional details: {extra_notes}
    
    The prompt should be detailed, vivid, and optimized for photorealistic image generation.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def generate_image_with_google(prompt):
    """Generate image using Google Vertex AI Imagen"""
    credentials = setup_google_ai()
    
    # Create the Imagen model
    model = aiplatform.models.Model.get_by_name("imagegeneration@002")
    
    # Generate the image
    response = model.predict(
        prompt=prompt,
        parameters={
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "negativePrompt": "deformed, ugly, watermark, signature, text, low quality"
        }
    )
    
    # Extract the base64 image from the response
    image_b64 = response.predictions[0]
    
    # Convert base64 to image bytes
    image_bytes = base64.b64decode(image_b64)
    
    return image_bytes, image_b64

def generate_cartoon_prompt(original_prompt, cartoon_style):
    """Generate a cartoon-style prompt based on the original prompt"""
    setup_openai()
    
    system_message = """You are an expert image prompt engineer specialized in cartoon and stylized art. 
    Your task is to convert a photorealistic image prompt into a stylized cartoon prompt while preserving 
    the essential elements, composition, and emotion of the original scene."""
    
    user_message = f"""
    Original photorealistic prompt: "{original_prompt}"
    
    Convert this into a prompt for generating an image in {cartoon_style} style. 
    Maintain the same scene, characters, and composition, but adapt the description to fit the {cartoon_style} 
    aesthetic. The new prompt should start with "A {cartoon_style} style illustration of" and include 
    style-specific details.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def generate_etsy_description(image_prompt, product_title, product_type):
    """Generate SEO-friendly Etsy product description"""
    setup_openai()
    
    system_message = """You are an Etsy marketing expert who creates compelling, SEO-optimized product 
    descriptions. Your descriptions should be engaging, highlight key features, and include relevant 
    keywords for search optimization."""
    
    user_message = f"""
    Create an SEO-optimized Etsy product description for:
    
    Product Title: {product_title}
    Product Type: {product_type}
    Image Description: {image_prompt}
    
    The description should:
    1. Be 3-4 paragraphs long
    2. Include 3-5 bullet points highlighting key features
    3. Mention materials, size options, and customization if applicable
    4. Include relevant keywords for Etsy search optimization
    5. Have a compelling call-to-action
    
    Format with markdown for easy reading.
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
    
    return response.choices[0].message.content.strip()

def generate_etsy_tags(product_title, product_type, image_prompt):
    """Generate SEO-friendly Etsy tags (13 tags, each ≤20 characters)"""
    setup_openai()
    
    system_message = """You are an Etsy SEO expert who creates optimized tags for product listings. 
    Create exactly 13 tags, each 20 characters or less, that will help the product appear in relevant searches."""
    
    user_message = f"""
    Create 13 SEO-optimized Etsy tags for:
    
    Product Title: {product_title}
    Product Type: {product_type}
    Image Description: {image_prompt}
    
    Requirements:
    1. Exactly 13 tags
    2. Each tag must be 20 characters or less
    3. Include a mix of specific and broader terms
    4. Focus on searchable keywords
    5. Return as a simple bullet list with one tag per line
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=400,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def download_image(image_bytes, filename):
    """Create a download link for an image"""
    b64 = base64.b64encode(image_bytes).decode()
    href = f'<a href="data:image/jpeg;base64,{b64}" download="{filename}" class="download-btn">Download Image</a>'
    return href

def save_to_history(image_type, image_bytes, prompt, timestamp=None):
    """Save generated image to history"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    image_id = str(uuid.uuid4())
    
    st.session_state.generated_images.append({
        "id": image_id,
        "type": image_type,
        "image": image_bytes,
        "prompt": prompt,
        "timestamp": timestamp
    })
    
    return image_id

def display_image_with_options(image_bytes, prompt, image_type="realistic"):
    """Display an image with download options"""
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.image(image_bytes, use_column_width=True)
        
    with col2:
        st.markdown("### Image Details")
        st.markdown(f"**Type:** {image_type.capitalize()}")
        
        with st.expander("View Prompt"):
            st.write(prompt)
        
        filename = f"{image_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        st.markdown(download_image(image_bytes, filename), unsafe_allow_html=True)
        
        if image_type == "realistic":
            if st.button("Convert to Cartoon", key=f"convert_{uuid.uuid4()}"):
                st.session_state.current_image = image_bytes
                st.session_state.current_prompt = prompt
                st.experimental_rerun()

# Main app
def main():
    st.title("🎨 AI Image Studio")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🖼️ Realistic Image Generator", 
        "🎭 Cartoon Converter", 
        "🛍️ Etsy Metadata Generator",
        "📚 Image History"
    ])
    
    # Tab 1: Realistic Image Generator
    with tab1:
        st.header("Generate Photorealistic Images")
        
        with st.form("image_generation_form"):
            # Category selection
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
            selected_category = st.selectbox("Select Category", category_options, key="category_select")
            
            # Idea selection based on category
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
                    "Mountain Trip",
                    "City Exploration",
                    "Camping Memory",
                    "Landmark Photo",
                    "Sunset Moment",
                    "Family Trip",
                    "Holiday Tradition"
                ]
            }
            
            selected_idea = st.selectbox("Select Idea", idea_options.get(selected_category, []), key="idea_select")
            
            # Ethnicity selection
            ethnicity_options = [
                "European", "Asian", "African", "Middle Eastern", 
                "Hispanic/Latino", "South Asian", "East Asian", "Mixed"
            ]
            selected_ethnicity = st.selectbox("Select Ethnicity", ethnicity_options, key="ethnicity_select")
            
            # Style selection
            style_options = [
                "Natural Light", "Studio Portrait", "Vintage", "Modern", 
                "Dramatic", "Minimalist", "Artistic", "Candid"
            ]
            selected_style = st.selectbox("Select Style", style_options, key="style_select")
            
            # Extra notes
            extra_notes = st.text_area(
                "Additional Details (optional)",
                placeholder="Add specific details like: outdoor setting, time of day, specific props, emotions, etc.",
                key="extra_notes"
            )
            
            # Submit button
            submitted = st.form_submit_button("Generate Image")
        
        # Process form submission
        if submitted:
            with st.spinner("Generating prompt with AI..."):
                prompt = generate_prompt_with_openai(
                    selected_category, 
                    selected_idea, 
                    selected_ethnicity, 
                    selected_style, 
                    extra_notes
                )
                st.session_state.current_prompt = prompt
            
            st.success("Prompt generated successfully!")
            
            with st.spinner("Creating image with Google Imagen..."):
                try:
                    image_bytes, image_b64 = generate_image_with_google(prompt)
                    st.session_state.current_image = image_bytes
                    
                    # Save to history
                    save_to_history("realistic", image_bytes, prompt)
                    
                    st.success("Image generated successfully!")
                    
                    # Display the image
                    st.markdown("### Generated Image")
                    display_image_with_options(image_bytes, prompt)
                    
                except Exception as e:
                    st.error(f"Error generating image: {str(e)}")
    
    # Tab 2: Cartoon Converter
    with tab2:
        st.header("Convert Images to Cartoon Style")
        
        # Check if we have a current image to work with
        if st.session_state.current_image is not None:
            st.markdown("### Original Image")
            st.image(st.session_state.current_image, width=300)
            
            # Cartoon style selection
            st.markdown("### Select Cartoon Style")
            
            cartoon_styles = [
                "Pixar 3D", "Disney Animation", "Studio Ghibli", "Anime", 
                "The Simpsons", "South Park", "Cartoon Network", "Manga"
            ]
            
            col1, col2 = st.columns(2)
            with col1:
                selected_style = st.radio("Choose Style", cartoon_styles)
            
            # Generate cartoon button
            if st.button("Generate Cartoon Version"):
                with st.spinner("Creating cartoon prompt..."):
                    cartoon_prompt = generate_cartoon_prompt(st.session_state.current_prompt, selected_style)
                    st.session_state.cartoon_prompt = cartoon_prompt
                
                with st.spinner(f"Generating {selected_style} style image..."):
                    try:
                        cartoon_bytes, cartoon_b64 = generate_image_with_google(cartoon_prompt)
                        st.session_state.cartoon_image = cartoon_bytes
                        
                        # Save to history
                        save_to_history("cartoon", cartoon_bytes, cartoon_prompt)
                        
                        st.success("Cartoon image generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating cartoon: {str(e)}")
            
            # Display cartoon result if available
            if st.session_state.cartoon_image is not None:
                st.markdown("### Cartoon Result")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(st.session_state.current_image, caption="Original Image", width=300)
                with col2:
                    st.image(st.session_state.cartoon_image, caption=f"{selected_style} Version", width=300)
                
                with st.expander("View Cartoon Prompt"):
                    st.write(st.session_state.cartoon_prompt)
                
                # Download button for cartoon image
                filename = f"cartoon_{selected_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                st.markdown(download_image(st.session_state.cartoon_image, filename), unsafe_allow_html=True)
                
                # Button to use this image for Etsy metadata
                if st.button("Use for Etsy Metadata"):
                    # Switch to Etsy tab
                    st.experimental_set_query_params(active_tab="etsy")
                    st.experimental_rerun()
        else:
            st.info("No image available for conversion. Please generate an image first in the 'Realistic Image Generator' tab.")
            
            # Option to upload an image
            uploaded_file = st.file_uploader("Or upload an image to convert", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                image_bytes = uploaded_file.getvalue()
                st.session_state.current_image = image_bytes
                
                # Display the uploaded image
                st.image(image_bytes, caption="Uploaded Image", width=300)
                
                # Ask for a description of the image
                image_description = st.text_area(
                    "Please describe this image (for better cartoon conversion)",
                    placeholder="E.g., A family of four sitting on a beach at sunset, smiling at the camera..."
                )
                
                if image_description and st.button("Proceed with This Image"):
                    st.session_state.current_prompt = image_description
                    st.experimental_rerun()
    
    # Tab 3: Etsy Metadata Generator
    with tab3:
        st.header("Generate Etsy Product Metadata")
        
        # Check if we have a cartoon image to work with
        if st.session_state.cartoon_image is not None:
            st.markdown("### Product Image")
            st.image(st.session_state.cartoon_image, width=300)
            
            with st.form("etsy_metadata_form"):
                product_title = st.text_input(
                    "Product Title",
                    placeholder="E.g., Custom Family Portrait, Personalized Cartoon Art..."
                )
                
                product_type = st.selectbox(
                    "Product Type",
                    [
                        "Digital Download", "Physical Print", "Canvas Print", 
                        "Framed Print", "T-shirt Design", "Mug Design", 
                        "Custom Merchandise", "Wall Art"
                    ]
                )
                
                product_price = st.text_input(
                    "Product Price ($)",
                    placeholder="E.g., 29.99"
                )
                
                generate_metadata = st.form_submit_button("Generate Etsy Metadata")
            
            if generate_metadata:
                with st.spinner("Generating SEO-optimized product description..."):
                    description = generate_etsy_description(
                        st.session_state.cartoon_prompt,
                        product_title,
                        product_type
                    )
                    st.session_state.etsy_description = description
                
                with st.spinner("Generating Etsy tags..."):
                    tags = generate_etsy_tags(
                        product_title,
                        product_type,
                        st.session_state.cartoon_prompt
                    )
                    st.session_state.etsy_tags = tags
                
                st.success("Etsy metadata generated successfully!")
            
            # Display metadata if available
            if st.session_state.etsy_description is not None and st.session_state.etsy_tags is not None:
                st.markdown("### Etsy Product Description")
                st.markdown(st.session_state.etsy_description, unsafe_allow_html=True)
                
                st.markdown("### Etsy Tags")
                st.markdown(st.session_state.etsy_tags)
                
                # Download buttons for metadata
                col1, col2 = st.columns(2)
                with col1:
                    description_text = st.session_state.etsy_description
                    description_b64 = base64.b64encode(description_text.encode()).decode()
                    description_href = f'<a href="data:text/plain;base64,{description_b64}" download="etsy_description.txt" class="download-btn">Download Description</a>'
                    st.markdown(description_href, unsafe_allow_html=True)
                
                with col2:
                    tags_text = st.session_state.etsy_tags
                    tags_b64 = base64.b64encode(tags_text.encode()).decode()
                    tags_href = f'<a href="data:text/plain;base64,{tags_b64}" download="etsy_tags.txt" class="download-btn">Download Tags</a>'
                    st.markdown(tags_href, unsafe_allow_html=True)
        else:
            st.info("No cartoon image available. Please generate a cartoon image first in the 'Cartoon Converter' tab.")
            
            # Option to select from history
            if st.session_state.generated_images:
                st.markdown("### Or select an image from your history:")
                
                cartoon_images = [img for img in st.session_state.generated_images if img["type"] == "cartoon"]
                
                if cartoon_images:
                    selected_image_index = st.selectbox(
                        "Select a cartoon image",
                        range(len(cartoon_images)),
                        format_func=lambda i: f"{cartoon_images[i]['timestamp']} - {cartoon_images[i]['prompt'][:50]}..."
                    )
                    
                    selected_image = cartoon_images[selected_image_index]
                    st.image(selected_image["image"], width=300)
                    
                    if st.button("Use This Image"):
                        st.session_state.cartoon_image = selected_image["image"]
                        st.session_state.cartoon_prompt = selected_image["prompt"]
                        st.experimental_rerun()
                else:
                    st.write("No cartoon images found in your history.")
    
    # Tab 4: Image History
    with tab4:
        st.header("Image Generation History")
        
        if not st.session_state.generated_images:
            st.info("No images generated yet. Create some images to see them here!")
        else:
            # Group images by date
            images_by_date = {}
            for img in st.session_state.generated_images:
                date = img["timestamp"].split()[0]
                if date not in images_by_date:
                    images_by_date[date] = []
                images_by_date[date].append(img)
            
            # Display images by date
            for date, images in sorted(images_by_date.items(), reverse=True):
                st.subheader(date)
                
                for i, img_data in enumerate(images):
                    with st.container():
                        st.markdown(f"<div class='image-card'>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.image(img_data["image"], width=150)
                        
                        with col2:
                            st.markdown(f"**Type:** {img_data['type'].capitalize()}")
                            st.markdown(f"**Time:** {img_data['timestamp'].split()[1]}")
                            
                            with st.expander("View Prompt"):
                                st.write(img_data["prompt"])
                            
                            # Action buttons
                            btn_col1, btn_col2, btn_col3 = st.columns(3)
                            
                            with btn_col1:
                                filename = f"{img_data['type']}_{img_data['timestamp'].replace(' ', '_').replace(':', '-')}.jpg"
                                st.markdown(download_image(img_data["image"], filename), unsafe_allow_html=True)
                            
                            with btn_col2:
                                if img_data["type"] == "realistic" and st.button("Convert to Cartoon", key=f"convert_history_{img_data['id']}"):
                                    st.session_state.current_image = img_data["image"]
                                    st.session_state.current_prompt = img_data["prompt"]
                                    # Switch to cartoon tab
                                    st.experimental_set_query_params(active_tab="cartoon")
                                    st.experimental_rerun()
                            
                            with btn_col3:
                                if img_data["type"] == "cartoon" and st.button("Use for Etsy", key=f"etsy_history_{img_data['id']}"):
                                    st.session_state.cartoon_image = img_data["image"]
                                    st.session_state.cartoon_prompt = img_data["prompt"]
                                    # Switch to Etsy tab
                                    st.experimental_set_query_params(active_tab="etsy")
                                    st.experimental_rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

