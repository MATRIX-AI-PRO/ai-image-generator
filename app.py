import streamlit as st
import io
import base64
from PIL import Image
import time
from openai import OpenAI

# Parola koruması
def check_password():
    """Basit parola kontrolü"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    password = st.text_input("Şifre giriniz", type="password")
    if password == "matrix2025":  # Güçlü bir şifre belirleyin
        st.session_state.password_correct = True
        return True
    else:
        if password:
            st.error("Şifre yanlış")
        return False

if not check_password():
    st.stop()  # Şifre doğru değilse uygulamayı durdur

# OpenAI istemcisini oluştur
client = OpenAI(api_key=st.secrets["openai_api_key"])

# Niş kategorileri ve fikirleri
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
    ]
}

def generate_prompt(fikir, nis_kategori, detaylar=""):
    """Seçilen fikir için İngilizce prompt oluşturur"""
    
    stil_tanimlari = {
        "Aile & Çift Portreleri (Pixar / Disney tarzı)": "in 3D Disney/Pixar style, warm color tones, detailed 3D modeling, soft shadows, nostalgic feeling",
        "Pet Karakterleri (Köpek / Kedi)": "in Disney-Pixar pet style, cute, vibrant colors, big eyes, expressive facial features",
        "Çocuklar & Bebekler İçin Portreler": "in 3D animation baby face style, big eyes, cute figures, soft lines, bright colors",
        "İş Hayatı & Hediye Portreleri": "professional looking 3D character, detailed office environment, modern and elegant design",
        "Duvar Dekoru & Komik Stil Afişler (Poster Tarzı)": "vibrant colors, minimalist design, funny and playful style, arranged in poster format"
    }
    
    base_prompt = f"{fikir}, {stil_tanimlari[nis_kategori]}"
    
    if detaylar:
        base_prompt += f", {detaylar}"
    
    return base_prompt

def generate_realistic_prompt(cartoon_prompt):
    """Cartoon prompttan gerçekçi bir prompt oluşturur"""
    try:
        system_message = """You are an expert in converting cartoon/animation style image prompts into realistic photography prompts. 
        Take the given cartoon-style prompt and convert it to a prompt that would generate a realistic, high-quality photographic image 
        of the same subject. Maintain the core subject and theme, but adapt it to realistic photography style.
        
        Your output should ONLY be the new realistic prompt text, nothing else. No explanations or additional text.
        """
        
        user_message = f"Convert this cartoon prompt to a realistic photography prompt: {cartoon_prompt}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating realistic prompt: {str(e)}"

def generate_image(prompt):
    """OpenAI API kullanarak görsel oluşturur"""
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        return image_url, None
    except Exception as e:
        return None, str(e)

def generate_etsy_metadata(prompt, fikir, nis_kategori):
    """Etsy için başlık, açıklama ve etiketler oluşturur"""
    try:
        system_message = """You are an Etsy listing expert. Create the following for a digital art product based on the given image prompt:
        1. Title: Under 140 characters, SEO-optimized with relevant keywords
        2. Description: 3-4 paragraphs highlighting product features and creating emotional connection
        3. Tags: 13 tags, each maximum 20 characters (comma separated)
        
        Format your response exactly as:
        TITLE: [title text]
        
        DESCRIPTION:
        [description text]
        
        TAGS:
        [tag1], [tag2], ... [tag13]
        """
        
        user_message = f"""
        Image prompt: {prompt}
        Product idea: {fikir}
        Category: {nis_kategori}
        
        Create Etsy-optimized title, description, and tags for this digital art product.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating Etsy metadata: {str(e)}"

