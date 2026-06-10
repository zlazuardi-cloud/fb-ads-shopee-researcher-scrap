import streamlit as st
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Library untuk Selenium Browser Otomatis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA STREAMLIT
# ==========================================
st.set_page_config(page_title="FB Ads Scraper (Shopee)", layout="wide")

st.title("🎯 FB Ads Library Scraper Tool")
st.subheader("Riset Iklan Shopee Tanpa Token API (Metode Browser Otomatis)")
st.write("Tool ini menyortir iklan aktif dari yang terlama berdasarkan kata kunci link Shopee.")

# ==========================================
# 2. MEMBUAT FORM INPUT DI SIDEBAR (SEBELAH KIRI)
# ==========================================
st.sidebar.header("⚙️ Pengaturan Filter")
LINK_KEYWORD = st.sidebar.text_input("Kata Kunci / Link Target", value="s.shopee.co.id")
country = st.sidebar.selectbox("Negara Target", ["ID", "ALL"])

# Berapa kali browser harus scroll ke bawah untuk memuat iklan lama
scroll_count = st.sidebar.slider("Jumlah Scroll (Makin banyak = makin banyak iklan terlama didapat)", min_value=2, max_value=30, value=10)


# ==========================================
# 3. FUNGSI UTAMA SCRAPING (MENGGUNAKAN SELENIUM)
# ==========================================
# --- UPDATE KODE BAGIAN KONFIGURASI DRIVER DI APP.PY ---
def scrape_fb_ads(keyword, target_country, total_scroll):
    # Konfigurasi agar Chrome berjalan mulus di server Linux Streamlit Cloud (Headless mode)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Tambahan perintah khusus untuk Linux Debian agar jalurnya tidak bentrok
    chrome_options.binary_location = "/usr/bin/chromium"
    
    # Jalankan webdriver secara langsung mengarah ke sistem Linux
    driver = webdriver.Chrome(options=chrome_options)
    
    # Susun URL target FB Ads Library berdasarkan kata kunci
    fb_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={target_country}&q={keyword}&sort_data[direction]=desc&sort_data[mode]=relevancy_id&media_type=all"
    driver.get(fb_url)
    time.sleep(5) # Tunggu halaman loading awal sempurna
    
    # Proses Simulasi Scroll Down untuk memuat iklan-iklan yang sudah lama jalan
    for i in range(total_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2) # Jeda waktu agar konten iklan termuat sempurna
    
    # Ambil seluruh struktur HTML halaman setelah di-scroll
    page_source = driver.page_source
    driver.quit() # Tutup browser otomatis agar tidak membebani memori server
    
    # Ekstrak data menggunakan BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Mencari kotak elemen pembungkus tiap iklan di FB Ads Library
    ad_cards = soup.find_all('div', class_='_997a') 
    
    ads_list = []
    
    for card in ad_cards:
        try:
            # Ambil Nama Fanspage/Halaman
            page_name = card.find('span', class_='xt0psk2').text if card.find('span', class_='xt0psk2') else "Tanpa Nama"
            
            # Ambil Informasi Tanggal Mulai Tayang Iklan
            info_divs = card.find_all('div', class_='_997e')
            start_date_text = ""
            for div in info_divs:
                if "Started running on" in div.text or "Mulai ditayangkan" in div.text:
                    start_date_text = div.text.replace("Started running on", "").replace("Mulai ditayangkan", "").strip()
                    break
            
            # Ambil Teks/Copywriting Iklan
            ad_text_element = card.find('div', class_='_1wl*') 
            ad_text = ad_text_element.text if ad_text_element else "Tidak ada teks"
            
            # Ambil Link Detil Iklan (Snapshot)
            snapshot_link = ""
            link_element = card.find('a', href=True)
            if link_element and "ads/library" in link_element['href']:
                snapshot_link = link_element['href']
            
            # Masukkan ke list mentah
            ads_list.append({
                "Nama Halaman": page_name,
                "Tanggal Mulai": start_date_text if start_date_text else "Tidak Terdeteksi",
                "Teks Iklan": ad_text,
                "Link Detail": snapshot_link
            })
        except Exception as e:
            continue
            
    return ads_list


# ==========================================
# 4. PROSES LOGIKA UTAMA (KETIKA TOMBOL DIKLIK)
# ==========================================
if st.sidebar.button("Mulai Scraping Iklan"):
    with st.spinner("Browser otomatis sedang membuka Facebook Ads Library & memuat iklan lama... Mohon tunggu..."):
        data_iklan = scrape_fb_ads(LINK_KEYWORD, country, scroll_count)
        
        if data_iklan:
            df = pd.DataFrame(data_iklan)
            
            # Tampilkan Hasil Sukses
            st.success(f"✅ Berhasil mengikis {len(df)} iklan dari FB Ads Library!")
            
            # Tampilkan Tabel Data Ringkas
            st.write("### 📊 Hasil Data Scraping")
            st.dataframe(df[["Nama Halaman", "Tanggal Mulai", "Teks Iklan"]])
            
            # Tampilkan Detail Berbentuk Card (Expander)
            st.write("### 🔍 Detail Teks & Link Kompetitor")
            for index, row in df.iterrows():
                with st.expander(f"📌 {row['Nama Halaman']} | Info: {row['Tanggal Mulai']}"):
                    st.write("**Teks Copywriting:**")
                    st.code(row['Teks Iklan'], language="text")
                    if row['Link Detail']:
                        st.markdown(f"[🔗 Lihat Detail Iklan Asli di Facebook Ads Library]({row['Link Detail']})")
        else:
            st.error("❌ Gagal mendapatkan data atau tidak ada iklan yang termuat. Coba naikkan jumlah scroll atau periksa kata kunci Anda.")
