import streamlit as st
import json
import base64
import os
import io
from PIL import Image
from openai import OpenAI
import random
from datetime import datetime

# Sayfa yapılandırması
st.set_page_config(page_title="AI Görsel Üretim Aracı", layout="wide")

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

# Session state başlatma
if 'realistic_images' not in st.session_state:
    st.session_state.realistic_images = []
if 'cartoon_images' not in st.session_state:
    st.session_state.cartoon_images = []
if 'realistic_prompt' not in st.session_state:
    st.session_state.realistic_prompt = ""
if 'selected_image' not in st.session_state:
    st.session_state.selected_image = None

# Ana sekmeler
tab1, tab2, tab3 = st.tabs(["Görsel Oluşturma", "Cartoon Dönüşümü", "Etsy Metadata"])

with tab1:
    st.markdown('<div class="section-title"><h3>Görsel Oluşturma Ayarları</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Kategori seçimi
        category_options = [
            "Aile & Çift Portreleri",
            "Düğün Portreleri",
            "Doğum Günü Portreleri",
            "Mezuniyet Portreleri",
            "Evcil Hayvan Portreleri",
            "Özel Anı Portreleri"
        ]
        selected_category = st.selectbox("Kategori Seçin", category_options)
        
        # Fikir seçimi
        idea_options = {
            "Aile & Çift Portreleri": ["Aile Portresi", "Çift Portresi", "Yıldönümü Portresi", "Aşk Portresi"],
            "Düğün Portreleri": ["Düğün Anı", "Nikah Töreni", "Düğün Dansı", "Gelin Buketi"],
            "Doğum Günü Portreleri": ["Doğum Günü Kutlaması", "Pasta Kesimi", "Hediye Açma", "Parti Portresi"],
            "Mezuniyet Portreleri": ["Diploma Töreni", "Kep Atma", "Mezuniyet Cübbesi", "Başarı Portresi"],
            "Evcil Hayvan Portreleri": ["Köpek Portresi", "Kedi Portresi", "Evcil Hayvan ve Sahip", "Sevimli Anı"],
            "Özel Anı Portreleri": ["Tatil Anısı", "Seyahat Portresi", "Özel Gün", "Aile Buluşması"]
        }
        selected_idea = st.selectbox("Fikir Seçin", idea_options[selected_category])
        
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
        
        # Prompt oluşturma butonu
        if st.button("Promptları Oluştur"):
            # GPT ile prompt oluşturma
            ethnicity_prompt = ""
            if selected_ethnicity != "Karışık/Rastgele":
                ethnicity_prompt = f", {selected_ethnicity} appearance"
            
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
                
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### Oluşturulan Gerçekçi Prompt:")
                st.text_area("", realistic_prompt, height=150, key="prompt_result")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Prompt oluşturulurken bir hata oluştu: {e}")
        
        # Görselleri oluşturma butonu
        if st.button("Görselleri Oluştur") and st.session_state.realistic_prompt:
            try:
                with st.spinner("Görseller oluşturuluyor..."):
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
                    st.markdown("#### Oluşturulan Gerçekçi Görseller:")
                    
                    # Görselleri göster
                    image_cols = st.columns(min(num_images, 2))
                    for i, image_url in enumerate(st.session_state.realistic_images):
                        col_idx = i % len(image_cols)
                        with image_cols[col_idx]:
                            st.image(image_url, use_column_width=True)
                            if st.button(f"Bu Görseli Seç #{i+1}", key=f"select_img_{i}"):
                                st.session_state.selected_image = image_url
                                st.success(f"Görsel #{i+1} seçildi! Cartoon Dönüşümü sekmesine geçebilirsiniz.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Görseller oluşturulurken bir hata oluştu: {e}")

with tab2:
    st.markdown('<div class="section-title"><h3>Cartoon Stiline Dönüştürme</h3></div>', unsafe_allow_html=True)
    
    if st.session_state.selected_image:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Seçilen Gerçekçi Görsel")
            st.image(st.session_state.selected_image, use_column_width=True)
        
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
            
            selected_cartoon_style = st.selectbox("Cartoon Stili", cartoon_style_options)
            
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
                placeholder="Örn: pastel renkler, abartılı yüz ifadeleri..."
            )
            
            # Dönüştürme butonu
            if st.button("Cartoon Stiline Dönüştür"):
                try:
                    with st.spinner("Görsel dönüştürülüyor..."):
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
                        st.image(cartoon_image_url, use_column_width=True)
                        
                except Exception as e:
                    st.error(f"Görsel dönüştürülürken bir hata oluştu: {e}")
    else:
        st.info("Lütfen önce 'Görsel Oluşturma' sekmesinden bir görsel oluşturun ve seçin.")
        
    # Geçmiş dönüşümler
    if st.session_state.cartoon_images:
        st.markdown("#### Önceki Dönüşümler")
        for i, img_data in enumerate(st.session_state.cartoon_images):
            st.image(img_data["url"], caption=f"{img_data['style']} - {img_data['timestamp']}", width=200)

with tab3:
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
            
    else:
        st.info("Lütfen önce 'Cartoon Dönüşümü' sekmesinden bir görseli cartoon stiline dönüştürün.")

# Footer
st.markdown("---")
st.markdown("© 2025 AI Görsel Üretim Aracı | Tüm hakları saklıdır.")