def get_download_link(text, filename, link_text):
    """Metin dosyasını indirmek için link oluşturur"""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def main():
    st.set_page_config(page_title="AI Görsel Üretim Aracı", page_icon="🎨", layout="wide")
    
    st.title("🎨 AI Görsel Üretim Aracı")
    st.markdown("### Pixar/Disney Tarzı ve Gerçekçi Görsel Üretim Asistanı")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Görsel Oluşturma Ayarları")
        
        nis_kategori = st.selectbox("Niş Kategori Seçin", list(nis_kategorileri.keys()))
        
        fikir = st.selectbox("Fikir Seçin", nis_kategorileri[nis_kategori])
        
        detaylar = st.text_area("Ek Detaylar (İsteğe Bağlı)", 
                               placeholder="Örn: red hair, blue eyes, beach background...")
        
        if st.button("Promptları Oluştur"):
            cartoon_prompt = generate_prompt(fikir, nis_kategori, detaylar)
            st.session_state.cartoon_prompt = cartoon_prompt
            
            with st.spinner("Gerçekçi prompt oluşturuluyor..."):
                realistic_prompt = generate_realistic_prompt(cartoon_prompt)
                st.session_state.realistic_prompt = realistic_prompt
            
            st.session_state.cartoon_image = None
            st.session_state.realistic_image = None
            st.session_state.error = None
            st.session_state.etsy_metadata_cartoon = None
            st.session_state.etsy_metadata_realistic = None
        
        if st.button("Görselleri Oluştur", type="primary"):
            if "cartoon_prompt" in st.session_state and "realistic_prompt" in st.session_state:
                # Cartoon görsel oluştur
                with st.spinner("Cartoon tarzı görsel oluşturuluyor..."):
                    cartoon_image_url, cartoon_error = generate_image(st.session_state.cartoon_prompt)
                    st.session_state.cartoon_image = cartoon_image_url
                    st.session_state.cartoon_error = cartoon_error
                    
                    if not cartoon_error:
                        with st.spinner("Cartoon için Etsy metadata oluşturuluyor..."):
                            etsy_metadata_cartoon = generate_etsy_metadata(
                                st.session_state.cartoon_prompt, 
                                fikir, 
                                nis_kategori
                            )
                            st.session_state.etsy_metadata_cartoon = etsy_metadata_cartoon
                
                # Gerçekçi görsel oluştur
                with st.spinner("Gerçekçi tarzda görsel oluşturuluyor..."):
                    realistic_image_url, realistic_error = generate_image(st.session_state.realistic_prompt)
                    st.session_state.realistic_image = realistic_image_url
                    st.session_state.realistic_error = realistic_error
                    
                    if not realistic_error:
                        with st.spinner("Gerçekçi görsel için Etsy metadata oluşturuluyor..."):
                            etsy_metadata_realistic = generate_etsy_metadata(
                                st.session_state.realistic_prompt, 
                                fikir, 
                                nis_kategori
                            )
                            st.session_state.etsy_metadata_realistic = etsy_metadata_realistic
            else:
                st.warning("Önce promptları oluşturmalısınız.")
    
    with col2:
        st.subheader("Sonuçlar")
        
        # Cartoon Sonuçları
        if "cartoon_prompt" in st.session_state:
            st.markdown("### Cartoon Tarzı")
            st.markdown("#### Oluşturulan Cartoon Prompt:")
            st.code(st.session_state.cartoon_prompt)
            
            if "cartoon_image" in st.session_state and st.session_state.cartoon_image:
                st.markdown("#### Cartoon Tarzı Görsel:")
                st.image(st.session_state.cartoon_image, use_column_width=True)
                
                # İndirme butonu
                st.markdown(f"[Cartoon Görseli İndir]({st.session_state.cartoon_image})")
            
            if "cartoon_error" in st.session_state and st.session_state.cartoon_error:
                st.error(f"Cartoon görsel oluşturma hatası: {st.session_state.cartoon_error}")
            
            if "etsy_metadata_cartoon" in st.session_state and st.session_state.etsy_metadata_cartoon:
                st.markdown("#### Cartoon için Etsy Metadata:")
                st.text_area("Cartoon Etsy Bilgileri", st.session_state.etsy_metadata_cartoon, height=200)
                
                # Metadata indirme butonu
                timestamp = int(time.time())
                filename = f"cartoon_etsy_metadata_{timestamp}.txt"
                st.markdown(
                    get_download_link(st.session_state.etsy_metadata_cartoon, filename, "Cartoon Etsy Metadatasını İndir"),
                    unsafe_allow_html=True
                )
        
        # Gerçekçi Sonuçlar
        if "realistic_prompt" in st.session_state:
            st.markdown("### Gerçekçi Tarz")
            st.markdown("#### Oluşturulan Gerçekçi Prompt:")
            st.code(st.session_state.realistic_prompt)
            
            if "realistic_image" in st.session_state and st.session_state.realistic_image:
                st.markdown("#### Gerçekçi Görsel:")
                st.image(st.session_state.realistic_image, use_column_width=True)
                
                # İndirme butonu
                st.markdown(f"[Gerçekçi Görseli İndir]({st.session_state.realistic_image})")
            
            if "realistic_error" in st.session_state and st.session_state.realistic_error:
                st.error(f"Gerçekçi görsel oluşturma hatası: {st.session_state.realistic_error}")
            
            if "etsy_metadata_realistic" in st.session_state and st.session_state.etsy_metadata_realistic:
                st.markdown("#### Gerçekçi Görsel için Etsy Metadata:")
                st.text_area("Gerçekçi Etsy Bilgileri", st.session_state.etsy_metadata_realistic, height=200)
                
                # Metadata indirme butonu
                timestamp = int(time.time())
                filename = f"realistic_etsy_metadata_{timestamp}.txt"
                st.markdown(
                    get_download_link(st.session_state.etsy_metadata_realistic, filename, "Gerçekçi Etsy Metadatasını İndir"),
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    main()
