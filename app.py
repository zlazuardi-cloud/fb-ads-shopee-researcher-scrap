import streamlit as st
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Library untuk Selenium Browser Otomatis
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="FB Ads Scraper (Shopee)", layout="wide")

st.title("🎯 FB Ads Library Scraper Tool")
st.subheader("Riset Iklan Shopee Tanpa Token API (Metode Browser Otomatis)")

# --- SIDEBAR: KONTROL ---
st.sidebar.header("⚙️ Pengaturan Filter")
LINK_KEYWORD = st.sidebar.text_input("Kata Kunci / Link Target", value="s.shopee.co.id")
country = st.sidebar.selectbox("Negara Target", ["ID", "ALL"])

# Berapa kali browser harus scroll ke bawah untuk memuat iklan lama
scroll_count = st.sidebar.slider("Jumlah Scroll (Makin banyak = makin banyak iklan terlama didapat)", min_value=2, max_value=30, value=10)

# --- FUNGSI UTAMA SCRAPING ---
def scrape_fb_ads(keyword, target_country, total_scroll):
    # 1. Konfigurasi agar Chrome berjalan di latar belakang (Headless mode)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Setup Driver Otomatis
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 2. Susun URL target FB Ads Library berdasarkan kata kunci
    # q = kata kunci, country = negara, media_type = all (semua jenis iklan)
    fb_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={target_country}&q={keyword}&sort_data[direction]=desc&sort_data[mode]=relevancy_id&media_type=all"
    
    driver.get(fb_url)
    time.sleep(5) # Tunggu halaman loading awal sempurna
    
    # 3. Proses Simulasi Scroll Down untuk memuat iklan-iklan yang sudah lama jalan
    for i in range(total_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2) # Jeda waktu agar konten iklan termuat sempurna
    
    # 4. Ambil seluruh struktur HTML halaman setelah di-scroll
    page_source = driver.page_source
    driver.quit() # Tutup browser otomatis
    
    # 5. Ekstrak data menggunakan BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Mencari kotak elemen pembungkus tiap iklan di FB Ads Library
    ad_cards = soup.find_all('div', class_='_997a') 
    
    ads_list = []
    today = datetime.now()
    
    for card in ad_cards:
        try:
            # Ambil Nama Fanspage/Halaman
            page_name = card.find('span', class_='xt0psk2').text if card.find('span', class_='xt0psk2') else "Tanpa Nama"
            
            # Ambil Informasi Tanggal Mulai Tayang Iklan
            # Format teks di FB biasanya: "Started running on Jun 8, 2026"
            info_divs = card.find_all('div', class_='_997e')
            start_date_text = ""
            for div in info_divs:
                if "Started running on" in div.text or "Mulai ditayangkan" in div.text:
                    start_date_text = div.text.replace("Started running on", "").replace("Mulai ditayangkan", "").strip()
                    break
            
            # Ambil Teks/Copywriting Iklan
            ad_text_element = card.find('div', class_='_1wl*') # Class text iklan FB
            ad_text = ad_text_element.text if ad_text_element else "Tidak ada teks"
            
            # Ambil Link Detil Iklan (Snapshot)
            snapshot_link = ""
            link_element = card.find('a', href=True)
            if link_element and "ads/library" in link_element['href']:
                snapshot_link = link_element['href']
            
            # Masukkan ke list mentah
            ads_list.append({
                "Nama Halaman": page_name,
                "Tanggal Teks": start_date_text if start_date_text else "Tidak Terdeteksi",
                "Teks Iklan": ad_text,
                "Link Detail": snapshot_link
            })
        except Exception as e:
            continue
            
    return ads_list

# --- TOMBOL AKSI ---
if st.sidebar.button("Mulai Scraping Iklan"):
    with st.spinner("Browser otomatis sedang membuka Facebook Ads Library & memuat iklan lama... Mohon tunggu..."):
        data_iklan = scrape_fb_ads(LINK_KEYWORD, country, scroll_count)
        
        if data_iklan:
            df = pd.DataFrame(data_iklan)
            
            # Tampilkan Hasil
            st.success(f"✅ Berhasil mengikis {len(df)} iklan dari FB Ads Library!")
            
            st.write("### 📊 Hasil Data Scraping")
            st.dataframe(df)
            
            # Detail Tampilan Card
            st.write("### 🔍 Detail Teks & Link Kompetitor")
            for index, row in df.iterrows():
                with st.expander(f"📌 {row['Nama Halaman']} | Info: {row['Tanggal Teks']}"):
                    st.write("**Teks Copywriting:**")
                    st.code(row['Teks Iklan'], language="text")
                    if row['Link Detail']:
                        st.markdown(f"[🔗 Lihat Detail Iklan Asli di FB]({row['Link Detail']})")
        else:
            st.error("❌ Gagal mendapatkan data atau tidak ada iklan yang termuat. Coba naikkan jumlah scroll atau periksa kata kunci.")