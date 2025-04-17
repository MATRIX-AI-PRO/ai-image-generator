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
if 'selected_style' not in st.session_state:
    st.session_state.selected_style = None

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

# YENİ: Doğrudan görsel stil transferi fonksiyonu
def direct_style_transfer(image_url, style_name):
    """Doğrudan görsel stil transferi yapan fonksiyon"""
    try:
        # Görüntüyü yükle
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        
        # Görüntüyü base64'e dönüştür
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Stil transferi için komut oluştur
        style_prompts = {
            "Pixar 3D": "Transform this photo into a Pixar 3D animated character style. Maintain the exact same pose, expression, and composition, just convert to the Pixar 3D animation style with characteristic large eyes, stylized features, and high-quality 3D rendering. Include a small circular thumbnail of the original photo in the corner.",
            
            "Disney 2D Animation": "Transform this photo into a Disney 2D animated character style. Maintain the exact same pose, expression, and composition, just convert to the Disney 2D animation style with fluid lines, expressive eyes, and vibrant colors. Include a small circular thumbnail of the original photo in the corner.",
            
            "DreamWorks": "Transform this photo into a DreamWorks animation style character. Maintain the exact same pose, expression, and composition, just convert to the DreamWorks style with slightly exaggerated features, detailed textures, and dynamic lighting. Include a small circular thumbnail of the original photo in the corner.",
            
            "Anime": "Transform this photo into an anime style character. Maintain the exact same pose, expression, and composition, just convert to anime style with large eyes, simplified facial features, and stylized hair. Include a small circular thumbnail of the original photo in the corner.",
            
            "South Park": "Transform this photo into a South Park style character. Maintain the exact same pose and composition, just convert to the South Park paper cutout style with simple shapes, flat colors, and characteristic expressions. Include a small circular thumbnail of the original photo in the corner.",
            
            "The Simpsons": "Transform this photo into a Simpsons style character. Maintain the exact same pose and composition, just convert to The Simpsons style with yellow skin tone, overbite, large eyes, and the distinctive outline. Include a small circular thumbnail of the original photo in the corner.",
            
            "Studio Ghibli": "Transform this photo into a Studio Ghibli style character. Maintain the exact same pose, expression, and composition, just convert to the Studio Ghibli style with soft details, natural movements, and pastel color palette. Include a small circular thumbnail of the original photo in the corner."
        }
        
        # Seçilen stile göre komut al
        style_prompt = style_prompts.get(style_name, "Transform this photo into a cartoon character.")
        
        # DALL-E ile doğrudan görsel dönüştürme
        response = client.images.generate(
            model="dall-e-3",
            prompt=style_prompt,
            n=1,
            size="1024x1024",
            quality="hd",
            image=buffered.getvalue()
        )
        
        # Dönüştürülen görselin URL'sini al
        transformed_image_url = response.data[0].url
        return transformed_image_url
        
    except Exception as e:
        st.error(f"Stil transferi sırasında bir hata oluştu: {str(e)}")
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
            
            st.session_state.notification = f"{num_images} görsel başarıyla oluşturuldu"
            st.session_state.notification_type = "success"
            
        except Exception as e:
            st.session_state.notification = f"Görsel oluşturma hatası: {str(e)}"
            st.session_state.notification_type = "error"

# 2. Çizgi Film Dönüştürme Sekm
# Stil seçimi için görsel örnekler
style_examples = {
    "Pixar 3D": "https://i.imgur.com/8JLGtLF.jpg",
    "Disney 2D Animation": "https://i.imgur.com/2D9fRpD.jpg",
    "DreamWorks": "https://i.imgur.com/LGPxVHC.jpg",
    "Anime": "https://i.imgur.com/qsf4MZL.jpg",
    "South Park": "https://i.imgur.com/8ETtSP3.jpg",
    "The Simpsons": "https://i.imgur.com/5BF1EoH.jpg",
    "Studio Ghibli": "https://i.imgur.com/NJJBqDz.jpg"
}

# Dönüştürülecek görsel seçimi
upload_col, preview_col = st.columns([1, 1])

with upload_col:
    st.markdown("### Gerçek Fotoğraf Yükle")
    uploaded_file = st.file_uploader("Fotoğrafınızı yükleyin", type=["jpg", "jpeg", "png"])
    
    # Veya önceden oluşturulan görseli kullan
    if st.session_state.selected_image_to_convert:
        st.markdown("#### Seçilen Görsel")
        st.image(st.session_state.selected_image_to_convert, use_column_width=True)

