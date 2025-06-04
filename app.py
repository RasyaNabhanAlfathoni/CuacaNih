import customtkinter as ctk
import requests
import threading
import time
from PIL import Image, ImageTk
from geopy.geocoders import Nominatim
import geocoder
from io import BytesIO
import os

# ========== SETUP ==========
API_KEY = "<your_openweathermap_api>"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"

# List of major Indonesian cities
indonesian_cities = [
    "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
    "Makassar", "Palembang", "Depok", "Tangerang", "Bekasi",
    "Bogor", "Malang", "Yogyakarta", "Denpasar", "Surakarta",
    "Bandar Lampung", "Padang", "Pekanbaru", "Balikpapan",
    "Samarinda", "Pontianak", "Manado", "Mataram", "Jayapura",
    "Banjarmasin", "Cimahi", "Jambi", "Serang", "Batu",
    "Probolinggo", "Sukabumi", "Tasikmalaya", "Palu", "Ambon",
    "Kupang", "Pekalongan", "Cirebon", "Banda Aceh", "Binjai",
    "Tebing Tinggi", "Pematang Siantar", "Bukittinggi", "Padang Panjang",
    "Payakumbuh", "Pariaman", "Solok", "Sawahlunto", "Padang Sidempuan",
    "Sibolga", "Tanjung Balai", "Tanjung Pinang", "Batam", "Ternate",
    "Tidore", "Sorong", "Manokwari", "Fakfak", "Kaimana"
]

ctk.set_appearance_mode("system")  # Default to system appearance
ctk.set_default_color_theme("dark-blue")  # You can try "dark-blue" for a more elegant look

app = ctk.CTk()
app.title("CuacaNih ⛅")
app.geometry("500x700")  # Slightly taller for better spacing
app.resizable(False, False)

# ========== VARIABLES ==========
dark_mode = ctk.BooleanVar(value=False)
weather_icons = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "⛅",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌦️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️"
}

# ========== FUNCTIONS ==========
def toggle_dark_mode():
    current = ctk.get_appearance_mode()
    new_mode = "dark" if current == "light" else "light"
    ctk.set_appearance_mode(new_mode)
    dark_mode.set(new_mode == "dark")
    # Update gradient frame color based on mode
    if new_mode == "dark":
        header_frame.configure(fg_color=("#1a2a3a", "#2a3a4a"))
        search_frame.configure(fg_color=("#1a2a3a", "#2a3a4a"))
        output_frame.configure(fg_color=("#1a2a3a", "#2a3a4a"))
    else:
        header_frame.configure(fg_color=("#f0f8ff", "#e6f2ff"))
        search_frame.configure(fg_color=("#f0f8ff", "#e6f2ff"))
        output_frame.configure(fg_color=("#f0f8ff", "#e6f2ff"))

def get_location():
    progress.configure(text="Mendeteksi lokasi...", text_color="#4a90e2")
    try:
        g = geocoder.ip('me')
        if g.ok:
            geolocator = Nominatim(user_agent="weather_app")
            location = geolocator.reverse(f"{g.latlng[0]}, {g.latlng[1]}")
            city = location.raw.get('address', {}).get('city', '')
            if city:
                city_dropdown.set(city)
                fetch_weather()
            else:
                progress.configure(text="", text_color="red")
                output_label.configure(text="⚠️ Tidak dapat menemukan nama kota dari lokasi saat ini")
        else:
            progress.configure(text="", text_color="red")
            output_label.configure(text="⚠️ Gagal mendeteksi lokasi")
    except Exception as e:
        progress.configure(text="", text_color="red")
        output_label.configure(text=f"⚠️ Error lokasi: {e}")

def animate_loading():
    dots = ["", ".", "..", "..."]
    for i in range(12):  # Longer animation for better UX
        progress.configure(text="Mengambil data" + dots[i % 4], text_color="#4a90e2")
        time.sleep(0.25)

def fetch_weather():
    city = city_dropdown.get()
    if not city or city == "Pilih kota":
        output_label.configure(text="⚠️ Pilih nama kota!", text_color="red")
        return

    output_label.configure(text="")
    threading.Thread(target=animate_loading).start()

    try:
        # First get coordinates for the city
        geo_params = {
            "q": f"{city},ID",  # ID for Indonesia country code
            "limit": 1,
            "appid": API_KEY
        }
        geo_response = requests.get(GEOCODING_URL, params=geo_params)
        geo_data = geo_response.json()
        
        if not geo_data:
            progress.configure(text="", text_color="red")
            output_label.configure(text=f"❌ Kota '{city}' tidak ditemukan.", text_color="red")
            return
            
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        
        # Then get weather data
        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric",
            "lang": "id"
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if response.status_code == 200:
            suhu = data['main']['temp']
            feels_like = data['main']['feels_like']
            cuaca = data['weather'][0]['description']
            kelembapan = data['main']['humidity']
            angin = data['wind']['speed']
            pressure = data['main']['pressure']
            icon_code = data['weather'][0]['icon']
            weather_icon = weather_icons.get(icon_code, "🌫️")
            
            # Try to load animated icon
            try:
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"  # Higher resolution
                icon_response = requests.get(icon_url)
                icon_img = Image.open(BytesIO(icon_response.content))
                icon_img = icon_img.resize((120, 120), Image.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_img)
                icon_label.configure(image=icon_photo)
                icon_label.image = icon_photo  # Keep reference
            except:
                icon_label.configure(text=weather_icon, font=ctk.CTkFont(size=64))  # Larger emoji
            
            # Format with better visual hierarchy
            result = f"""
📍 {city.title()}
            
🌡️ {suhu}°C (Terasa seperti: {feels_like}°C)
            
{cuaca.title()}
            
💧 Kelembapan: {kelembapan}%
💨 Angin: {angin} m/s
📊 Tekanan: {pressure} hPa
"""
            progress.configure(text="", text_color="#4a90e2")
            output_label.configure(text=result, text_color=("#333333", "#f0f0f0"))
            
            # Update time display
            time_str = time.strftime("%H:%M:%S")
            time_label.configure(text=f"Terakhir diperbarui: {time_str}")
        else:
            progress.configure(text="", text_color="red")
            output_label.configure(text=f"❌ Error: {data.get('message', 'Unknown error')}", text_color="red")
    except Exception as e:
        progress.configure(text="", text_color="red")
        output_label.configure(text=f"⚠️ Error: {str(e)}", text_color="red")

