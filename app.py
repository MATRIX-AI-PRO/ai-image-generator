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

# Sayfa yapılandırması
st.set_page_config(page_title="AI Görsel Oluşturma Aracı", layout="wide")

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

# OpenAI API istemcisini başlat
client = OpenAI(api_key=st.secrets["openai_api_key"])

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
    """Yapay zeka ile prompt oluşturma"""
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

def generate_cartoon_prompt(style, description):
    """Çizgi film stili için prompt oluşturma"""
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

def download_image(image_url):
    """Görsel indirme fonksiyonu"""
    try:
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

# YENİ: ChatGPT ile görsel dönüştürme fonksiyonu
def transform_image_with_openai(image_url, style):
    """ChatGPT ve DALL-E kullanarak görseli dönüştürme"""
    try:
        # Görüntüyü base64'e dönüştür
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        
        # Görüntü boyutunu kontrol et ve gerekirse yeniden boyutlandır
        max_size = (1024, 1024)
        if image.width > max_size[0] or image.height > max_size[1]:
            image.thumbnail(max_size, Image.LANCZOS)
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # GPT-4V ile görüntüyü analiz edip DALL-E için prompt oluştur
        prompt = f"""Analyze this image and create a detailed prompt to transform it into {style} style.
        Maintain the exact same subject, composition, and scene - only change the visual style.
        If there's a person or animal in the image, keep the same person/animal with same pose and expression.
        Describe the image in detail including what you see, and specify how it should be transformed to {style} style.
        Your prompt must ensure the AI keeps the same subject and doesn't change it to something else."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # DALL-E için prompt oluştur
        dalle_prompt = response.choices[0].message.content
        
        # DALL-E ile görüntü dönüştür
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt + f" Make sure to maintain the exact same subject and composition as the original image, just transform it to {style} style.",
            n=1,
            size="1024x1024",
            quality="standard"
        )
        
        transformed_image_url = dalle_response.data[0].url
        return transformed_image_url
        
    except Exception as e:
        st.session_state.notification = f"Dönüştürme hatası: {str(e)}"
        st.session_state.notification_type = "error"
        return None

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
    "Çizgi Film Dönüştürme", 
    "Etsy Metadata", 
    "Görsel Geçmişi"
])

# 1. Gerçekçi Görsel Oluşturma Sekmesi
with tab1:
    st.markdown('<div class="section-title"><h3>Gerçekçi Görsel Oluşturma</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Kategori seçimi
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
        selected_category = st.selectbox("Kategori Seçin", category_options, key="category")
        
        # Fikir seçimi
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
        selected_idea = st.selectbox("Fikir Seçin", idea_options[selected_category], key="idea")
        
        # Etnik köken/görünüm seçimi
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
        selected_ethnicity = st.selectbox("Görünüm/Etnik Köken", ethnicity_options, key="ethnicity")
        
        # Görsel stil seçimi
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
        selected_style = st.selectbox("Görsel Stil", style_options, key="style")
        
        # Ek detaylar
        additional_details = st.text_area(
            "Ek Detaylar (İsteğe Bağlı)", 
            placeholder="Örn: kızıl saç, mavi gözler, plaj arka planı...",
            key="additional_details"
        )
    
    with col2:
        # Görsel boyutu
        size_options = ["1024x1024", "1024x1792", "1792x1024"]
        selected_size = st.selectbox("Görsel Boyutu", size_options, key="size")
        
        # Görsel kalitesi
        quality_options = ["Standard", "HD"]
        quality_mapping = {"Standard": "standard", "HD": "hd"}
        selected_quality_display = st.selectbox("Görsel Kalitesi", quality_options, key="quality")
        selected_quality = quality_mapping[selected_quality_display]

        # Görsel sayısı
        num_images = st.slider("Oluşturulacak Görsel Sayısı", 1, 4, 1, key="num_images")
        
        # İpuçları
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
    
    # Prompt oluşturma butonu
    if st.button("Prompt Oluştur", key="gen_prompt_btn"):
        with st.spinner("Prompt oluşturuluyor..."):
            try:
                # Prompt oluştur
                realistic_prompt = generate_ai_prompt(
                    selected_category, 
                    selected_idea, 
                    selected_ethnicity, 
                    selected_style, 
                    additional_details
                )
                
                # Session state'e kaydet
                st.session_state.realistic_prompt = realistic_prompt
                
                # Prompt göster
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Oluşturulan Prompt:")
                st.text_area("", realistic_prompt, height=150, key="prompt_display", disabled=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.session_state.notification = "Prompt başarıyla oluşturuldu"
                st.session_state.notification_type = "success"
                
            except Exception as e:
                st.session_state.notification = f"Prompt oluşturma hatası: {e}"
                st.session_state.notification_type = "error"
    
    # Görsel oluşturma butonu
    if st.button("Görsel Oluştur", key="gen_img_btn", disabled=not st.session_state.realistic_prompt):
        # İlerleme çubuğu için yer tutucu
        progress_placeholder = st.empty()
        
        try:
            images = []
            for i in range(num_images):
                # İlerlemeyi güncelle
                progress_placeholder.progress((i) / num_images, text=f"Görsel {i+1}/{num_images} oluşturuluyor...")
                
                # Görsel oluştur
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=st.session_state.realistic_prompt + " Make sure this is a photorealistic image, not a cartoon or illustration. Use photographic style with realistic lighting and textures.",
                    n=1,  # DALL-E 3 sadece n=1 destekliyor
                    size=selected_size,
                    quality=selected_quality
                )
                
                for data in response.data:
                    image_url = data.url
                    images.append(image_url)
                    # Geçmişe ekle
                    st.session_state.image_history.append({
                        "url": image_url,
                        "type": "Realistic",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # İlerleme çubuğunu temizle
            progress_placeholder.empty()
            
            # Session state'e kaydet
            st.session_state.realistic_images = images
            
            # Görselleri göster
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown("#### Oluşturulan Gerçekçi Görseller:")
            
            # Modern galeri içinde görselleri göster
            st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
            for i, image_url in enumerate(st.session_state.realistic_images):
                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                st.image(image_url, use_column_width=True, caption=f"Gerçekçi Görsel #{i+1}")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Çizgi filme dönüştürme butonu
                    if st.button(f"Çizgi Filme Dönüştür #{i+1}", key=f"convert_{i}"):
                        set_image_to_convert(image_url)
                
                with col2:
                    # Etsy için kullanma butonu
                    if st.button(f"Etsy İçin Kullan #{i+1}", key=f"etsy_{i}"):
                        set_image_for_etsy(image_url)
                
                # İndirme butonu
                image_data = download_image(image_url)
                if image_data:
                    st.download_button(
                        label="Görseli İndir",
                        data=image_data,
                        file_name=f"realistic_image_{i+1}.png",
                        mime="image/png",
                        key=f"download_{i}"
                    )
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.session_state.notification = f"{num_images} gerçekçi görsel başarıyla oluşturuldu"
            st.session_state.notification_type = "success"
            
        except Exception as e:
            st.session_state.notification = f"Görsel oluşturma hatası: {e}"
            st.session_state.notification_type = "error"
            st.error("Lütfen farklı bir prompt deneyin veya API anahtarınızı kontrol edin.")

# 2. Çizgi Film Dönüştürme Sekmesi
with tab2:
    st.markdown('<div class="section-title"><h3>Çizgi Film Stiline Dönüştürme</h3></div>', unsafe_allow_html=True)
    
    # Dönüştürülecek görsel var mı kontrol et
    if st.session_state.selected_image_to_convert:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Dönüştürülecek Gerçekçi Görsel")
            st.image(st.session_state.selected_image_to_convert, use_column_width=True)
        
        with col2:
            st.markdown("#### Çizgi Film Stili Seçimi")
            
            # Çizgi film stili seçimi
            cartoon_style_options = [
                "Pixar 3D",
                "Disney 2D Animation",
                "DreamWorks",
                "Anime",
                "South Park",
                "The Simpsons",
                "Studio Ghibli",
                "Comic Book",
                "Watercolor Illustration",
                "Claymation",
                "Cartoon Network",
                "Chibi Style",
                "Retro Cartoon",
                "Minimalist Animation",
                "Caricature"
            ]
            selected_style = st.selectbox("Çizgi Film Stili", cartoon_style_options, key="cartoon_style")
            
            # Özelleştirme seçenekleri
            customization = st.text_area(
                "Özelleştirme (İsteğe Bağlı)", 
                placeholder="Örn: parlak renkler, daha çocuksu, daha detaylı...",
                key="cartoon_customization"
            )
            
            # Dönüşüm kalitesi
            quality_options = ["Standard", "HD"]
            quality_mapping = {"Standard": "standard", "HD": "hd"}
            selected_quality_display = st.selectbox("Dönüşüm Kalitesi", quality_options, key="cartoon_quality")
            selected_quality = quality_mapping[selected_quality_display]
            
            # Dönüşüm yöntemi seçimi
            conversion_method = st.radio(
                "Dönüşüm Yöntemi",
                ["Standart (Prompt Tabanlı)", "Gelişmiş (ChatGPT Analizi)"],
                key="conversion_method"
            )
            
            # Stil önizleme
            st.markdown("#### Seçilen Stil Örneği")
            style_examples = {
                "Pixar 3D": "https://i.imgur.com/8JLGtLF.jpg",
                "Disney 2D Animation": "https://i.imgur.com/2D9fRpD.jpg",
                "DreamWorks": "https://i.imgur.com/LGPxVHC.jpg",
                "Anime": "https://i.imgur.com/qsf4MZL.jpg",
                "South Park": "https://i.imgur.com/8ETtSP3.jpg",
                "The Simpsons": "https://i.imgur.com/5BF1EoH.jpg",
                "Studio Ghibli": "https://i.imgur.com/NJJBqDz.jpg",
                "Comic Book": "https://i.imgur.com/XzZ9Nbz.jpg",
                "Watercolor Illustration": "https://i.imgur.com/JM9cMiZ.jpg",
                "Claymation": "https://i.imgur.com/7R1VgQz.jpg",
                "Cartoon Network": "https://i.imgur.com/2Uj3T0Y.jpg",
                "Chibi Style": "https://i.imgur.com/9kJbB5F.jpg",
                "Retro Cartoon": "https://i.imgur.com/KzQDVQs.jpg",
                "Minimalist Animation": "https://i.imgur.com/4YgvfTH.jpg",
                "Caricature": "https://i.imgur.com/XWG0SYm.jpg"
            }
            # Eğer örnek görsel varsa göster, yoksa placeholder göster
            if selected_style in style_examples:
                st.image(style_examples[selected_style], width=200, caption=f"{selected_style} Stil Örneği")
            else:
                st.image("https://placehold.co/200x200?text=Örnek+Yok", width=200, caption="Örnek Yok")
            
            # Dönüştür butonu
            if st.button("Çizgi Filme Dönüştür", key="convert_btn"):
                with st.spinner(f"{selected_style} stiline dönüştürülüyor..."):
                    try:
                        # Dönüşüm yöntemine göre işlem yap
                        if conversion_method == "Standart (Prompt Tabanlı)":
                            # Çizgi film promptu oluştur
                            cartoon_prompt = generate_cartoon_prompt(
                                selected_style,
                                customization
                            )
                            
                            # Promptu kaydet
                            st.session_state.cartoon_prompt = cartoon_prompt
                            
                            # Promptu göster
                            with st.expander("Oluşturulan Dönüşüm Promptu"):
                                st.text_area("", cartoon_prompt, height=100, key="cartoon_prompt_display", disabled=True)
                            
                            # DALL-E ile görseli dönüştür
                            response = client.images.generate(
                                model="dall-e-3",
                                prompt=cartoon_prompt + f" Based on this realistic image. Make it a high-quality {selected_style} style cartoon.",
                                n=1,
                                size="1024x1024",
                                quality=selected_quality
                            )
                            
                            cartoon_image_url = response.data[0].url
                        else:
                            # Gelişmiş dönüşüm (ChatGPT analizi ile)
                            cartoon_image_url = transform_image_with_openai(
                                st.session_state.selected_image_to_convert,
                                selected_style + (f", {customization}" if customization else "")
                            )
                        
                        # Çizgi film görsellerine ve geçmişe ekle
                        st.session_state.cartoon_images.append(cartoon_image_url)
                        st.session_state.image_history.append({
                            "url": cartoon_image_url,
                            "type": f"Cartoon ({selected_style})",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        # Sonucu göster
                        st.markdown("#### Dönüştürülen Çizgi Film Görseli:")
                        st.image(cartoon_image_url, use_column_width=True)
                        
                        # Çizgi film görseli için butonlar
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Etsy İçin Kullan", key="use_for_etsy_cartoon"):
                                set_image_for_etsy(cartoon_image_url)
                        with col2:
                            image_data = download_image(cartoon_image_url)
                            if image_data:
                                st.download_button(
                                    label="Görseli İndir",
                                    data=image_data,
                                    file_name=f"cartoon_{selected_style.lower().replace(' ', '_')}.png",
                                    mime="image/png",
                                    key="download_cartoon"
                                )
                        
                        # Karşılaştırma göster
                        st.markdown("#### Karşılaştırma:")
                        comparison_col1, comparison_col2 = st.columns(2)
                        with comparison_col1:
                            st.markdown("**Öncesi (Gerçekçi)**")
                            st.image(st.session_state.selected_image_to_convert, use_column_width=True)
                        with comparison_col2:
                            st.markdown(f"**Sonrası ({selected_style})**")
                            st.image(cartoon_image_url, use_column_width=True)
                        
                        # Stil analizi
                        with st.expander("Stil Analizi"):
                            st.markdown("#### Stil Özellikleri")
                            style_analysis = {
                                "Pixar 3D": "3 boyutlu modelleme, yumuşak yüzeyler, gerçekçi doku, abartılı yüz ifadeleri",
                                "Disney 2D Animation": "Akıcı animasyon, yumuşak hatlar, canlı renkler, ifadeli gözler",
                                "DreamWorks": "Detaylı 3D modelleme, daha karikatürize yüzler, dinamik hareketler",
                                "Anime": "Büyük gözler, stilize saçlar, minimal yüz detayları, düz renkler",
                                "South Park": "Basit şekiller, kağıt kesim görünümü, sınırlı animasyon, canlı renkler",
                                "The Simpsons": "Sarı ten, büyük gözler, dört parmak, belirgin kontur çizgileri",
                                "Studio Ghibli": "Detaylı arka planlar, yumuşak renkler, doğa vurgusu, akıcı animasyon",
                                "Comic Book": "Kalın konturlar, noktalı gölgelendirme, canlı renkler, konuşma balonları",
                                "Watercolor Illustration": "Sulu boya efekti, yumuşak geçişler, sanatsal fırça darbeleri",
                                "Claymation": "Kil görünümü, dokulu yüzeyler, stop-motion etkisi",
                                "Cartoon Network": "Geometrik şekiller, kalın konturlar, düz renkler, dinamik pozlar",
                                "Chibi Style": "Küçük vücut, büyük kafa, minimalist özellikler, sevimli ifadeler",
                                "Retro Cartoon": "Vintage görünüm, sınırlı renk paleti, nostaljik stil",
                                "Minimalist Animation": "Basit şekiller, sınırlı detaylar, düz renkler, şık tasarım",
                                "Caricature": "Abartılı özellikler, mizahi yaklaşım, tanınabilir yüzler"
                            }
                            
                            if selected_style in style_analysis:
                                st.markdown(f"**{selected_style} Stili Özellikleri:**")
                                for özellik in style_analysis[selected_style].split(", "):
                                    st.markdown(f"- {özellik}")
                            else:
                                st.info("Bu stil için detaylı analiz bulunmuyor.")
                        
                        st.session_state.notification = f"Görsel başarıyla {selected_style} stiline dönüştürüldü"
                        st.session_state.notification_type = "success"
                        
                    except Exception as e:
                        st.session_state.notification = f"Dönüştürme hatası: {str(e)}"
                        st.session_state.notification_type = "error"
                        st.error("Lütfen başka bir stil deneyin veya API anahtarınızı kontrol edin.")
    else:
        # Dönüştürülecek görsel seçilmemişse
        st.info("Lütfen önce 'Gerçekçi Görsel Oluşturma' sekmesinden bir görsel oluşturun ve 'Çizgi Filme Dönüştür' butonuna tıklayın.")
        
        # Örnek görseller
        st.markdown("### Örnek Dönüşümler")
        st.markdown("Aşağıda bazı örnek dönüşümleri görebilirsiniz:")
        
        example_col1, example_col2, example_col3 = st.columns(3)
        with example_col1:
            st.image("https://i.imgur.com/JKy7JbN.jpg", caption="Gerçekçi Portre")
        with example_col2:
            st.image("https://i.imgur.com/8ETtSP3.jpg", caption="South Park Stili")
        with example_col3:
            st.image("https://i.imgur.com/NJJBqDz.jpg", caption="Studio Ghibli Stili")
        
        # Stil karşılaştırma
        st.markdown("### Stil Karşılaştırma Tablosu")
        st.markdown("""
        | Stil | Özellikler | En İyi Kullanım |
        | ---- | ---------- | --------------- |
        | Pixar 3D | 3D modelleme, gerçekçi doku | Aile filmleri, duygusal hikayeler |
        | Disney 2D | Akıcı animasyon, canlı renkler | Masallar, klasik hikayeler |
        | Anime | Büyük gözler, stilize saçlar | Japon tarzı, aksiyon, fantezi |
        | Comic Book | Kalın konturlar, canlı renkler | Süper kahraman, aksiyon |
        | Watercolor | Sulu boya efekti, yumuşak geçişler | Sanatsal, duygusal, nostaljik |
        """)
        
        # Stil seçimi ipuçları
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Stil Seçimi İpuçları</h4>
            <ul>
                <li>Çocuklar için: Pixar 3D, Disney 2D veya Cartoon Network</li>
                <li>Genç yetişkinler için: Anime, Comic Book veya The Simpsons</li>
                <li>Sanatsal görünüm için: Studio Ghibli veya Watercolor Illustration</li>
                <li>Mizahi yaklaşım için: South Park, Caricature veya The Simpsons</li>
                <li>Nostaljik hava için: Retro Cartoon veya Claymation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# 3. Etsy Metadata Sekmesi
with tab3:
    st.markdown('<div class="section-title"><h3>Etsy Metadata Oluşturma</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.selected_image_for_etsy:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Seçilen Görsel")
            st.image(st.session_state.selected_image_for_etsy, use_column_width=True)
            
            # Görsel analizi
            with st.expander("Görsel Analizi"):
                st.markdown("Görselin otomatik analizi yapılıyor...")
                try:
                    # Görüntüyü base64'e dönüştür
                    response = requests.get(st.session_state.selected_image_for_etsy)
                    image = Image.open(BytesIO(response.content))
                    
                    # Görüntü boyutunu kontrol et ve gerekirse yeniden boyutlandır
                    max_size = (512, 512)  # Analiz için küçük boyut yeterli
                    if image.width > max_size[0] or image.height > max_size[1]:
                        image.thumbnail(max_size, Image.LANCZOS)
                    
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # GPT-4V ile görüntüyü analiz et
                    analysis_prompt = "Describe this image in detail, focusing on: 1) Main subject 2) Style 3) Colors 4) Mood/atmosphere 5) Potential uses as a digital product. Keep it concise."
                    
                    analysis_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": analysis_prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{img_str}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=300
                    )
                    
                    analysis_text = analysis_response.choices[0].message.content
                    st.markdown(analysis_text)
                    
                    # Renk paleti analizi
                    st.markdown("#### Renk Paleti")
                    # Görüntüdeki baskın renkleri bul
                    image = image.convert('RGB')
                    image = image.resize((50, 50))  # Performans için küçült
                    pixels = list(image.getdata())
                    
                    # Renkleri grupla ve en yaygın 5 rengi bul
                    color_counts = {}
                    for pixel in pixels:
                        # Benzer renkleri grupla (hassasiyeti azalt)
                        grouped_pixel = (pixel[0]//20*20, pixel[1]//20*20, pixel[2]//20*20)
                        if grouped_pixel in color_counts:
                            color_counts[grouped_pixel] += 1
                        else:
                            color_counts[grouped_pixel] = 1
                    
                    # En yaygın 5 rengi al
                    dominant_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    # Renk paletini göster
                    color_cols = st.columns(5)
                    for i, (color, count) in enumerate(dominant_colors):
                        hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                        with color_cols[i]:
                            st.markdown(
                                f"""
                                <div style="background-color: {hex_color}; 
                                            height: 50px; 
                                            border-radius: 5px; 
                                            margin-bottom: 5px;">
                                </div>
                                <p style="text-align: center; font-size: 12px;">{hex_color}</p>
                                """, 
                                unsafe_allow_html=True
                            )
                except Exception as e:
                    st.error(f"Görsel analizi sırasında bir hata oluştu: {str(e)}")
        
        with col2:
            st.markdown("#### Etsy Ürün Bilgileri")
            
            # Ürün tipi
            product_type = st.selectbox(
                "Ürün Tipi",
                [
                    "Digital Download",
                    "Physical Print",
                    "Custom Portrait",
                    "Wall Art",
                    "Phone Case Design",
                    "T-shirt Design",
                    "Mug Design",
                    "Canvas Print",
                    "Poster",
                    "Printable Art",
                    "SVG Cut File",
                    "Digital Planner",
                    "Digital Stickers",
                    "Logo Template",
                    "Social Media Template"
                ],
                key="product_type"
            )
            
            # Ürün başlığı
            product_title = st.text_input("Ürün Başlığı", key="product_title")
            
            # Ürün açıklaması
            product_description = st.text_area("Ürün Açıklaması", height=150, key="product_description")
            
            # Etiketler
            product_tags = st.text_input(
                "Etiketler (virgülle ayırın)",
                placeholder="örn: dijital sanat, portre, hediye, özel tasarım",
                key="product_tags"
            )
            
            # Fiyat
            product_price = st.number_input("Fiyat ($)", min_value=0.99, value=9.99, step=1.0, key="product_price")
            
            # Hedef kitle
            target_audience = st.multiselect(
                "Hedef Kitle",
                [
                    "Çocuklar",
                    "Gençler",
                    "Yetişkinler",
                    "Aileler",
                    "Çiftler",
                    "Öğrenciler",
                    "Profesyoneller",
                    "Sanat Severler",
                    "Koleksiyoncular",
                    "Hediye Arayanlar"
                ],
                key="target_audience"
            )
            
            # Metadata oluştur butonu
            if st.button("Etsy Metadata Oluştur", key="gen_metadata_btn"):
                with st.spinner("Etsy için metadata oluşturuluyor..."):
                    try:
                        # Görsel analizi için ChatGPT kullanımı
                        response = requests.get(st.session_state.selected_image_for_etsy)
                        image = Image.open(BytesIO(response.content))
                        
                        # Görüntü boyutunu kontrol et ve gerekirse yeniden boyutlandır
                        max_size = (1024, 1024)
                        if image.width > max_size[0] or image.height > max_size[1]:
                            image.thumbnail(max_size, Image.LANCZOS)
                        
                        buffered = BytesIO()
                        image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Hedef kitle bilgisini hazırla
                        audience_info = ", ".join(target_audience) if target_audience else "Genel"
                        
                        # GPT-4V ile görüntüyü analiz et
                        prompt = f"""Analyze this image and help create Etsy metadata for it. The product type is: {product_type}.
                        Target audience: {audience_info}
                        
                        1. Suggest a catchy product title (max 80 characters)
                        2. Write a detailed product description (200-300 words) that highlights features and benefits
                        3. Suggest 10-13 relevant tags for Etsy search optimization
                        4. Recommend a fair price range for this type of product
                        5. Identify key features of the image that should be highlighted in marketing
                        6. Suggest 3 upselling ideas for this product
                        
                        Format your response as JSON with these keys: title, description, tags (array), price_range, key_features (array), upselling_ideas (array)"""
                        
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{img_str}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            response_format={"type": "json_object"},
                            max_tokens=800
                        )
                        
                        # JSON yanıtını parse et
                        metadata = json.loads(response.choices[0].message.content)
                        
                        # Sonuçları göster
                        st.markdown('<div class="result-container">', unsafe_allow_html=True)
                        st.markdown("### Etsy Metadata Sonuçları")
                        
                        st.markdown("#### Önerilen Başlık:")
                        st.text_input("", metadata["title"], key="suggested_title")
                        
                        st.markdown("#### Önerilen Açıklama:")
                        st.text_area("", metadata["description"], height=200, key="suggested_description")
                        
                        st.markdown("#### Önerilen Etiketler:")
                        tags_str = ", ".join(metadata["tags"])
                        st.text_area("", tags_str, height=80, key="suggested_tags")
                        
                        st.markdown("#### Önerilen Fiyat Aralığı:")
                        st.info(metadata["price_range"])
                        
                        st.markdown("#### Öne Çıkan Özellikler:")
                        for feature in metadata["key_features"]:
                            st.markdown(f"- {feature}")
                        
                        st.markdown("#### Ek Satış Fırsatları:")
                        for idea in metadata["upselling_ideas"]:
                            st.markdown(f"- {idea}")
                        
                        # SEO analizi
                        with st.expander("SEO Analizi"):
                            st.markdown("#### Etsy SEO İpuçları")
                            st.markdown("""
                            1. **Başlık Optimizasyonu:** Başlığınızda ana anahtar kelimeleri kullanın
                            2. **Etiket Kullanımı:** Tüm 13 etiketi kullanın ve çeşitli arama terimlerini kapsayın
                            3. **Uzun-Kuyruk Anahtar Kelimeler:** Daha spesifik arama terimleri ekleyin
                            4. **Kategori Seçimi:** Doğru kategoriyi seçtiğinizden emin olun
                            5. **Açıklama İçeriği:** Açıklamada anahtar kelimeleri doğal bir şekilde kullanın
                            """)
                            
                            # Anahtar kelime analizi
                            st.markdown("#### Anahtar Kelime Analizi")
                            keywords = []
                            # Başlıktan anahtar kelimeleri çıkar
                            title_words = metadata["title"].lower().replace(",", "").replace(".", "").split()
                            # Etiketlerden anahtar kelimeleri çıkar
                            tag_words = []
                            for tag in metadata["tags"]:
                                tag_words.extend(tag.lower().replace(",", "").replace(".", "").split())
                            
                            # Tüm anahtar kelimeleri birleştir ve tekrar edenleri say
                            all_keywords = title_words + tag_words
                            keyword_counts = {}
                            for word in all_keywords:
                                if len(word) > 3:  # Sadece anlamlı kelimeleri al
                                    if word in keyword_counts:
                                        keyword_counts[word] += 1
                                    else:
                                        keyword_counts[word] = 1
                            
                            # En çok tekrar eden 10 anahtar kelimeyi göster
                            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                            
                            keyword_cols = st.columns(5)
                            for i, (keyword, count) in enumerate(top_keywords):
                                col_idx = i % 5
                                with keyword_cols[col_idx]:
                                    st.markdown(
                                        f"""
                                        <div style="background-color: rgba(255, 75, 75, {count/max(dict(top_keywords).values())}); 
                                                    padding: 10px; 
                                                    border-radius: 5px; 
                                                    margin-bottom: 10px;
                                                    text-align: center;">
                                            <p style="margin: 0; font-weight: bold;">{keyword}</p>
                                            <p style="margin: 0; font-size: 12px;">({count})</p>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                        # JSON indirme butonu
                        json_str = json.dumps(metadata, indent=2)
                        st.download_button(
                            label="Metadata JSON İndir",
                            data=json_str,
                            file_name="etsy_metadata.json",
                            mime="application/json",
                            key="download_metadata"
                        )
                        
                        # HTML şablonu oluştur
                        html_template = f"""
                        <!DOCTYPE html>
                        <html lang="tr">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{metadata["title"]}</title>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    max-width: 800px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                h1 {{
                                    color: #d85a5a;
                                }}
                                .product-description {{
                                    margin: 20px 0;
                                }}
                                .features {{
                                    background-color: #f9f9f9;
                                    padding: 15px;
                                    border-radius: 5px;
                                }}
                                .tags {{
                                    display: flex;
                                    flex-wrap: wrap;
                                    margin: 20px 0;
                                }}
                                .tag {{
                                    background-color: #eee;
                                    padding: 5px 10px;
                                    margin: 5px;
                                    border-radius: 3px;
                                    font-size: 14px;
                                }}
                                .price {{
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: #d85a5a;
                                }}
                                .upsell {{
                                    margin-top: 30px;
                                    padding-top: 20px;
                                    border-top: 1px solid #eee;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>{metadata["title"]}</h1>
                            
                            <div class="price">
                                {metadata["price_range"]}
                            </div>
                            
                            <div class="product-description">
                                {metadata["description"].replace("\n", "<br>")}
                            </div>
                            
                            <div class="features">
                                <h3>Öne Çıkan Özellikler</h3>
                                <ul>
                                    {"".join(f"<li>{feature}</li>" for feature in metadata["key_features"])}
                                </ul>
                            </div>
                            
                            <div class="tags">
                                <h3>Etiketler:</h3>
                                {"".join(f'<span class="tag">{tag}</span>' for tag in metadata["tags"])}
                            </div>
                            
                            <div class="upsell">
                                <h3>Ayrıca Bakabilirsiniz:</h3>
                                <ul>
                                    {"".join(f"<li>{idea}</li>" for idea in metadata["upselling_ideas"])}
                                </ul>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # HTML şablonunu indir
                        st.download_button(
                            label="HTML Şablonu İndir",
                            data=html_template,
                            file_name="etsy_listing.html",
                            mime="text/html",
                            key="download_html"
                        )
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.session_state.notification = "Etsy metadata başarıyla oluşturuldu"
                        st.session_state.notification_type = "success"
                        
                    except Exception as e:
                        st.session_state.notification = f"Metadata oluşturma hatası: {str(e)}"
                        st.session_state.notification_type = "error"
                        st.error("Lütfen tekrar deneyin veya API anahtarınızı kontrol edin.")
    else:
        # Etsy için görsel seçilmemişse
        st.info("Lütfen önce bir görsel oluşturun ve 'Etsy İçin Kullan' butonuna tıklayın.")
        
        # Etsy satış ipuçları
        st.markdown("### Etsy Satış İpuçları")
        st.markdown("""
        <div class="tips-box">
            <h4>💡 Etsy'de Başarılı Olma İpuçları</h4>
            <ul>
                <li><strong>SEO Optimizasyonu:</strong> Başlık ve etiketlerde anahtar kelimeler kullanın</li>
                <li><strong>Kaliteli Görseller:</strong> Yüksek çözünürlüklü, net ve çekici görseller kullanın</li>
                <li><strong>Detaylı Açıklamalar:</strong> Ürününüzün tüm özelliklerini ve faydalarını belirtin</li>
                <li><strong>Doğru Fiyatlandırma:</strong> Pazar araştırması yaparak rekabetçi fiyatlar belirleyin</li>
                <li><strong>Müşteri Hizmetleri:</strong> Hızlı yanıt verin ve müşteri memnuniyetine önem verin</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Örnek Etsy listeleme
        st.markdown("### Örnek Etsy Listeleme")
        example_col1, example_col2 = st.columns([1, 2])
        with example_col1:
            st.image("https://i.imgur.com/JM9cMiZ.jpg", caption="Örnek Dijital İndirme")
        with example_col2:
            st.markdown("""
            #### Sulu Boya Aile Portresi, Kişiselleştirilmiş Dijital İndirme
            
            **$12.99**
            
            Bu güzel sulu boya aile portresi, özel anılarınızı sanatsal bir şekilde ölümsüzleştirmek için mükemmel bir seçimdir. Fotoğrafınızdan oluşturulan bu dijital sanat eseri, evinizin duvarlarında harika görünecek.
            
            **Özellikler:**
            - Yüksek çözünürlüklü dijital dosya (300 DPI)
            - Çeşitli boyut seçenekleri (8x10, 11x14, 16x20 inç)
            - Sınırsız indirme hakkı
            - Kişiselleştirilebilir renk seçenekleri
            - 24 saat içinde teslim
            
            **Etiketler:** aile portresi, sulu boya sanat, kişiselleştirilmiş hediye, duvar sanatı, dijital indirme, özel portre, ev dekorasyonu, doğum günü hediyesi, yıldönümü hediyesi
            """)

