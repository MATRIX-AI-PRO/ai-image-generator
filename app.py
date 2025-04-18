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
import openai  # OpenAI kütüphanesini ekliyoruz

# Google Cloud için gerekli kütüphaneler
from google.cloud import aiplatform
from google.oauth2 import service_account
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# Sayfa yapılandırması
st.set_page_config(page_title="AI Görsel Oluşturma Aracı", layout="wide")

# OpenAI API anahtarını ayarla
try:
    openai.api_key = st.secrets["openai"]["api_key"]
except Exception as e:
    st.error(f"OpenAI API anahtarı bulunamadı: {str(e)}")

# Google Cloud kimlik doğrulama ve başlatma
def initialize_google_cloud():
    # Google Cloud kimlik bilgilerini Streamlit secrets'tan al
    credentials_json = st.secrets["google_credentials"]
    
    # JSON string'i bir sözlük nesnesine dönüştür
    credentials_info = json.loads(credentials_json)
    
    # Kimlik bilgilerini oluştur
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    # Vertex AI'yi başlat
    aiplatform.init(
        project=credentials_info["project_id"],
        location="us-central1",  # veya uygun bölge
        credentials=credentials
    )

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
    """ChatGPT API ile prompt oluşturma"""
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
        
        # ChatGPT API çağrısı
        response = openai.ChatCompletion.create(
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
        # Eğer OpenAI API hatası olursa, Google Cloud Vertex AI'ye yönlendir
        try:
            # Google Cloud Vertex AI'nin text-bison modelini kullan
            endpoint = aiplatform.Endpoint(
                endpoint_name="projects/{}/locations/us-central1/publishers/google/models/text-bison".format(
                    st.secrets["google_credentials"]["project_id"]
                )
            )
            
            full_prompt = system_prompt + "\n\n" + user_prompt
            
            response = endpoint.predict(
                instances=[
                    {"content": full_prompt}
                ],
                parameters={
                    "temperature": 0.2,
                    "maxOutputTokens": 300,
                    "topK": 40,
                    "topP": 0.95,
                }
            )
            
            return response.predictions[0]
        except Exception as backup_error:
            raise Exception(f"AI prompt oluşturma hatası: {str(e)}, Yedek hata: {str(backup_error)}")

def generate_image_with_imagen(prompt, size="1024x1024", num_images=1):
    """Google Imagen ile görsel oluşturma"""
    try:
        # Imagen model endpoint'i
        endpoint = aiplatform.Endpoint(
            endpoint_name="projects/{}/locations/us-central1/publishers/google/models/imagegeneration@002".format(
                st.secrets["google_credentials"]["project_id"]
            )
        )
        
        # Boyut ayarlarını yap
        if size == "1024x1024":
            aspect_ratio = "1:1"
        elif size == "1024x1792":
            aspect_ratio = "9:16"
        else:  # 1792x1024
            aspect_ratio = "16:9"
        
        # Imagen API çağrısı
        response = endpoint.predict(
            instances=[
                {
                    "prompt": prompt,
                    "sampleCount": num_images,
                    "aspectRatio": aspect_ratio,
                    "seed": random.randint(0, 2147483647)
                }
            ]
        )
        
        # Yanıttan görsel URL'lerini çıkar
        image_urls = []
        for i in range(num_images):
            # Base64 kodlu görüntüyü al ve geçici bir URL oluştur
            # Not: Gerçek uygulamada bu görselleri bir depolama hizmetine yükleyebilirsiniz
            image_data = response.predictions[i]["bytesBase64Encoded"]
            image_url = f"data:image/png;base64,{image_data}"
            image_urls.append(image_url)
        
        return image_urls
        
    except Exception as e:
        raise Exception(f"Imagen görsel oluşturma hatası: {str(e)}")

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
        
        # Önce ChatGPT API ile dene
        try:
            # Stil transferi için prompt oluştur
            prompt_request = f"""
            Analyze an image and create a detailed prompt to transform it into {style_name} style.
            The image shows a person with specific features, expressions, and pose.
            Create a detailed prompt that will maintain the person's identity, expression, pose, and key features,
            but adapt the visual style to {style_desc}.
            Focus on describing the person's facial features, expression, pose, clothing, and any distinctive elements.
            """
            
            # ChatGPT API çağrısı
            prompt_response = openai.ChatCompletion.create(
                model="gpt-4", # veya "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a professional artist specializing in style transfer."},
                    {"role": "user", "content": prompt_request}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            detailed_prompt = prompt_response.choices[0].message.content.strip()
            
        except Exception as e:
            # ChatGPT başarısız olursa Google Cloud'a yönlendir
            text_endpoint = aiplatform.Endpoint(
                endpoint_name="projects/{}/locations/us-central1/publishers/google/models/text-bison".format(
                    st.secrets["google_credentials"]["project_id"]
                )
            )
            
            prompt_response = text_endpoint.predict(
                instances=[
                    {"content": prompt_request}
                ],
                parameters={
                    "temperature": 0.2,
                    "maxOutputTokens": 500,
                    "topK": 40,
                    "topP": 0.95,
                }
            )
            
            detailed_prompt = prompt_response.predictions[0]
        
        # Imagen ile görsel oluştur
        final_prompt = f"{detailed_prompt} The result should look exactly like the person in the original image but in {style_name} style. Maintain the same pose, expression, and key features."
        
        # Imagen endpoint'i
        imagen_endpoint = aiplatform.Endpoint(
            endpoint_name="projects/{}/locations/us-central1/publishers/google/models/imagegeneration@002".format(
                st.secrets["google_credentials"]["project_id"]
            )
        )
        
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
        st.error(f"Stil transferi sırasında bir hata oluştu: {str(e)}")
        return None

def generate_etsy_description(image_url, product_title, product_type, product_price):
    """Etsy ürün açıklaması oluşturma"""
    try:
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
        
        # Önce Google Cloud Vertex AI'nin multimodal-bison modelini kullan
        try:
            endpoint = aiplatform.Endpoint(
                endpoint_name="projects/{}/locations/us-central1/publishers/google/models/multimodalembedding@001".format(
                    st.secrets["google_credentials"]["project_id"]
                )
            )
            
            # Görsel analizi yap
            image_analysis_response = endpoint.predict(
                instances=[
                    {
                        "image": {"bytesBase64Encoded": base64_image}
                    }
                ]
            )
            
            # Görsel analiz sonuçlarını al
            image_description = image_analysis_response.predictions[0]["imageEmbedding"]["description"]
        except Exception as e:
            # Görsel analizi başarısız olursa basit bir açıklama kullan
            image_description = "A digital or physical product with artistic elements"
        
        # Önce ChatGPT API ile dene
        try:
            description_prompt = f"""
            Create an Etsy product description for this image:
            
            Image Description: {image_description}
            Product Title: {product_title}
            Product Type: {product_type}
            Price: ${product_price}
            
            Include sections for:
            1. Product details
            2. What customer will receive
            3. Why they should buy it
            
            Make it SEO friendly and engaging. Use bullet points where appropriate.
            """
            
            # ChatGPT API çağrısı
            description_response = openai.ChatCompletion.create(
                model="gpt-4", # veya "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a professional e-commerce copywriter specializing in Etsy listings."},
                    {"role": "user", "content": description_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return description_response.choices[0].message.content.strip()
            
        except Exception as e:
            # ChatGPT başarısız olursa Google Cloud'a yönlendir
            text_endpoint = aiplatform.Endpoint(
                endpoint_name="projects/{}/locations/us-central1/publishers/google/models/text-bison".format(
                    st.secrets["google_credentials"]["project_id"]
                )
            )
            
            description_response = text_endpoint.predict(
                instances=[
                    {"content": description_prompt}
                ],
                parameters={
                    "temperature": 0.7,
                    "maxOutputTokens": 1000,
                    "topK": 40,
                    "topP": 0.95,
                }
            )
            
            return description_response.predictions[0]
        
    except Exception as e:
        raise Exception(f"Etsy açıklaması oluşturma hatası: {str(e)}")

def generate_etsy_tags(product_title, product_type):
    """Etsy SEO etiketleri oluşturma"""
    try:
        # Önce ChatGPT API ile dene
        try:
            tags_prompt = f"""
            Create 13 effective Etsy SEO tags for this product:
            
            Product Title: {product_title}
            Product Type: {product_type}
            
            Make sure the tags are within Etsy's character limits (20 characters per tag) and highly searchable.
            Format the output as a list with each tag on a new line, preceded by a bullet point.
            """
            
            # ChatGPT API çağrısı
            tags_response = openai.ChatCompletion.create(
                model="gpt-4", # veya "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are an SEO expert specializing in Etsy marketplace."},
                    {"role": "user", "content": tags_prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return tags_response.choices[0].message.content.strip()
            
        except Exception as e:
            # ChatGPT başarısız olursa Google Cloud'a yönlendir
            endpoint = aiplatform.Endpoint(
                endpoint_name="projects/{}/locations/us-central1/publishers/google/models/text-bison".format(
                    st.secrets["google_credentials"]["project_id"]
                )
            )
            
            tags_response = endpoint.predict(
                instances=[
                    {"content": tags_prompt}
                ],
                parameters={
                    "temperature": 0.5,
                    "maxOutputTokens": 300,
                    "topK": 40,
                    "topP": 0.95,
                }
            )
            
            return tags_response.predictions[0]
        
    except Exception as e:
        raise Exception(f"Etsy etiketleri oluşturma hatası: {str(e)}")

# Aktif sekmeyi ayarla
if st.session_state.active_tab == 0:
    default_tab = "Gerçekçi Görsel Oluşturma"
elif st.session_state.active_tab == 1:
    default_tab = "Çizgi Film Dönüştürme"
elif st.session_state.active_tab == 2:
    default_tab = "Etsy Metadata"
else:
    default_tab = "Görsel Geçmişi"

# Sekmeler
tab1, tab2, tab3, tab4 = st.tabs([
    "Gerçekçi Görsel Oluşturma", 
    "Çizgi Film Dönüştür