def search_weather_thread():
    threading.Thread(target=fetch_weather).start()

# ========== WIDGETS ==========
# Main container for better padding
main_container = ctk.CTkFrame(app, fg_color="transparent")
main_container.pack(pady=20, padx=20, fill="both", expand=True)

# Header Frame with gradient background
header_frame = ctk.CTkFrame(main_container, corner_radius=15, 
                           fg_color=("#f0f8ff", "#e6f2ff"),  # Light blue gradient
                           height=80)
header_frame.pack(fill="x", pady=(0, 15))

title = ctk.CTkLabel(header_frame, text="CuacaNih ⛅", 
                    font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"),
                    text_color=("#2a5885", "#e6f2ff"))
title.pack(side="left", padx=20, pady=10)

# Dark mode toggle with text instead of icon
dark_mode_btn = ctk.CTkButton(header_frame, text="☀️/🌙", width=60, height=40,
                             command=toggle_dark_mode, 
                             fg_color="transparent",
                             hover_color=("#d1e3ff", "#3a4a5a"),
                             font=ctk.CTkFont(size=16))
dark_mode_btn.pack(side="right", padx=15)

# Search Frame with subtle background
search_frame = ctk.CTkFrame(main_container, corner_radius=15,
                           fg_color=("#f0f8ff", "#e6f2ff"),
                           height=100)
search_frame.pack(fill="x", pady=(0, 15))

# City dropdown with modern styling
city_dropdown = ctk.CTkComboBox(search_frame, values=indonesian_cities,
                               width=300, height=45,
                               font=ctk.CTkFont(size=16),
                               dropdown_font=ctk.CTkFont(size=14),
                               corner_radius=10,
                               button_color="#4a90e2",
                               border_color="#4a90e2",
                               dropdown_fg_color=("#ffffff", "#2b2b2b"))
city_dropdown.pack(pady=15, padx=15, side="left", expand=True)
city_dropdown.set("Pilih kota")

# Search button with modern styling
search_btn = ctk.CTkButton(main_container, text="Cari Cuaca", 
                          command=search_weather_thread, 
                          width=200, height=45, 
                          corner_radius=10,
                          font=ctk.CTkFont(size=16, weight="bold"),
                          fg_color="#4a90e2",
                          hover_color="#3a80d2",
                          border_width=0)
search_btn.pack(pady=(0, 15))

# Weather Icon with circular frame
icon_frame = ctk.CTkFrame(main_container, width=130, height=130, 
                         corner_radius=65, 
                         fg_color=("#e6f2ff", "#2a3a4a"))
icon_frame.pack(pady=(10, 5))
icon_frame.pack_propagate(False)
icon_label = ctk.CTkLabel(icon_frame, text="", font=ctk.CTkFont(size=64))
icon_label.pack(expand=True)

# Time label
time_label = ctk.CTkLabel(main_container, text="", 
                         font=ctk.CTkFont(size=12),
                         text_color="gray")
time_label.pack()

# Output Frame with card-like design
output_frame = ctk.CTkFrame(main_container, corner_radius=15,
                           fg_color=("#f0f8ff", "#e6f2ff"))
output_frame.pack(fill="both", expand=True, pady=(10, 0))

output_label = ctk.CTkLabel(output_frame, text="", 
                           font=ctk.CTkFont(size=18, family="Segoe UI"), 
                           justify="left", 
                           wraplength=400,
                           padx=20, pady=20)
output_label.pack(expand=True, fill="both")

progress = ctk.CTkLabel(main_container, text="", 
                       font=ctk.CTkFont(size=14, slant="italic"),
                       text_color="#4a90e2")
progress.pack(pady=(10, 0))

footer = ctk.CTkLabel(app, text="Powered by OpenWeatherMap", 
                     font=ctk.CTkFont(size=10), 
                     text_color="gray")
footer.pack(side="bottom", pady=10)

# Initial UI update
toggle_dark_mode()

app.mainloop()