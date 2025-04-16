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

# Sayfa yapılandırması
st.set_page_config(page_title="AI Görsel Üretim Aracı", layout="wide")

# OpenAI API istemcisini başlat
client = OpenAI(api_key=st.secrets["openai_api_key"])

# Session state başlatma
if 'realistic_images' not in st.session_state:
    st.session_state.realistic_images = []
if 'cartoon_images' not in st.session_state:
    st.session_state.cartoon_images = []
if 'realistic_prompt' not in st.session_state:
    st.session_state.realistic_prompt = ""
if 'selected_image' not in st.session_state:
    st.session_state.selected_image = None
if 'show_cartoon_section' not in st.session_state:
    st.session_state.show_cartoon_section = False

# Kategori ve alt kategoriler
nis_kategorileri = {
    "Aile & Çift Portreleri (Pixar / Disney tarzı)": [
        "Pixar Style Anniversary Portrait",
        "Engagement Couple Cartoon Portrait",
        "Disney-Inspired Wedding Portrait",
        "First Valentine's Together - Cartoon Version",
        "Before & After Pixar Style Transformation",
        "Holding Hands in Animated Magic",
        "Cartoon Hugging Pose with Background",
        "Kissing Couple Sunset Cartoon",
        "Holding a Pet Together",
        "Wedding Dress & Suit in Disney Style",
        "Couple on the Beach Pixar Style",
        "Matching T-Shirts Cartoon Look",
        "Proposal Scene Reimagined",
        "First Date Memory in Animation",
        "Baby Announcement Cartoon Portrait",
        "Couple Cooking Together Cartoon",
        "Couple Reading Book in Bed Pixar Style",
        "Christmas Sweater Couple Portrait",
        "Couple Traveling Scene (Eiffel, NYC…)",
        "Couple with Pet in Fairytale Scene",
        "Cartoon Style Couple on Bike Ride",
        "Disney Couple Holding Balloons",
        "Anime-Inspired Couple Hug",
        "Pajamas Cartoon Couple",
        "Family with Baby in Cartoon Style",
        "Personalized Names & Date Background",
        "Cartoon Couple Watching Movie",
        "Sunflower Field Couple Style",
        "Fall Leaves Couple Portrait",
        "Winter Wonderland Couple Illustration"
    ],
    "Pet Karakterleri (Köpek / Kedi)": [
        "Custom Cartoon Pet Portrait (Pixar Inspired)",
        "Dog with Sunglasses & Name Tag",
        "Superhero Style Dog Portrait",
        "Royal Style Cat Portrait with Crown",
        "Pet with Owner (Half Human-Half Pet)",
        "Cartoon Pet with Name on Sign",
        "Birthday Pet Illustration",
        "Pet Angel Memorial Portrait",
        "Funny Bathroom Poster – Cat on Toilet",
        "Pet with Pizza/Donut Illustration",
        "Two Dogs Hugging in Pixar Style",
        "Cartoon Cat and Dog Duo",
        "Pet Graduation Portrait",
        "Pet & Child Holding Hands Cartoon",
        "Rainbow Bridge Tribute",
        "Pet With Galaxy Background",
        "Cartoon Dog Chilling at the Beach",
        "Holiday Dog Portrait (Santa Hat)",
        "Wedding Pet Portrait with Veil",
        "Cartoon Puppy With His Favorite Toy",
        "Sleeping Dog and Moon Cartoon Style",
        "Funny Grumpy Cat in Cartoon Style",
        "Cartoon Pet Family Portrait",
        "Cat Drinking Wine (Stylized)",
        "Pet as Super Mario Character",
        "Dog as Astronaut Cartoon Portrait",
        "Before & After Cartoon Pet Glow-Up",
        "Cartoon Pet Face Close-Up",
        "Pet in Frame on Living Room Wall Mockup",
        "Pet in a Coffee Cup Illustration"
    ],
    "Çocuklar & Bebekler İçin Portreler": [
        "Baby First Birthday Cartoon Portrait",
        "Pixar Style Baby Laughing Scene",
        "Siblings Hugging Cartoon Style",
        "Twins Portrait with Names & Date",
        "Newborn with Stuffed Animal",
        "Cartoon Baby Angel Memorial",
        "Christmas Baby Portrait with Hat",
        "Cartoon Toddler in Forest Scene",
        "Baby Holding Parent Finger Illustration",
        "Super Baby Flying Portrait",
        "Baby & Pet Together Cartoon Style",
        "Cartoonized Baby Playing with Toys",
        "Cute Face Close-Up in Pixar Look",
        "Crying Baby Cartoon Portrait (Funny)",
        "Baby in Animal Costume",
        "Cartoon Kid Drawing Scene",
        "First Steps Memory Cartoon",
        "Sitting Baby on Floor Cartoon",
        "Toddler in Rain with Umbrella",
        "Sibling Hugging Baby Style",
        "Cartoon Baby and Balloon Scene",
        "Baby in Garden Scene",
        "Funny Baby on Toilet Illustration",
        "Baby in Cradle with Fairy Lights",
        "Dreamland Baby Portrait",
        "Cute Baby Sleeping with Moon",
        "Baby as Little Prince/Princess",
        "Cartoonized Baby Dressed as Santa",
        "Kid Dressed as Astronaut",
        "Baby's First Tooth Cartoon Style"
    ],
    "İş Hayatı & Hediye Portreleri": [
        "Cartoon Teacher Portrait with Blackboard",
        "Boss Day Gift - Cartoon Office Look",
        "Accountant Cartoon Portrait with Calculator",
        "Female CEO Cartoon Style with Desk",
        "Freelancer at Laptop with Coffee",
        "Engineer with Blueprints & Helmet",
        "Doctor with Cartoon Style Medical Tools",
        "Custom Cartoon Lawyer Portrait",
        "Cartoon Barista with Coffee Machine",
        "Teacher with Students Behind",
        "Digital Nomad Cartoon Beach Setup",
        "Cartoon Zoom Call Pose",
        "Nurse with Clipboard Cartoon Style",
        "Mezuniyet Karikatürü Kasketli",
        "Funny Office Pose (Cartoon Chaos)",
        "Podcast Host Cartoon Setup",
        "Makeup Artist with Brushes",
        "Cartoon Fitness Trainer with Dumbbells",
        "Cartoon YouTuber Setup",
        "Real Estate Agent Cartoon with Keys",
        "Therapist at Desk in Cartoon Style",
        "Cartoon Music Producer with Headphones",
        "Teacher Reading Book to Kids",
        "Cartoon Delivery Driver Style",
        "Funny Freelancer Desk Mess Cartoon",
        "Graduation Cartoon with Hat & Diploma",
        "Cartoon Portrait in a Laptop Screen",
        "Boss Lady Desk Scene",
        "Teacher Holding Apple & Books",
        "Illustrated Portrait with Job Title & Catchphrase"
    ],
    "Duvar Dekoru & Komik Stil Afişler (Poster Tarzı)": [
        "No Bitchin' in the Kitchen Poster",
        "Bathroom Cat Reading Newspaper",
        "Superhero Pet Poster",
        "Stay Saucy Tomato Wall Art",
        "Let's Get This Bread Poster",
        "Graffiti Style Funny Dog Portrait",
        "Minimalist Couple Hug Poster",
        "Poster: Don't Let Idiots Ruin Your Day",
        "Espresso Yourself Cartoon Art",
        "Quirky Dog Poster Bundle",
        "Cartoon Quote Poster - Self Love",
        "'You Got This' Cartoon Motivational",
        "Funny Poster - Grumpy Cat Monday",
        "Anime Girl 'Don't Care' Poster",
        "Retro Food Character Wall Poster",
        "Shower Thoughts Black & White Poster",
        "'Get Out of My Kitchen' Funny Cat",
        "Cartoon Eyes Peeking Poster",
        "Before/After Glow Up Poster Style",
        "Cute Bear Cartoon in Frame",
        "Cartoon City Background Poster",
        "Black Cat with Ramen Bowl Poster",
        "'I Need Coffee' Bunny Poster",
        "Cartoon Style Life Tips Poster Set",
        "'No Drama Lama' Cartoon Wall Art",
        "Cat & Dog Funny Bathroom Rules",
        "'You Are My Sunshine' Cartoon Poster",
        "Color Pop Funny Animal Poster",
        "Cartoon Hug Scene – Quote Version",
        "Cartoon Kitchen Scene Poster"
    ],
    "Özel Günler & Kutlamalar": [
        "Birthday Cartoon Portrait with Cake",
        "Anniversary Celebration Scene",
        "Valentine's Day Couple Portrait",
        "Christmas Family Cartoon",
        "New Year's Eve Party Scene",
        "Halloween Costume Cartoon",
        "Easter Bunny Family Portrait",
        "Thanksgiving Dinner Scene",
        "Mother's Day Cartoon Gift",
        "Father's Day Cartoon Portrait",
        "Graduation Ceremony Cartoon",
        "Baby Shower Announcement",
        "Wedding Day Cartoon Scene",
        "Retirement Celebration Portrait",
        "Housewarming Gift Cartoon",
        "Engagement Announcement Scene",
        "Job Promotion Celebration",
        "New Baby Arrival Cartoon",
        "Friendship Day Cartoon",
        "Vacation Memory Cartoon"
    ],
    "Fantastik & Tematik Portreler": [
        "Family as Superheroes",
        "Pet as Fantasy Character",
        "Space Adventure Family Portrait",
        "Underwater Mermaid Scene",
        "Fairy Tale Castle Background",
        "Steampunk Style Portrait",
        "Medieval Fantasy Characters",
        "Cyberpunk City Background",
        "Jungle Adventure Scene",
        "Western Cowboy Style Portrait",
        "Pirate Ship Family Adventure",
        "Viking Style Family Portrait",
        "Wizard School Magic Scene",
        "Dinosaur World Background",
        "Alien Planet Exploration",
        "Time Traveler Portrait",
        "Post-Apocalyptic Scene",
        "Ancient Egypt Theme",
        "Futuristic City Background",
        "Fantasy Forest Creatures"
    ]
}

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
    .cartoon-section {
        margin-top: 30px;
        padding: 20px;
        background-color: #1e1e1e;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .image-card {
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
        background-color: #222;
    }
    .image-card:hover {
        border-color: #ff4b4b;
        box-shadow: 0 0 10px rgba(255, 75, 75, 0.3);
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
</style>
""", unsafe_allow_html=True)

# Başlık ve açıklama
st.markdown("""
<div class="header">
    <img src="https://img.icons8.com/color/48/000000/paint-palette.png" alt="palette icon">
    <h1>AI Görsel Üretim Aracı</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("### Gerçekçi Görsel Üretim ve Cartoon Dönüşüm Asistanı")

# Ana sekmeler
tab1, tab2 = st.tabs(["Görsel Oluşturma & Dönüştürme", "Etsy Metadata"])

with tab1:
    st.markdown('<div class="section-title"><h3>Görsel Oluşturma Ayarları</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Kategori seçimi
        selected_category = st.selectbox("Kategori Seçin", list(nis_kategorileri.keys()))
        
        # Fikir seçimi
        selected_idea = st.selectbox("Fikir Seçin", nis_kategorileri[selected_category])
        
        # Etnik köken/görünüm seçimi
        ethnicity_options = [
            "Karışık/Rastgele",
            "Avrupa",
            "Asya",
            "Afrika",
            "Orta Doğu",
            "Latin Amerika",
            "Hint",
            "Doğu Asya"
        ]
        selected_ethnicity = st.selectbox("Görünüm/Etnik Köken", ethnicity_options)
        
        # Görsel stili
        style_options = [
            "Fotoğraf gerçekçiliği",
            "Yumuşak aydınlatma",
            "Dramatik aydınlatma",
            "Dış mekan doğal ışık",
            "İç mekan stüdyo",
            "Vintage",
            "Modern",
            "Minimalist"
        ]
        selected_style = st.selectbox("Görsel Stili", style_options)
        
        # Ek detaylar
        additional_details = st.text_area(
            "Ek Detaylar (İsteğe Bağlı)", 
            placeholder="Örn: kızıl saç, mavi gözler, plaj arka planı..."
        )
    
    with col2:
        # Görsel boyutu
        size_options = ["1024x1024", "1024x1792", "1792x1024"]
        selected_size = st.selectbox("Görsel Boyutu", size_options)
        
        # Görsel kalitesi
        quality_options_display = ["Standart", "HD"]
        quality_options_api = ["standard", "hd"]
        quality_index = st.selectbox("Görsel Kalitesi", quality_options_display)
        selected_quality = quality_options_api[quality_options_display.index(quality_index)]
        
        # Görsel sayısı
        num_images = st.slider("Oluşturulacak Görsel Sayısı", 1, 4, 2)
        
        # Hızlı prompt oluşturma
        st.markdown("#### 🚀 Hızlı Prompt Oluşturma")
        
        if st.button("Hızlı Prompt Oluştur"):
            with st.spinner("Prompt oluşturuluyor..."):
                ethnicity_prompt = ""
                if selected_ethnicity != "Karışık/Rastgele":
                    ethnicity_prompt = f", {selected_ethnicity} appearance"
                
                # Basitleştirilmiş prompt oluşturma
                realistic_prompt = f"A photorealistic image of {selected_idea}{ethnicity_prompt}, in {selected_style} style. {additional_details}"
                st.session_state.realistic_prompt = realistic_prompt
                
                st.success("Prompt oluşturuldu!")
                st.code(realistic_prompt)
        
        # Detaylı prompt oluşturma
        st.markdown("#### 🎯 Detaylı Prompt Oluşturma")
        
        if st.button("Detaylı Prompt Oluştur"):
            with st.spinner("Detaylı prompt oluşturuluyor..."):
                # GPT ile prompt oluşturma
                system_prompt = """
                Sen profesyonel bir fotoğrafçı ve görsel sanatçısısın. 
                DALL-E için gerçekçi, yüksek kaliteli görsel oluşturmak için prompt yazman gerekiyor.
                Verilen bilgilere dayanarak detaylı, gerçekçi ve estetik bir fotoğraf için prompt oluştur.
                Prompt İngilizce olmalı ve gerçekçi bir fotoğraf için gerekli tüm detayları içermeli.
                """
                
                user_prompt = f"""
                Kategori: {selected_category}
                Fikir: {selected_idea}
                Görünüm: {selected_ethnicity}
                Stil: {selected_style}
                Ek detaylar: {additional_details}
                
                Lütfen bu bilgilere dayanarak gerçekçi, yüksek kaliteli bir fotoğraf için DALL-E prompt'u oluştur.
                Prompt, fotoğraf çekimi için gerekli tüm detayları içermeli: kompozisyon, aydınlatma, atmosfer, renk şeması, vb.
                Prompt'un başında "A photorealistic image" ifadesi olsun ve AI tarafından oluşturulmuş görüntü hissi vermemesi için direktifler ekle.
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
                    
                    st.success("Detaylı prompt oluşturuldu!")
                    st.code(realistic_prompt)
                    
                except Exception as e:
                    st.error(f"Prompt oluşturulurken bir hata oluştu: {e}")
    
    # Görselleri oluşturma butonu - Ortalanmış
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("👉 GÖRSELLERİ OLUŞTUR 👈", use_container_width=True):
            if not st.session_state.realistic_prompt:
                st.warning("Lütfen önce bir prompt oluşturun.")
            else:
                try:
                    with st.spinner("Görseller oluşturuluyor... Bu işlem biraz zaman alabilir."):
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
                        
                        st.success(f"{len(images)} görsel başarıyla oluşturuldu!")
                        
                except Exception as e:
                    st.error(f"Görseller oluşturulurken bir hata oluştu: {e}")
    
    # Oluşturulan görselleri göster
    if st.session_state.realistic_images:
        st.markdown("### 🖼️ Oluşturulan Görseller")
        
        # Görselleri göster
        cols = st.columns(min(len(st.session_state.realistic_images), 2))
        for i, image_url in enumerate(st.session_state.realistic_images):
            col_idx = i % len(cols)
            with cols[col_idx]:
                st.markdown(f'<div class="image-card">', unsafe_allow_html=True)
                st.image(image_url, use_container_width=True)
                if st.button(f"Bu Görseli Cartoon'a Dönüştür #{i+1}", key=f"convert_{i}"):
                    st.session_state.selected_image = image_url
                    st.session_state.show_cartoon_section = True
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Cartoon dönüşüm bölümü
    if st.session_state.show_cartoon_section and st.session_state.selected_image:
        st.markdown('<div class="cartoon-section">', unsafe_allow_html=True)
        st.markdown("## 🎭 Cartoon Dönüşümü")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Seçilen Gerçekçi Görsel")
            st.image(st.session_state.selected_image, use_container_width=True)
        
        with col2:
            st.markdown("#### Cartoon Stili Seçimi")
            
            cartoon_style_options = [
                "Pixar 3D",
                "Disney 2D Animasyon",
                "DreamWorks",
                "Anime",
                "South Park",
                "The Simpsons",
                "Studio Ghibli",
                "Claymation",
                "Comic Book",
                "Watercolor Illustration"
            ]
            
            selected_cartoon_style = st.selectbox("Cartoon Stili", cartoon_style_options, key="cartoon_style")
            
            # Stil detayları
            style_details = {
                "Pixar 3D": "3D Pixar animation style with detailed textures, expressive features, and warm lighting",
                "Disney 2D Animasyon": "Classic Disney 2D animation style with smooth lines, vibrant colors, and expressive characters",
                "DreamWorks": "DreamWorks animation style with exaggerated features, dynamic poses, and rich texturing",
                "Anime": "Japanese anime style with large eyes, simplified features, and vibrant colors",
                "South Park": "South Park style with simple shapes, flat colors, and minimalist design",
                "The Simpsons": "The Simpsons style with yellow skin, overbite, and simplified cartoon features",
                "Studio Ghibli": "Studio Ghibli style with detailed backgrounds, soft colors, and whimsical elements",
                "Claymation": "Claymation style with textured surfaces, slightly imperfect shapes, and warm tones",
                "Comic Book": "Comic book style with bold outlines, flat colors, and action-oriented composition",
                "Watercolor Illustration": "Watercolor illustration style with soft edges, transparent colors, and artistic brush strokes"
            }
            
            st.markdown(f"**Stil Detayları:** {style_details[selected_cartoon_style]}")
            
            additional_style_details = st.text_area(
                "Ek Stil Detayları (İsteğe Bağlı)",
                placeholder="Örn: pastel renkler, abartılı yüz ifadeleri...",
                key="additional_style"
            )
            
            # Dönüştürme butonu
            if st.button("🔄 Cartoon Stiline Dönüştür", use_container_width=True):
                try:
                    with st.spinner("Görsel dönüştürülüyor... Bu işlem biraz zaman alabilir."):
                        # Gerçekçi görseli cartoon stiline dönüştürme promptu
                        style_prompt = f"""
                        Transform this realistic image into a {selected_cartoon_style} cartoon style. 
                        {style_details[selected_cartoon_style]}. 
                        {additional_style_details}
                        Maintain the same composition, characters, and scene, but fully convert to cartoon style.
                        Make it look professional, high-quality, and authentic to the {selected_cartoon_style} style.
                        """
                        
                        # DALL-E API ile dönüştürme
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
                        
                        st.success("Görsel başarıyla cartoon stiline dönüştürüldü!")
                        
                except Exception as e:
                    st.error(f"Görsel dönüştürülürken bir hata oluştu: {e}")
        
        # Dönüştürülen görselleri göster
        if st.session_state.cartoon_images:
            st.markdown("#### Son Dönüştürülen Cartoon")
            st.image(st.session_state.cartoon_images[-1]["url"], use_container_width=True)
            
            if st.button("📊 Etsy Metadata Oluşturmaya Geç"):
                st.switch_page("Etsy Metadata")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Geçmiş dönüşümler
        if len(st.session_state.cartoon_images) > 1:
            st.markdown("### 📜 Önceki Dönüşümler")
            
            # Önceki dönüşümleri göster (en son olanı hariç)
            prev_images = st.session_state.cartoon_images[:-1]
            cols = st.columns(min(len(prev_images), 3))
            for i, img_data in enumerate(prev_images):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    st.image(img_data["url"], caption=f"{img_data['style']} - {img_data['timestamp']}", width=200)

with tab2:
    st.markdown('<div class="section-title"><h3>Etsy Metadata Oluşturma</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.cartoon_images:
        st.markdown("#### Son Dönüştürülen Görsel")
        st.image(st.session_state.cartoon_images[-1]["url"], width=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_title = st.text_input("Ürün Başlığı", f"Özel {st.session_state.cartoon_images[-1]['style']} Tarzı Portre")
            product_description = st.text_area(
                "Ürün Açıklaması", 
                f"""Gerçek fotoğrafınızdan özel olarak oluşturulan {st.session_state.cartoon_images[-1]['style']} tarzı dijital portre. 
                Tamamen kişiselleştirilmiş, yüksek çözünürlüklü dijital dosya olarak teslim edilir.
                Baskı için mükemmel, anında indirilebilir."""
            )
        
        with col2:
            tags = st.text_input(
                "Etiketler (virgülle ayırın)",
                f"özel portre, {st.session_state.cartoon_images[-1]['style'].lower()}, dijital sanat, kişiselleştirilmiş hediye, aile portresi"
            )
            price = st.number_input("Fiyat ($)", min_value=5.0, value=19.99, step=1.0)
            delivery_format = st.selectbox(
                "Teslimat Formatı",
                ["Dijital İndirme (JPG & PNG)", "Dijital İndirme + Baskı", "Sadece Baskı"]
            )
        
# Metadata oluştur butonu
if st.button("Etsy Metadatası Oluştur"):
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
    
    # Metadatayı JSON olarak göster
    st.markdown('<div class="result-container">', unsafe_allow_html=True)
    st.markdown("#### Oluşturulan Etsy Metadata:")
    st.json(metadata)
    
    # İndirme butonu
    json_str = json.dumps(metadata, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="etsy_metadata.json">Metadata Dosyasını İndir</a>'
    st.markdown(href, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # GPT ile otomatik ürün açıklaması oluşturma
    st.markdown("#### 🤖 AI ile Gelişmiş Ürün Açıklaması")
    
    if st.button("Gelişmiş Ürün Açıklaması Oluştur"):
        with st.spinner("Gelişmiş açıklama oluşturuluyor..."):
            try:
                system_prompt = """
                Sen bir Etsy satıcısısın ve dijital sanat ürünleri satıyorsun.
                Müşterinin fotoğrafından özel olarak oluşturulan cartoon tarzı portreler için
                ikna edici, SEO dostu ve detaylı bir ürün açıklaması yazman gerekiyor.
                """
                
                user_prompt = f"""
                Ürün: {product_title}
                Tarz: {st.session_state.cartoon_images[-1]['style']}
                Teslimat: {delivery_format}
                Fiyat: ${price}
                
                Lütfen bu ürün için aşağıdakileri içeren ikna edici bir Etsy ürün açıklaması yaz:
                1. Dikkat çekici bir giriş
                2. Ürünün benzersiz özellikleri
                3. Sipariş sürecinin açıklaması
                4. Teslimat detayları
                5. Neden bu ürünün mükemmel bir hediye olduğu
                6. Müşteri memnuniyeti garantisi
                
                Açıklama, SEO için anahtar kelimeler içermeli ve duygusal bağlantı kurmalı.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=800
                )
                
                enhanced_description = response.choices[0].message.content.strip()
                
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Gelişmiş Ürün Açıklaması:")
                st.markdown(enhanced_description)
                
                # Kopyalama butonu
                st.text_area("Açıklamayı Kopyala", enhanced_description, height=300)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Açıklama oluşturulurken bir hata oluştu: {e}")
else:
    st.info("Lütfen önce 'Görsel Oluşturma & Dönüştürme' sekmesinden bir görseli cartoon stiline dönüştürün.")
    if st.button("Görsel Oluşturmaya Dön"):
        st.session_state.active_tab = 'Görsel Oluşturma'
        st.rerun()

# Görsel üretim ipuçları
st.markdown("---")
st.markdown("### 🚀 Görsel Üretimi Hızlandırma İpuçları")

tips_expander = st.expander("İpuçlarını Göster")
with tips_expander:
    st.markdown("""
    #### 1. Prompt Optimizasyonu
    - **Kısa ve net promptlar kullanın**: Çok uzun promptlar yerine, önemli detaylara odaklanan kısa promptlar daha hızlı sonuç verir.
    - **Anahtar kelimeleri stratejik kullanın**: "photorealistic", "high quality", "detailed" gibi anahtar kelimeleri başta kullanın.
    
    #### 2. Görsel Ayarları
    - **Daha küçük boyutlar seçin**: 1024x1024 boyutu daha hızlı sonuç üretir.
    - **Standart kalite** HD kaliteden daha hızlıdır.
    
    #### 3. İş Akışı İyileştirmeleri
    - **Hızlı prompt oluşturma** özelliğini kullanın.
    - Aynı anda çok sayıda görsel oluşturmak yerine, 1-2 görsel oluşturup beğendiğinizi seçin.
    
    #### 4. Teknik İyileştirmeler
    - Uygulamayı kullanırken diğer sekmeleri kapatın.
    - İnternet bağlantınızın güçlü olduğundan emin olun.
    - Tarayıcı önbelleğini düzenli olarak temizleyin.
    
    #### 5. Şablon Kullanımı
    - Başarılı bulduğunuz promptları kaydedin ve şablon olarak kullanın.
    - Kategori bazlı hazır promptlar oluşturun ve sadece küçük değişiklikler yapın.
    """)

# Footer
st.markdown("---")
st.markdown("© 2025 AI Görsel Üretim Aracı | Tüm hakları saklıdır.")