# 4. Görsel Geçmişi Sekmesi
with tab4:
    st.markdown('<div class="section-title"><h3>Görsel Geçmişi</h3></div>', unsafe_allow_html=True)
    
    # Geçmiş görselleri göster
    if st.session_state.image_history:
        # Filtreleme seçenekleri
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_type = st.selectbox(
                "Görsel Tipi Filtrele",
                ["Tümü", "Realistic", "Cartoon"],
                key="filter_type"
            )
        with filter_col2:
            sort_order = st.selectbox(
                "Sıralama",
                ["En Yeni", "En Eski"],
                key="sort_order"
            )
        
        # Filtreleme ve sıralama uygula
        filtered_history = st.session_state.image_history
        if filter_type != "Tümü":
            filtered_history = [img for img in filtered_history if filter_type in img["type"]]
        
        # Sıralama uygula
        if sort_order == "En Yeni":
            filtered_history = sorted(filtered_history, key=lambda x: x["timestamp"], reverse=True)
        else:
            filtered_history = sorted(filtered_history, key=lambda x: x["timestamp"])
        
        # Geçmiş görselleri göster
        st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
        for i, image_data in enumerate(filtered_history):
            st.markdown('<div class="image-card">', unsafe_allow_html=True)
            st.image(image_data["url"], use_column_width=True, caption=f"{image_data['type']} - {image_data['timestamp']}")
            
            col1, col2 = st.columns(2)
            with col1:
                # Çizgi filme dönüştürme butonu (sadece gerçekçi görseller için)
                if "Realistic" in image_data["type"]:
                    if st.button(f"Çizgi Filme Dönüştür", key=f"hist_convert_{i}"):
                        set_image_to_convert(image_data["url"])
            
            with col2:
                # Etsy için kullanma butonu
                if st.button(f"Etsy İçin Kullan", key=f"hist_etsy_{i}"):
                    set_image_for_etsy(image_data["url"])
            
            # İndirme butonu
            image_bytes = download_image(image_data["url"])
            if image_bytes:
                st.download_button(
                    label="Görseli İndir",
                    data=image_bytes,
                    file_name=f"image_{image_data['type'].lower().replace(' ', '_')}_{i}.png",
                    mime="image/png",
                    key=f"hist_download_{i}"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Geçmişi temizleme butonu
        if st.button("Geçmişi Temizle", key="clear_history"):
            st.session_state.image_history = []
            st.session_state.notification = "Görsel geçmişi temizlendi"
            st.session_state.notification_type = "info"
            st.rerun()
    else:
        st.info("Henüz oluşturulmuş görsel bulunmuyor. Lütfen önce bir görsel oluşturun.")

# Alt bilgi
st.markdown("""
<div class="footer">
    <p>© 2025 AI Görsel Oluşturma ve Dönüştürme Aracı</p>
    <p>Bu uygulama OpenAI API kullanarak yapay zeka destekli görsel oluşturma ve dönüştürme hizmeti sunar.</p>
</div>
""", unsafe_allow_html=True)
