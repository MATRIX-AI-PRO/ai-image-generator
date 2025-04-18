import streamlit as st
import json
import base64
import os
import io
from PIL import Image
import random
from datetime import datetime
import requests
from io import BytesIO
import time
from openai import OpenAI

# Google Cloud için gerekli kütüphaneler
from google.cloud import aiplatform
from google.oauth2 import service_account
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image as VertexImage

# Sayfa yapılandırması
st.set_page_config(page_title="AI Image Studio", layout="wide")

# OpenAI API anahtarını ayarla
try:
    # ESKİ KOD: openai.api_key = st.secrets["openai"]["openai_api_key"]
    # YENİ KOD:
    client = OpenAI(api_key=st.secrets["openai"]["openai_api_key"])
except Exception as e:
    st.error(f"OpenAI API anahtarı bulunamadı: {str(e)}")

# Google Cloud kimlik doğrulama ve başlatma
def initialize_google_cloud():
    """Google Cloud kimlik doğrulama ve başlatma"""
    try:
        # Google Cloud kimlik bilgilerini Streamlit secrets'tan al
        project_id = st.secrets["google_cloud"]["project_id"]
        location = st.secrets["google_cloud"]["location"]
        
        # Servis hesabı kimlik bilgilerini kullan
        credentials_info = st.secrets["google_credentials"]
        
        # Kimlik bilgilerini oluştur
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Vertex AI'yi başlat
        aiplatform.init(
            project=project_id,
            location=location,
            credentials=credentials
        )
        
        # Vertex AI'yi başlat (generative models için)
        vertexai.init(
            project=project_id,
            location=location,
            credentials=credentials
        )
        
        return True
    except Exception as e:
        st.error(f"Google Cloud başlatma hatası: {str(e)}")
        return False

# Google Cloud'u başlat
try:
    initialize_google_cloud()
except Exception as e:
    st.error(f"Google Cloud başlatma hatası: {str(e)}")

# Session state değişkenlerini başlat
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
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
if 'selected_image_to_convert' not in st.session_state:
    st.session_state.selected_image_to_convert = None
if 'selected_image_for_etsy' not in st.session_state:
    st.session_state.selected_image_for_etsy = None
if 'notification' not in st.session_state:
    st.session_state.notification = None
if 'notification_type' not in st.session_state:
    st.session_state.notification_type = None
if 'selected_style' not in st.session_state:
    st.session_state.selected_style = None