# Stil seçimi
st.markdown("### Çizgi Film Stili Seçin")

# Stil seçimini görsel olarak göster
style_cols = st.columns(3)
selected_style = None

for i, (style_name, style_img) in enumerate(style_examples.items()):
    with style_cols[i % 3]:
        st.image(style_img, caption=style_name, width=180)
        if st.button(f"Seç: {style_name}", key=f"style_btn_{i}"):
            selected_style = style_name
            st.session_state.selected_style = style_name

# Eğer session state'te seçili stil varsa göster
if 'selected_style' in st.session_state and st.session_state.selected_style:
    st.success(f"Seçilen stil: {st.session_state.selected_style}")
    selected_style = st.session_state.selected_style

# Dönüştürme butonu
if (uploaded_file or st.session_state.selected_image_to_convert) and selected_style:
    if st.button("Çizgi Film Karakterine Dönüştür", key="convert_cartoon_btn", use_container_width=True):
        with st.spinner(f"Fotoğrafınız {selected_style} stiline dönüştürülüyor..."):
            try:
                # Görüntüyü hazırla
                if uploaded_file:
                    # Yüklenen dosyayı kullan
                    image = Image.open(uploaded_file)
                    # Görüntüyü geçici olarak kaydet
                    temp_img = BytesIO()
                    image.save(temp_img, format="PNG")
                    temp_img.seek(0)
                    
                    # Görüntüyü base64'e dönüştür
                    img_str = base64.b64encode(temp_img.getvalue()).decode()
                    image_url = f"data:image/png;base64,{img_str}"
                else:
                    # Seçilen görseli kullan
                    image_url = st.session_state.selected_image_to_convert
                
                # Doğrudan stil transferi yap
                cartoon_image_url = direct_style_transfer(image_url, selected_style)
                
                if cartoon_image_url:
                    # Sonucu göster
                    result_col1, result_col2 = st.columns(2)
                    
                    with result_col1:
                        st.markdown("### Orijinal Fotoğraf")
                        if uploaded_file:
                            st.image(uploaded_file, use_column_width=True)
                        else:
                            st.image(st.session_state.selected_image_to_convert, use_column_width=True)
                    
                    with result_col2:
                        st.markdown(f"### {selected_style} Karakteri")
                        st.image(cartoon_image_url, use_column_width=True)
                    
                    # Görseli geçmişe ve çizgi film görsellerine ekle
                    st.session_state.cartoon_images.append(cartoon_image_url)
                    st.session_state.image_history.append({
                        "url": cartoon_image_url,
                        "type": f"Cartoon ({selected_style})",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # İndirme butonu
                    cartoon_image_data = download_image(cartoon_image_url)
                    if cartoon_image_data:
                        st.download_button(
                            label="Çizgi Film Karakterini İndir",
                            data=cartoon_image_data,
                            file_name=f"cartoon_{selected_style.lower().replace(' ', '_')}.png",
                            mime="image/png",
                            key="download_cartoon_result"
                        )
                    
                    # Başarı mesajı
                    st.success(f"Fotoğrafınız başarıyla {selected_style} stilinde bir karaktere dönüştürüldü!")
                else:
                    st.error("Dönüştürme işlemi sırasında bir hata oluştu. Lütfen tekrar deneyin.")
                
            except Exception as e:
                st.error(f"Dönüştürme sırasında bir hata oluştu: {str(e)}")
                st.error("Lütfen başka bir fotoğraf veya stil deneyin.")
else:
    # Kullanıcıya ne yapması gerektiğini açıkla
    if not (uploaded_file or st.session_state.selected_image_to_convert):
        st.info("Lütfen bir fotoğraf yükleyin veya önceki sekmeden bir görsel seçin.")
    if not selected_style:
        st.info("Lütfen bir çizgi film stili seçin.")

# Örnek dönüşümler
st.markdown("### Örnek Dönüşümler")
st.markdown("Aşağıda bazı örnek dönüşümleri görebilirsiniz:")

example_cols = st.columns(3)

# Örnek görselleri göster (eğer dosyalar mevcutsa)
try:
    with example_cols[0]:
        st.image("https://i.imgur.com/JKwFnGj.jpg", caption="Pixar 3D Stil Örneği", use_column_width=True)
    
    with example_cols[1]:
        st.image("https://i.imgur.com/R5LgkXc.jpg", caption="Disney 2D Stil Örneği", use_column_width=True)
    
    with example_cols[2]:
        st.image("https://i.imgur.com/Pn9Vw7S.jpg", caption="Anime Stil Örneği", use_column_width=True)
except:
    # Dosyalar mevcut değilse örnek görseller için yer tutucular göster
    with example_cols[0]:
        st.markdown("*Pixar 3D Stil Örneği*")
    
    with example_cols[1]:
        st.markdown("*Disney 2D Stil Örneği*")
    
    with example_cols[2]:
        st.markdown("*Anime Stil Örneği*")

# Stil özellikleri
st.markdown("### Stil Özellikleri")

style_features = {
    "Pixar 3D": [
        "Büyük, ifadeli gözler",
        "Yumuşatılmış, hafif stilize yüz hatları",
        "Gerçekçi doku ve aydınlatma",
        "Canlı renkler ve yüksek kontrast",
        "Duygusal ifadelere vurgu"
    ],
    "Disney 2D Animation": [
        "Akıcı çizgiler ve yumuşak kenarlar",
        "Büyük, ifadeli gözler",
        "Stilize vücut oranları",
        "Canlı, doygun renkler",
        "Klasik animasyon estetiği"
    ],
    "DreamWorks": [
        "Daha karikatürize yüz özellikleri",
        "Abartılı ifadeler",
        "Detaylı saç ve kıyafet dokuları",
        "Dinamik poz ve kompozisyonlar",
        "Yumuşak gölgelendirme"
    ],
    "Anime": [
        "Büyük gözler ve küçük burun/ağız",
        "Stilize saç şekilleri ve renkleri",
        "Basitleştirilmiş yüz detayları",
        "Keskin çizgiler",
        "İfadeli duruşlar"
    ],
    "South Park": [
        "Basit, kağıt kesim tarzı",
        "Minimal detay",
        "Düz renkler",
        "Basit geometrik şekiller",
        "Karakteristik yüz ifadeleri"
    ],
    "The Simpsons": [
        "Sarı cilt tonu",
        "Büyük, yuvarlak gözler",
        "Abartılı saç stilleri",
        "Dört parmak",
        "Belirgin dış çizgiler"
    ],
    "Studio Ghibli": [
        "Yumuşak, detaylı arka planlar",
        "Doğal, gerçekçi hareketler",
        "İnce detaylar",
        "Pastel renk paleti",
        "Duygusal yüz ifadeleri"
    ]
}

# Seçilen stil için özellikleri göster
if selected_style and selected_style in style_features:
    st.markdown(f"#### {selected_style} Stil Özellikleri:")
    for feature in style_features[selected_style]:
        st.markdown(f"- {feature}")
# Seçilen görseli göster
if st.session_state.selected_image_for_etsy:
    st.markdown("### Seçilen Görsel")
    st.image(st.session_state.selected_image_for_etsy, width=300)
else:
    st.info("Henüz bir görsel seçilmedi. Lütfen diğer sekmelerden bir görsel oluşturun ve 'Etsy İçin Kullan' butonuna tıklayın.")

# Ürün bilgileri
if st.session_state.selected_image_for_etsy:
    st.markdown("### Ürün Bilgileri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_type = st.selectbox(
            "Ürün Türü", 
            ["Dijital İndirilebilir Portre", "Fiziksel Baskı", "Özel Sipariş Portre", "Dijital Çizgi Film Portresi"]
        )
        
        product_name = st.text_input("Ürün Adı", "Özel Dijital Portre")
        
        product_price = st.number_input("Fiyat ($)", min_value=5.0, max_value=500.0, value=29.99, step=5.0)
        
        delivery_time = st.selectbox(
            "Teslimat Süresi", 
            ["1-2 gün", "3-5 gün", "1 hafta", "2 hafta"]
        )
    
    with col2:
        tags = st.text_area(
            "Etiketler (virgülle ayırın)", 
            "dijital portre, özel portre, ai portre, kişiselleştirilmiş hediye"
        )
        
        description_prompt = st.text_area(
            "Açıklama İçin Prompt", 
            "Bu ürün için SEO dostu bir açıklama oluştur. Ürün bir dijital portre ve müşteriye e-posta ile gönderilecek."
        )

    # Metadata oluşturma butonu
    if st.button("Etsy Metadata Oluştur", key="gen_metadata_btn"):
        with st.spinner("Etsy için metadata oluşturuluyor..."):
            try:
                # Görüntüyü base64'e dönüştür
                response = requests.get(st.session_state.selected_image_for_etsy)
                image = Image.open(BytesIO(response.content))
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # GPT-4V ile görüntüyü analiz et
                prompt = f"""Analyze this image and create Etsy metadata for it.

                Product Type: {product_type}
                Product Name: {product_name}
                Price: ${product_price}
                Delivery Time: {delivery_time}
                Tags: {tags}

                Create the following:
                1. A catchy, SEO-friendly product title (max 140 characters)
                2. 5 bullet points highlighting the product features and benefits
                3. A detailed product description (250-300 words) that is SEO-friendly
                4. 10 additional relevant tags for Etsy search
                5. Suggest 3 upsell opportunities for this product

                Additional context: {description_prompt}
                """
                
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
                    max_tokens=1000
                )
                
                # Metadata'yı al
                metadata = response.choices[0].message.content
                
                # Sonucu göster
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("### Oluşturulan Etsy Metadata")
                st.markdown(metadata)
                
                # Kopyalama butonu
                st.text_area("Metadata (Kopyalamak için)", metadata, height=300)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Başarı mesajı
                st.success("Etsy metadata başarıyla oluşturuldu!")
                
            except Exception as e:
                st.error(f"Metadata oluşturma hatası: {str(e)}")

# Etsy satış ipuçları
st.markdown("### Etsy Satış İpuçları")
st.markdown("""
<div class="tips-box">
    <h4>💡 Etsy'de Daha Fazla Satış İçin İpuçları</h4>
    <ul>
        <li>Ürün başlığında anahtar kelimeleri stratejik olarak kullanın</li>
        <li>Yüksek kaliteli, net görseller kullanın</li>
        <li>Ürün açıklamasında müşterinin alacağı her şeyi detaylı olarak belirtin</li>
        <li>Hızlı teslimat ve müşteri hizmetlerine öncelik verin</li>
        <li>Ürün yorumları için müşterilerinizi teşvik edin</li>
        <li>Sosyal medyada ürünlerinizi tanıtın</li>
    </ul>
</div>
""", unsafe_allow_html=True)
# Geçmiş görselleri göster
if st.session_state.image_history:
    # Filtreleme seçenekleri
    filter_options = ["Tümü", "Gerçekçi", "Çizgi Film"]
    selected_filter = st.selectbox("Görsel Türüne Göre Filtrele", filter_options)
    
    # Sıralama seçenekleri
    sort_options = ["En Yeni", "En Eski"]
    selected_sort = st.selectbox("Sırala", sort_options)
    
    # Görselleri filtrele
    filtered_images = st.session_state.image_history
    if selected_filter == "Gerçekçi":
        filtered_images = [img for img in filtered_images if img["type"] == "Realistic"]
    elif selected_filter == "Çizgi Film":
        filtered_images = [img for img in filtered_images if "Cartoon" in img["type"]]
    
    # Görselleri sırala
    if selected_sort == "En Yeni":
        filtered_images = sorted(filtered_images, key=lambda x: x["timestamp"], reverse=True)
    else:
        filtered_images = sorted(filtered_images, key=lambda x: x["timestamp"])
    
    # Görselleri göster
    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
    for i, image_data in enumerate(filtered_images):
        st.markdown('<div class="image-card">', unsafe_allow_html=True)
        st.image(image_data["url"], use_column_width=True)
        st.markdown(f"**Tür:** {image_data['type']}")
        st.markdown(f"**Tarih:** {image_data['timestamp']}")
        
        col1, col2 = st.columns(2)
        with col1:
            # Çizgi filme dönüştürme butonu (sadece gerçekçi görseller için)
            if image_data["type"] == "Realistic":
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
else:
    st.info("Henüz oluşturulmuş görsel bulunmuyor. Diğer sekmeleri kullanarak görsel oluşturun.")

# Geçmişi temizleme butonu
if st.session_state.image_history and st.button("Görsel Geçmişini Temizle", key="clear_history_btn"):
    st.session_state.image_history = []
    st.session_state.realistic_images = []
    st.session_state.cartoon_images = []
    st.session_state.selected_image_to_convert = None
    st.session_state.selected_image_for_etsy = None
    st.session_state.notification = "Görsel geçmişi temizlendi"
    st.session_state.notification_type = "info"
    st.experimental_rerun()


