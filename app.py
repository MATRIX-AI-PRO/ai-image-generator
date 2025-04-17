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
@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
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

def set_image_for_etsy(image_url):
    """Etsy için görseli ayarla"""
    st.session_state.selected_image_for_etsy = image_url
    st.session_state.active_tab = 2  # Etsy Metadata sekmesine geç
    st.session_state.notification = "Görsel Etsy için seçildi"
    st.session_state.notification_type = "info"

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
                "Claymation"
            ]
            
            selected_style = st.selectbox("Çizgi Film Stili", cartoon_style_options, key="cartoon_style")
            
            # Ek özelleştirme
            customization = st.text_area(
                "Ek stil detayları (İsteğe bağlı)",
                placeholder="Örn: canlı renkler, abartılı yüz ifadeleri...",
                key="cartoon_customization"
            )
            
            # Dönüşüm kalitesi
            quality_options = ["Standard", "HD"]
            quality_mapping = {"Standard": "standard", "HD": "hd"}
            selected_quality_display = st.selectbox("Dönüşüm Kalitesi", quality_options, key="cartoon_quality")
            selected_quality = quality_mapping[selected_quality_display]
            
            # Dönüştür butonu
            if st.button("Çizgi Filme Dönüştür", key="convert_btn"):
                with st.spinner(f"{selected_style} stiline dönüştürülüyor..."):
                    try:
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
                         st.markdown("#### Karşılaştırma:")
                        comparison_col1, comparison_col2 = st.columns(2)
                        with comparison_col1:
                            st.markdown("**Öncesi (Gerçekçi)**")
                            st.image(st.session_state.selected_image_to_convert, use_column_width=True)
                        with comparison_col2:
                            st.markdown(f"**Sonrası ({selected_style})**")
                            st.image(cartoon_image_url, use_column_width=True)
                        
                        st.session_state.notification = f"Görsel başarıyla {selected_style} stiline dönüştürüldü"
                        st.session_state.notification_type = "success"
                        
                    except Exception as e:
                        st.session_state.notification = f"Dönüştürme hatası: {str(e)}"
                        st.session_state.notification_type = "error"
                        st.error("Lütfen başka bir stil deneyin veya API anahtarınızı kontrol edin.")
    else:
        # Dönüştürülecek görsel seçilmemiş
        st.info("Lütfen önce 'Gerçekçi Görsel Oluşturma' sekmesinden bir görsel oluşturun ve 'Çizgi Filme Dönüştür' butonuna tıklayın.")
        
        # Son oluşturulan gerçekçi görselleri göster
        if st.session_state.realistic_images:
            st.markdown("#### Son Oluşturulan Gerçekçi Görseller")
            st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
            for i, image_url in enumerate(st.session_state.realistic_images[-4:]):  # Son 4 görseli göster
                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                st.image(image_url, use_column_width=True, caption=f"Görsel #{i+1}")
                if st.button(f"Bu Görseli Dönüştür #{i+1}", key=f"convert_recent_{i}"):
                    set_image_to_convert(image_url)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Veya geçmişteki görsellerden göster
        elif st.session_state.image_history:
            st.markdown("#### Geçmiş Görsellerden Seçin")
            st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
            # Sadece gerçekçi görselleri filtrele
            realistic_images = [img for img in st.session_state.image_history if img["type"] == "Realistic"]
            for i, img_data in enumerate(realistic_images[-4:]):  # Son 4 gerçekçi görseli göster
                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                st.image(img_data["url"], use_column_width=True, caption=f"Görsel {img_data['timestamp']}")
                if st.button(f"Bu Görseli Dönüştür #{i+1}", key=f"convert_hist_{i}"):
                    set_image_to_convert(img_data["url"])
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# 3. Etsy Metadata Sekmesi
with tab3:
    st.markdown('<div class="section-title"><h3>Etsy Metadata Oluşturma</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.selected_image_for_etsy:
        st.markdown("#### Seçilen Görsel")
        st.image(st.session_state.selected_image_for_etsy, width=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_title = st.text_input("Ürün Başlığı", "Özel Fotoğraftan Portre")
            product_description = st.text_area(
                "Ürün Açıklaması", 
                """Fotoğrafınızdan oluşturulan özel dijital portre.
                Tamamen kişiselleştirilmiş, yüksek çözünürlüklü dijital dosya olarak teslim edilir.
                Baskı için mükemmel, anında indirilebilir."""
            )
        
        with col2:
            tags = st.text_input(
                "Etiketler (virgülle ayrılmış)",
                "özel portre, dijital sanat, kişiselleştirilmiş hediye, aile portresi, fotoğraftan sanata"
            )
            price = st.number_input("Fiyat ($)", min_value=5.0, value=19.99, step=1.0)
            delivery_format = st.selectbox(
                "Teslimat Formatı",
                ["Dijital İndirme (JPG & PNG)", "Dijital İndirme + Baskı", "Sadece Baskı"]
            )
        
        # Metadata oluştur butonu
        if st.button("Etsy Metadata Oluştur"):
            with st.spinner("Metadata oluşturuluyor..."):
                # Seçilen görselin çizgi film mi gerçekçi mi olduğunu belirle
                image_type = "Cartoon"
                for item in st.session_state.image_history:
                    if item["url"] == st.session_state.selected_image_for_etsy:
                        image_type = item["type"]
                        break
                
                metadata = {
                    "title": product_title,
                    "description": product_description,
                    "tags": tags.split(","),
                    "price": price,
                    "delivery_format": delivery_format,
                    "image_type": image_type,
                    "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "image_url": st.session_state.selected_image_for_etsy
                }
                
                # Metadata'yı JSON olarak göster
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Oluşturulan Etsy Metadata:")
                st.json(metadata)
                
                # İndirme butonu
                json_str = json.dumps(metadata, indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="etsy_metadata.json" class="download-btn">Metadata Dosyasını İndir</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # SEO önerileri oluştur
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Etsy için SEO Önerileri:")
                
                seo_suggestions = [
                    "Maksimum görünürlük için Etsy'nin izin verdiği tüm 13 etiketi kullanın",
                    "Daha iyi arama eşleşmesi için başlığınıza 'özel portre' ekleyin",
                    "'kişiselleştirilmiş hediye' yüksek arama hacmine sahip bir terimdir",
                    "'doğum günü hediyesi' veya 'yıldönümü hediyesi' gibi özel vesileler ekleyin",
                    "'özel portre' popüler bir arama terimidir",
                    "Daha iyi hedefleme için 'aile çizgi film portresi' gibi uzun kuyruklu anahtar kelimeler kullanın",
                    "Tatil dönemlerinde ilgili mevsimsel anahtar kelimeler ekleyin",
                    "'dijital indirme' veya 'yazdırılabilir sanat' gibi materyal terimleri ekleyin",
                    "Daha iyi müşteri beklentileri için açıklamanızda teslim süresinden bahsedin",
                    "Alıcıların aradığı anahtar kelimeleri kullanın",
                    "Ana anahtar kelimelerinizin varyasyonlarını ekleyin (portre, portreler, portre sanatı)",
                    "Görünürlüğü artırmak için 'el yapımı' veya 'özel yapım' gibi nitelikler ekleyin",
                    "Ürün kategorinizle ilgili trend olan anahtar kelimeleri kullanmayı düşünün"
                ]
                
                for suggestion in seo_suggestions:
                    st.markdown(f"• {suggestion}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Pazarlama ipuçları
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Pazarlama İpuçları:")
                
                marketing_tips = [
                    "Birden fazla portre için paket indirimleri sunun",
                    "İlk kez alışveriş yapanlar için sınırlı süreli promosyon oluşturun",
                    "Stil aralığınızı göstermek için örnek görsellerden oluşan bir portföy ekleyin",
                    "Açıklamanıza müşteri görüşleri ekleyin",
                    "Ek ücret karşılığında acil teslimat seçeneği sunun",
                    "Tatile özel promosyonlar oluşturun",
                    "Farklı fiyat noktalarında farklı boyut seçenekleri sunun",
                    "İş kalitenizi göstermek için öncesi/sonrası örnekleri sağlayın",
                    "Müşterilerin başkaları için satın alabileceği hediye çekleri oluşturun",
                    "Ek hizmet olarak çerçeveleme seçenekleri sunun",
                    "Geri dönen müşteriler için bir sadakat programı oluşturun"
                ]
                
                for tip in marketing_tips:
                    st.markdown(f"• {tip}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.session_state.notification = "Etsy metadata başarıyla oluşturuldu"
                st.session_state.notification_type = "success"
            
    else:
        st.info("Lütfen önce 'Gerçekçi Görsel Oluşturma' veya 'Çizgi Film Dönüşümü' sekmesinden bir görsel seçin.")

# 4. Görsel Geçmişi Sekmesi
with tab4:
    st.markdown('<div class="section-title"><h3>Oluşturulan Görsel Geçmişi</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.image_history:
        # Filtre seçenekleri ekle
        col1, col2 = st.columns(2)
        with col1:
            filter_options = ["Tümü", "Gerçekçi", "Çizgi Film"]
            selected_filter = st.selectbox("Görsel Tipine Göre Filtrele", filter_options)
        with col2:
            sort_order = st.selectbox(
                "Sıralama Düzeni",
                options=["En Yeni Önce", "En Eski Önce"]
            )
        
        # Görselleri filtrele ve sırala
        if selected_filter == "Tümü":
            filtered_images = st.session_state.image_history
        elif selected_filter == "Gerçekçi":
            filtered_images = [img for img in st.session_state.image_history if img["type"] == "Realistic"]
        else:  # Çizgi Film
            filtered_images = [img for img in st.session_state.image_history if "Cartoon" in img["type"]]
        
        if sort_order == "En Yeni Önce":
            filtered_images = list(reversed(filtered_images))
        
        if filtered_images:
            st.markdown("#### Önceden Oluşturulan Görseller")
            st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
            for i, img_data in enumerate(filtered_images[:12]):  # En fazla 12 görsel göster
                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                st.image(img_data["url"], use_column_width=True, 
                        caption=f"{img_data['type']} - {img_data['timestamp']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if img_data["type"] == "Realistic":
                        if st.button(f"Dönüştür", key=f"convert_hist_{i}"):
                            set_image_to_convert(img_data["url"])
                
                with col2:
                    if st.button(f"Etsy İçin", key=f"etsy_hist_{i}"):
                        set_image_for_etsy(img_data["url"])
                
                with col3:
                    image_data = download_image(img_data["url"])
                    if image_data:
                        st.download_button(
                            label="İndir",
                            data=image_data,
                            file_name=f"history_image_{i}.png",
                            mime="image/png",
                            key=f"download_hist_{i}"
                        )
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Geçmişi temizle butonu
            if st.button("Geçmişi Temizle", key="clear_history"):
                st.session_state.image_history = []
                st.session_state.notification = "Görsel geçmişi temizlendi"
                st.session_state.notification_type = "info"
                st.rerun()
        else:
            st.info("Seçilen filtrelere uygun görsel bulunamadı.")
    else:
        st.info("Henüz görsel oluşturulmadı. Görsel geçmişi burada görünecek.")

# Footer
st.markdown("""
<div class="footer">
    <p>Telif hakkı © 2025</p>
    <p>Tüm görseller, OpenAI'nin kullanım koşullarına uygun olarak kullanılmaktadır.</p>
</div>
""", unsafe_allow_html=True)