# CSS stilleri
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
    .section-title {
        background-color: #2a2a2a;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        border-left: 4px solid #ff4b4b;
        font-weight: bold;
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
    .tips-box {
        background-color: #2a2a2a;
        border-left: 4px solid #ff4b4b;
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
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
    .footer {
        margin-top: 50px;
        text-align: center;
        padding: 20px;
        background-color: #1a1a1a;
        border-radius: 10px;
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
    .style-card {
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .style-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(255, 75, 75, 0.3);
    }
    .style-card.selected {
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.5);
    }
    .style-card img {
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .comparison-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
        gap: 20px;
    }
    .comparison-arrow {
        font-size: 24px;
        color: #ff4b4b;
    }
    .feature-list {
        background-color: #2a2a2a;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
    .feature-item {
        padding: 8px 0;
        border-bottom: 1px solid #3a3a3a;
    }
    .feature-item:last-child {
        border-bottom: none;
    }
</style>
""", unsafe_allow_html=True)

# Başlık ve açıklama
st.markdown("""
<div class="header">
    <h1>AI Görsel Oluşturma ve Dönüştürme Aracı</h1>
</div>
""", unsafe_allow_html=True)

# Bildirim göster
if st.session_state.notification:
    if st.session_state.notification_type == "success":
        st.success(st.session_state.notification)
    elif st.session_state.notification_type == "error":
        st.error(st.session_state.notification)
    elif st.session_state.notification_type == "info":
        st.info(st.session_state.notification)
    elif st.session_state.notification_type == "warning":
        st.warning(st.session_state.notification)
    
    # Bildirimi temizle
    st.session_state.notification = None
    st.session_state.notification_type = None

# Fonksiyonlar
def generate_ai_prompt(category, idea, ethnicity, style, additional_details):
    """ChatGPT API veya Google Cloud ile prompt oluşturma"""
    try:
        system_prompt = """
        You are a professional photographer and visual artist.
        You need to write a prompt for image generation to create realistic, high-quality images.
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
        
        # Önce OpenAI ile dene
        try:
            # ChatGPT API çağrısı
            response = client.chat.completions.create(
                model="gpt-4", # veya "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # Yanıtı al
            ai_prompt = response.choices[0].message.content.strip()
            return ai_prompt
            
        except Exception as e:
            # OpenAI başarısız olursa Google Cloud'a yönlendir
            st.warning("OpenAI API hatası nedeniyle Google Cloud kullanılıyor...")
            
            # Gemini Pro modelini kullan
            model = GenerativeModel("gemini-pro")
            
            # API çağrısı
            full_prompt = system_prompt + "\n\n" + user_prompt
            response = model.generate_content(
                full_prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": 300}
            )
            
            return response.text
        
    except Exception as e:
        raise Exception(f"AI prompt oluşturma hatası: {str(e)}")

def generate_image_with_imagen(prompt, size="1024x1024", num_images=1):
    """Google Imagen ile görsel oluşturma"""
    try:
        # Google Cloud kimlik bilgilerini al
        project_id = st.secrets["google_cloud"]["project_id"]
        location = st.secrets["google_cloud"]["location"]
        
        # Boyut ayarlarını yap
        if size == "1024x1024":
            aspect_ratio = "1:1"
        elif size == "1024x1792":
            aspect_ratio = "9:16"
        else:  # 1792x1024
            aspect_ratio = "16:9"
        
        # Imagen model endpoint'i
        endpoint = aiplatform.Endpoint(
            endpoint_name=f"projects/{project_id}/locations/{location}/publishers/google/models/imagegeneration@002"
        )
        
        # Imagen API çağrısı
        instances = [{
            "prompt": prompt,
            "sampleCount": num_images,
            "aspectRatio": aspect_ratio,
            "seed": random.randint(0, 2147483647)
        }]
        
        response = endpoint.predict(instances=instances)
        
        # Yanıttan görsel URL'lerini çıkar
        image_urls = []
        for i in range(num_images):
            # Base64 kodlu görüntüyü al
            image_data = response.predictions[i]["bytesBase64Encoded"]
            image_url = f"data:image/png;base64,{image_data}"
            image_urls.append(image_url)
        
        return image_urls
        
    except Exception as e:
        st.error(f"Imagen API hatası: {str(e)}")
        # Hata durumunda alternatif olarak OpenAI DALL-E kullanmayı deneyebilirsiniz
        try:
            st.warning("Google Imagen API hatası nedeniyle OpenAI DALL-E kullanılıyor...")
            return generate_image_with_dalle(prompt, size, num_images)
        except:
            raise Exception(f"Imagen görsel oluşturma hatası: {str(e)}")

def generate_image_with_dalle(prompt, size="1024x1024", num_images=1):
    """OpenAI DALL-E ile görsel oluşturma (yedek olarak)"""
    try:
        images = []
        for i in range(num_images):
            # DALL-E API çağrısı
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            # URL'den görseli indir ve base64'e çevir
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Base64 formatında URL oluştur
            base64_url = f"data:image/png;base64,{img_str}"
            images.append(base64_url)
            
        return images
    except Exception as e:
        raise Exception(f"DALL-E görsel oluşturma hatası: {str(e)}")

def download_image(image_url):
    """Görsel indirme fonksiyonu"""
    try:
        if image_url.startswith('data:image'):
            # Base64 formatındaki görseli çöz
            image_data = image_url.split(",", 1)[1]
            image_bytes = base64.b64decode(image_data)
            return image_bytes
        else:
            # URL'den görseli indir
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            buf = BytesIO()
            image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            return byte_im
    except Exception as e:
        st.session_state.notification = f"Görsel indirme hatası: {e}"
        st.session_state.notification_type = "error"
        return None

def set_image_to_convert(image_url):
    """Dönüştürülecek görseli ayarla"""
    st.session_state.selected_image_to_convert = image_url
    st.session_state.active_tab = 1  # Çizgi Film Dönüştürme sekmesine geç
    st.session_state.notification = "Görsel dönüştürme için seçildi"
    st.session_state.notification_type = "info"
    # Sayfayı yeniden yükleme işlemi
    try:
        st.rerun()  # Yeni Streamlit sürümlerinde
    except:
        try:
            st.experimental_rerun()  # Eski Streamlit sürümlerinde
        except:
            # Her iki yöntem de çalışmazsa kullanıcıya manuel talimat ver
            st.success("Görsel dönüştürme için seçildi. Lütfen 'Çizgi Film Dönüştürme' sekmesine geçin.")

def set_image_for_etsy(image_url):
    """Etsy için görseli ayarla"""
    st.session_state.selected_image_for_etsy = image_url
    st.session_state.active_tab = 2  # Etsy Metadata sekmesine geç
    st.session_state.notification = "Görsel Etsy için seçildi"
    st.session_state.notification_type = "info"
    # Sayfayı yeniden yükleme işlemi
    try:
        st.rerun()  # Yeni Streamlit sürümlerinde
    except:
        try:
            st.experimental_rerun()  # Eski Streamlit sürümlerinde
        except:
            # Her iki yöntem de çalışmazsa kullanıcıya manuel talimat ver
            st.success("Görsel Etsy için seçildi. Lütfen 'Etsy Metadata' sekmesine geçin.")

def direct_style_transfer(image_url, style_name):
    """Google Imagen ile görsel stil transferi"""
    try:
        # Google Cloud kimlik bilgilerini al
        project_id = st.secrets["google_cloud"]["project_id"]
        location = st.secrets["google_cloud"]["location"]
        
        # Görüntüyü yükle ve base64'e dönüştür
        if image_url.startswith('data:image'):
            # Zaten base64 formatında
            base64_image = image_url.split(",", 1)[1]
        else:
            # URL'den görüntüyü yükle
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Stil açıklamaları
        style_descriptions = {
            "Pixar 3D": "a Pixar 3D animation style with characteristic large eyes, stylized features, and high-quality 3D rendering",
            "Disney 2D Animation": "a Disney 2D animation style with fluid lines, expressive eyes, and vibrant colors",
            "DreamWorks": "a DreamWorks animation style with exaggerated expressions and detailed texturing",
            "Anime": "an anime style with large eyes, colorful hair, and simplified facial features",
            "South Park": "a South Park style with simple shapes, flat colors, and characteristic animation",
            "The Simpsons": "a Simpsons style with yellow skin, overbite, and the distinctive Simpsons look",
            "Studio Ghibli": "a Studio Ghibli style with soft colors, detailed backgrounds, and whimsical character design"
        }
        
        # Seçilen stil açıklaması
        style_desc = style_descriptions.get(style_name, "a cartoon style")
        
        # Stil transferi için prompt oluştur
        prompt = f"Transform this image into {style_name} style. {style_desc}. Maintain the same pose, expression, and key features."
        
        # Gemini Pro Vision modelini kullan
        try:
            # Görseli yükle
            image_part = VertexImage.from_bytes(base64.b64decode(base64_image))
            
            # Modeli başlat
            model = GenerativeModel("gemini-pro-vision")
            
            # Prompt oluştur
            vision_prompt = f"""
            Analyze this image and create a detailed prompt to transform it into {style_name} style.
            The image shows a person with specific features, expressions, and pose.
            Create a detailed prompt that will maintain the person's identity, expression, pose, and key features,
            but adapt the visual style to {style_desc}.
            Focus on describing the person's facial features, expression, pose, clothing, and any distinctive elements.
            """
            
            # API çağrısı
            response = model.generate_content(
                [image_part, vision_prompt],
                generation_config={"temperature": 0.7, "max_output_tokens": 500}
            )
            
            detailed_prompt = response.text
            
            # Imagen endpoint'i
            imagen_endpoint = aiplatform.Endpoint(
                endpoint_name=f"projects/{project_id}/locations/{location}/publishers/google/models/imagegeneration@002"
            )
            
            # Final prompt
            final_prompt = f"{detailed_prompt} The result should look exactly like the person in the original image but in {style_name} style. Maintain the same pose, expression, and key features."
            
            # Imagen API çağrısı
            response = imagen_endpoint.predict(
                instances=[
                    {
                        "prompt": final_prompt,
                        "sampleCount": 1,
                        "aspectRatio": "1:1",
                        "seed": random.randint(0, 2147483647)
                    }
                ]
            )
            
            # Base64 kodlu görüntüyü al
            image_data = response.predictions[0]["bytesBase64Encoded"]
            transformed_image_url = f"data:image/png;base64,{image_data}"
            
            return transformed_image_url
            
        except Exception as e:
            # Gemini Pro Vision başarısız olursa doğrudan Imagen kullan
            st.warning("Gemini Pro Vision API hatası nedeniyle doğrudan Imagen kullanılıyor...")
            
            # Imagen endpoint'i
            imagen_endpoint = aiplatform.Endpoint(
                endpoint_name=f"projects/{project_id}/locations/{location}/publishers/google/models/imagegeneration@002"
            )
            
            # Basit prompt
            simple_prompt = f"Transform this image into {style_name} style. {style_desc}. Maintain the same pose, expression, and key features."
            
            # Imagen API çağrısı
            response = imagen_endpoint.predict(
                instances=[
                    {
                        "prompt": simple_prompt,
                        "sampleCount": 1,
                        "aspectRatio": "1:1",
                        "seed": random.randint(0, 2147483647)
                    }
                ]
            )
            
            # Base64 kodlu görüntüyü al
            image_data = response.predictions[0]["bytesBase64Encoded"]
            transformed_image_url = f"data:image/png;base64,{image_data}"
            
            return transformed_image_url
        
    except Exception as e:
        # Hata durumunda OpenAI'ye yönlendir
        try:
            st.warning("Google Cloud API hatası nedeniyle OpenAI DALL-E kullanılıyor...")
            
            # Görüntüyü base64'ten çıkar
            if image_url.startswith('data:image'):
                image_data = image_url.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
            else:
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
            
            # Görüntüyü geçici olarak kaydet
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                image.save(temp_file.name)
                temp_file_path = temp_file.name
            
            # DALL-E API çağrısı
            with open(temp_file_path, "rb") as image_file:
                response = client.images.edit(
                    model="dall-e-2",
                    image=image_file,
                    prompt=f"Transform this image into {style_name} style. {style_desc}. Maintain the same pose, expression, and key features.",
                    n=1,
                    size="1024x1024"
                )
            
            # Geçici dosyayı sil
            os.unlink(temp_file_path)
            
            # URL'den görseli indir ve base64'e çevir
            image_url = response.data[0].url
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Base64 formatında URL oluştur
            transformed_image_url = f"data:image/png;base64,{img_str}"
            
            return transformed_image_url
            
        except Exception as backup_error:
            st.error(f"Stil transferi sırasında bir hata oluştu: {str(e)}, Yedek hata: {str(backup_error)}")
            return None

def generate_etsy_description(image_url, product_title, product_type, product_price):
    """Etsy ürün açıklaması oluşturma"""
    try:
        # Google Cloud kimlik bilgilerini al
        project_id = st.secrets["google_cloud"]["project_id"]
        location = st.secrets["google_cloud"]["location"]
        
        # Görüntüyü base64'e dönüştür
        if image_url.startswith('data:image'):
            # Zaten base64 formatında
            base64_image = image_url.split(",", 1)[1]
        else:
            # URL'den görüntüyü yükle
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Gemini Pro Vision modelini kullan
        try:
            # Görseli yükle
            image_part = VertexImage.from_bytes(base64.b64decode(base64_image))
            
            # Modeli başlat
            model = GenerativeModel("gemini-pro-vision")
            
            # Create prompt
            prompt = f"""
            Create an Etsy product description for this image:
            
            Product Title: {product_title}
            Product Type: {product_type}
            Price: ${product_price}
            
            Include sections for:
            1. Product details
            2. What customer will receive
            3. Why they should buy it
            
            Make it SEO friendly and engaging. Use bullet points where appropriate.
            """
            
            # API call
            response = model.generate_content(
                [image_part, prompt],
                generation_config={"temperature": 0.7, "max_output_tokens": 1000}
            )
            
            return response.text
            
        except Exception as e:
            # If Gemini Pro Vision fails, redirect to OpenAI
            st.warning("Google Cloud API error, using OpenAI instead...")
            
            # OpenAI API call
            response = client.chat.completions.create(
                model="gpt-4", # or "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a professional e-commerce copywriter specializing in Etsy listings."},
                    {"role": "user", "content": f"""
                    Create an Etsy product description for this product:
                    
                    Product Title: {product_title}
                    Product Type: {product_type}
                    Price: ${product_price}
                    
                    Include sections for:
                    1. Product details
                    2. What customer will receive
                    3. Why they should buy it
                    
                    Make it SEO friendly and engaging. Use bullet points where appropriate.
                    """}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
    except Exception as e:
        raise Exception(f"Error generating Etsy description: {str(e)}")

def generate_etsy_tags(product_title, product_type):
    """Generate Etsy SEO tags"""
    try:
        # Get Google Cloud credentials
        project_id = st.secrets["google_cloud"]["project_id"]
        
        # Use Gemini Pro model
        model = GenerativeModel("gemini-pro")
        
        # Create prompt
        prompt = f"""
        Create 13 effective Etsy SEO tags for this product:
        
        Product Title: {product_title}
        Product Type: {product_type}
        
        Make sure the tags are within Etsy's character limits (20 characters per tag) and highly searchable.
        Format the output as a list with each tag on a new line, preceded by a bullet point.
        """
        
        # API call
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.5, "max_output_tokens": 300}
        )
        
        return response.text
        
    except Exception as e:
        # In case of error, redirect to OpenAI
        try:
            st.warning("Google Cloud API error, using OpenAI instead...")
            
            # OpenAI API call
            response = client.chat.completions.create(
                model="gpt-4", # or "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are an SEO expert specializing in Etsy marketplace."},
                    {"role": "user", "content": f"""
                    Create 13 effective Etsy SEO tags for this product:
                    
                    Product Title: {product_title}
                    Product Type: {product_type}
                    
                    Make sure the tags are within Etsy's character limits (20 characters per tag) and highly searchable.
                    Format the output as a list with each tag on a new line, preceded by a bullet point.
                    """}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as backup_error:
            raise Exception(f"Error generating Etsy tags: {str(e)}, Backup error: {str(backup_error)}")

def save_to_history(image_url, prompt, image_type="realistic"):
    """Save to image history"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.image_history.append({
        "image_url": image_url,
        "prompt": prompt,
        "timestamp": timestamp,
        "type": image_type
    })

# Create tabs
tabs = st.tabs(["Realistic Image Generation", "Cartoon Conversion", "Etsy Metadata", "Image History"])

# Tab content
with tabs[0]:
    st.session_state.active_tab = 0
    
    st.markdown('<div class="section-title">Realistic Image Generation</div>', unsafe_allow_html=True)
    
    # Tips
    with st.expander("📝 Tips and Suggestions"):
        st.markdown("""
        <div class="tips-box">
            <h4>Tips for Better Results:</h4>
            <ul>
                <li>Clearly specify the image category and idea</li>
                <li>Choose appearance and style options that match your image idea</li>
                <li>Add special requests like lighting, composition, color scheme in the additional details</li>
                <li>You can edit the AI-generated prompt for more specific results</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Create form
    with st.form("realistic_image_form"):
        # Category selection
        category = st.selectbox(
            "Image Category",
            ["Portrait", "Landscape", "Product", "Fashion", "Food", "Animal", "Sports", "Architecture", "Abstract", "Other"]
        )
        
        # Image idea
        idea = st.text_input("Image Idea", placeholder="E.g., A person watching sunset at the beach")
        
        # Appearance selection
        ethnicity = st.selectbox(
            "Appearance (For images containing humans)",
            ["Not specified", "Diverse", "Caucasian", "Asian", "African", "Hispanic", "Middle Eastern", "Mixed"]
        )
        
        # Style selection
        style = st.selectbox(
            "Image Style",
            ["Realistic", "Studio Photography", "Street Photography", "Fashion Photography", 
             "Documentary", "Minimalist", "Vintage", "Film", "HDR", "Dramatic Lighting"]
        )
        
        # Additional details
        additional_details = st.text_area(
            "Additional Details (Optional)",
            placeholder="E.g., Natural light, warm tones, blurred background"
        )
        
        # Image size selection
        size_options = {
            "Square (1024x1024)": "1024x1024",
            "Portrait (1024x1792)": "1024x1792",
            "Landscape (1792x1024)": "1792x1024"
        }
        size = st.selectbox("Image Size", list(size_options.keys()))
        
        # Number of images
        num_images = st.slider("Number of Images", 1, 4, 1)
        
        # Submit button
        submitted = st.form_submit_button("Generate Images")
    
    # Handle form submission
    if submitted:
        if not idea:
            st.error("Please enter an image idea.")
        else:
            with st.spinner("Generating AI prompt..."):
                try:
                    # Generate AI prompt
                    ai_prompt = generate_ai_prompt(category, idea, ethnicity, style, additional_details)
                    
                    # Display generated prompt
                    st.markdown('<div class="section-title">Generated AI Prompt</div>', unsafe_allow_html=True)
                    
                    # Allow editing the prompt
                    edited_prompt = st.text_area("Edit Prompt if needed:", value=ai_prompt, height=150)
                    
                    # Generate images
                    with st.spinner("Generating images... This may take a moment."):
                        # Use Google Imagen API
                        selected_size = size_options[size]
                        image_urls = generate_image_with_imagen(edited_prompt, selected_size, num_images)
                        
                        # Save to session state
                        st.session_state.realistic_images = image_urls
                        st.session_state.realistic_prompt = edited_prompt
                        
                        # Save to history
                        for img_url in image_urls:
                            save_to_history(img_url, edited_prompt, "realistic")
                    
                    # Display results
                    st.markdown('<div class="section-title">Generated Images</div>', unsafe_allow_html=True)
                    
                    # Create image gallery
                    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                    
                    cols = st.columns(min(4, num_images))
                    for i, img_url in enumerate(image_urls):
                        with cols[i % len(cols)]:
                            st.markdown(f"""
                            <div class="image-card">
                                <img src="{img_url}" style="width:100%;" />
                                <div style="margin-top:10px;">
                                    <a href="#" onclick="return false;" id="convert-btn-{i}">Convert to Cartoon</a> | 
                                    <a href="#" onclick="return false;" id="etsy-btn-{i}">Etsy Metadata</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add buttons with functionality
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"Convert to Cartoon {i+1}", key=f"convert_btn_{i}"):
                                    set_image_to_convert(img_url)
                            with col2:
                                if st.button(f"Etsy Metadata {i+1}", key=f"etsy_btn_{i}"):
                                    set_image_for_etsy(img_url)
                            
                            # Download button
                            img_bytes = download_image(img_url)
                            st.download_button(
                                label=f"Download Image {i+1}",
                                data=img_bytes,
                                file_name=f"ai_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png",
                                mime="image/png",
                                key=f"download_btn_{i}"
                            )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tabs[1]:
    st.session_state.active_tab = 1
    
    st.markdown('<div class="section-title">Cartoon Style Conversion</div>', unsafe_allow_html=True)
    
    # Tips
    with st.expander("📝 Tips for Cartoon Conversion"):
        st.markdown("""
        <div class="tips-box">
            <h4>Tips for Better Cartoon Conversions:</h4>
            <ul>
                <li>Use high-quality source images with good lighting</li>
                <li>Choose a cartoon style that matches the mood of your image</li>
                <li>Images with clear subjects and simple backgrounds work best</li>
                <li>For character conversions, images with visible faces work better</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Image upload section
    st.markdown("### Upload an Image or Use Generated Image")
    
    # Check if an image is selected for conversion
    if st.session_state.selected_image_to_convert:
        st.markdown("#### Selected Image:")
        st.image(st.session_state.selected_image_to_convert, width=300)
    
    # Upload option
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width=300)
        
        # Convert to base64 for API
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        image_url = f"data:image/png;base64,{img_str}"
        
        # Update selected image
        st.session_state.selected_image_to_convert = image_url
    
    # Style selection
    st.markdown("### Select Cartoon Style")
    
    # Define styles with sample images
    styles = {
        "Pixar 3D": "https://i.imgur.com/example_pixar.jpg",
        "Disney 2D Animation": "https://i.imgur.com/example_disney.jpg",
        "DreamWorks": "https://i.imgur.com/example_dreamworks.jpg",
        "Anime": "https://i.imgur.com/example_anime.jpg",
        "South Park": "https://i.imgur.com/example_southpark.jpg",
        "The Simpsons": "https://i.imgur.com/example_simpsons.jpg",
        "Studio Ghibli": "https://i.imgur.com/example_ghibli.jpg"
    }
    
    # Create style grid
    style_cols = st.columns(3)
    for i, (style_name, style_img) in enumerate(styles.items()):
        with style_cols[i % 3]:
            # Check if this style is selected
            is_selected = st.session_state.selected_style == style_name
            
            # Style card with selection state
            st.markdown(f"""
            <div class="style-card {'selected' if is_selected else ''}">
                <p>{style_name}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Selection button
            if st.button(f"Select {style_name}", key=f"style_{i}"):
                st.session_state.selected_style = style_name
                st.rerun()
    
    # Convert button
    if st.session_state.selected_image_to_convert and st.session_state.selected_style:
        if st.button("Convert to Cartoon", key="convert_final"):
            with st.spinner(f"Converting image to {st.session_state.selected_style} style..."):
                try:
                    # Perform style transfer
                    cartoon_image = direct_style_transfer(
                        st.session_state.selected_image_to_convert,
                        st.session_state.selected_style
                    )
                    
                    # Display comparison
                    st.markdown("### Before and After")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(st.session_state.selected_image_to_convert, caption="Original Image", width=300)
                    with col2:
                        st.image(cartoon_image, caption=f"{st.session_state.selected_style} Style", width=300)
                    
                    # Save to history
                    save_to_history(cartoon_image, f"Converted to {st.session_state.selected_style} style", "cartoon")
                    
                    # Download button
                    img_bytes = download_image(cartoon_image)
                    st.download_button(
                        label="Download Cartoon Image",
                        data=img_bytes,
                        file_name=f"cartoon_{st.session_state.selected_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )
                    
                    # Option to use for Etsy
                    if st.button("Use for Etsy Metadata"):
                        set_image_for_etsy(cartoon_image)
                    
                except Exception as e:
                    st.error(f"Error during conversion: {str(e)}")
    else:
        st.warning("Please select both an image and a cartoon style to continue.")

with tabs[2]:
    st.session_state.active_tab = 2
    
    st.markdown('<div class="section-title">Etsy Product Metadata Generator</div>', unsafe_allow_html=True)
    
    # Tips
    with st.expander("📝 Etsy Selling Tips"):
        st.markdown("""
        <div class="tips-box">
            <h4>Tips for Successful Etsy Listings:</h4>
            <ul>
                <li>Use descriptive, keyword-rich titles (max 140 characters)</li>
                <li>Include all 13 tags allowed by Etsy (max 20 characters each)</li>
                <li>Write detailed descriptions with all product information</li>
                <li>Mention materials, dimensions, and usage instructions</li>
                <li>Highlight what makes your product unique</li>
                <li>Include shipping information and processing time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Check if an image is selected for Etsy
    if st.session_state.selected_image_for_etsy:
        st.markdown("### Selected Product Image:")
        st.image(st.session_state.selected_image_for_etsy, width=300)
    else:
        st.info("Please select an image from the Image Generation or Cartoon Conversion tabs first.")
        
        # Upload option
        uploaded_file = st.file_uploader("Or upload a product image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", width=300)
            
            # Convert to base64 for API
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            image_url = f"data:image/png;base64,{img_str}"
            
            # Update selected image
            st.session_state.selected_image_for_etsy = image_url
    
    # Product information form
    if st.session_state.selected_image_for_etsy:
        with st.form("etsy_metadata_form"):
            st.markdown("### Product Information")
            
            # Product details
            product_title = st.text_input("Product Title (Max 140 characters)", 
                                        placeholder="E.g., Custom Digital Portrait, Personalized Cartoon Avatar")
            
            product_type = st.selectbox("Product Type", 
                                        ["Digital Download", "Physical Print", "Print on Demand", 
                                        "Custom Order", "Art Print", "Poster", "T-shirt Design", "Other"])
            
            product_price = st.number_input("Product Price ($)", min_value=0.99, max_value=9999.99, value=19.99, step=1.0)
            
            # Submit button
            submitted = st.form_submit_button("Generate Etsy Metadata")
        
        # Handle form submission
        if submitted:
            if not product_title:
                st.error("Please enter a product title.")
            else:
                with st.spinner("Generating Etsy metadata..."):
                    try:
                        # Generate product description
                        description = generate_etsy_description(
                            st.session_state.selected_image_for_etsy,
                            product_title,
                            product_type,
                            product_price
                        )
                        
                        # Generate SEO tags
                        tags = generate_etsy_tags(product_title, product_type)
                        
                        # Display results
                        st.markdown('<div class="section-title">Etsy Listing Metadata</div>', unsafe_allow_html=True)
                        
                        # Product description
                        st.markdown("### Product Description")
                        st.markdown('<div class="result-container">', unsafe_allow_html=True)
                        st.markdown(description)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # SEO tags
                        st.markdown("### SEO Tags")
                        st.markdown('<div class="result-container">', unsafe_allow_html=True)
                        st.markdown(tags)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Export options
                        st.markdown("### Export Options")
                        
                        # Create text file with all metadata
                        metadata_text = f"""
                        ETSY PRODUCT METADATA
                        ---------------------
                        
                        PRODUCT TITLE:
                        {product_title}
                        
                        PRODUCT TYPE:
                        {product_type}
                        
                        PRICE:
                        ${product_price}
                        
                        DESCRIPTION:
                        {description}
                        
                        SEO TAGS:
                        {tags}
                        
                        Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        """
                        
                        # Download button
                        st.download_button(
                            label="Download Metadata as Text File",
                            data=metadata_text,
                            file_name=f"etsy_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"Error generating Etsy metadata: {str(e)}")

with tabs[3]:
    st.session_state.active_tab = 3
    
    st.markdown('<div class="section-title">Image History</div>', unsafe_allow_html=True)
    
    # Display image history
    if st.session_state.image_history:
        # Sort by timestamp (newest first)
        sorted_history = sorted(st.session_state.image_history, key=lambda x: x["timestamp"], reverse=True)
        
        # Filter options
        st.markdown("### Filter Options")
        filter_type = st.selectbox("Filter by Type", ["All", "Realistic", "Cartoon"])
        
        # Apply filter
        if filter_type != "All":
            filtered_history = [item for item in sorted_history if item["type"].lower() == filter_type.lower()]
        else:
            filtered_history = sorted_history
        
        # Display images in a grid
        st.markdown("### Your Generated Images")
        
        if not filtered_history:
            st.info(f"No {filter_type.lower()} images found in your history.")
        else:
            # Create image gallery
            st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
            
            cols = st.columns(3)
            for i, item in enumerate(filtered_history):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="image-card">
                        <img src="{item['image_url']}" style="width:100%;" />
                        <p><strong>Date:</strong> {item['timestamp']}</p>
                        <p><strong>Type:</strong> {item['type'].capitalize()}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Expand to show prompt
                    with st.expander("Show Prompt"):
                        st.text_area("", value=item["prompt"], height=100, key=f"prompt_{i}", disabled=True)
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Convert to Cartoon", key=f"hist_convert_{i}"):
                            set_image_to_convert(item["image_url"])
                    with col2:
                        if st.button(f"Etsy Metadata", key=f"hist_etsy_{i}"):
                            set_image_for_etsy(item["image_url"])
                    
                    # Download button
                    img_bytes = download_image(item["image_url"])
                    st.download_button(
                        label=f"Download",
                        data=img_bytes,
                        file_name=f"history_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png",
                        mime="image/png",
                        key=f"hist_download_{i}"
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Clear history button
            if st.button("Clear History"):
                st.session_state.image_history = []
                st.rerun()
    else:
        st.info("Your image history is empty. Generate some images to see them here!")

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 AI Image Studio | Powered by Google Cloud and OpenAI</p>
    <p>This application uses AI to generate and transform images.</p>
</div>
""", unsafe_allow_html=True)
