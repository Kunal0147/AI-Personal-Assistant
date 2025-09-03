import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from dotenv import dotenv_values
import cv2
import imageio
import socket
import os
import psutil
import shutil
import threading
import time
import pythoncom
import wmi
import requests
import datetime
import subprocess
import re

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Load environment variables
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf"{TempDirPath}\Mic.data", "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf"{TempDirPath}\Mic.data", "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}\Status.data", "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(rf"{TempDirPath}\Status.data", "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def MicButtonInitiated():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    Path = rf"{GraphicsDirPath}\{Filename}"
    return Path

def TempDirectoryPath(Filename):
    Path = rf"{TempDirPath}\{Filename}"
    return Path

def ShowTextToScreen(Text):
    with open(rf"{TempDirPath}\Responses.data", "w", encoding='utf-8') as file:
        file.write(Text)

class HomeScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#000000")
        
        # Create main container for home screen content
        self.main_container = ctk.CTkFrame(self, fg_color="#000000")
        self.main_container.pack(fill="both", expand=True)

        SIDEBAR_WIDTH = 280
        self.left_sidebar = ctk.CTkFrame(self.main_container, width=SIDEBAR_WIDTH, corner_radius=0, fg_color="#111827")
        self.left_sidebar.pack(side="left", fill="y")
        self.left_sidebar.pack_propagate(False)
        self.create_left_sidebar_widgets()

        self.right_sidebar = ctk.CTkFrame(self.main_container, width=SIDEBAR_WIDTH, corner_radius=0, fg_color="#111827")
        self.right_sidebar.pack(side="right", fill="y")
        self.right_sidebar.pack_propagate(False)
        self.create_right_sidebar_widgets()

        # Create center content area
        self.center_frame = ctk.CTkFrame(self.main_container, fg_color="#000000")
        self.center_frame.pack(side="left", fill="both", expand=True)
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        self.webcam_update()

        # Start system stats update thread
        self.update_thread = threading.Thread(target=self.update_stats, daemon=True)
        self.update_thread.start()

        # Start animation
        self.play_center_animation()

        # Initialize mic button
        self.mic_state = True
        self.setup_mic_button()
        
        # Start status update
        self.status_timer = threading.Thread(target=self.status_update_loop, daemon=True)
        self.status_timer.start()

    def setup_mic_button(self):
        mic_on_img = Image.open(os.path.join("Frontend", "Graphics", "mic_on.png"))
        mic_off_img = Image.open(os.path.join("Frontend", "Graphics", "mic_off.png"))

        mic_on_img = mic_on_img.resize((60, 60), Image.LANCZOS)
        mic_off_img = mic_off_img.resize((60, 60), Image.LANCZOS)

        self.mic_on_icon = ImageTk.PhotoImage(mic_on_img)
        self.mic_off_icon = ImageTk.PhotoImage(mic_off_img)

        # Initialize mic state based on file content
        try:
            current_status = GetMicrophoneStatus()
            self.mic_state = current_status == "True"
        except:
            self.mic_state = False
            SetMicrophoneStatus("False")
        self.mic_button = tk.Button(
            self.main_container,
            image=self.mic_on_icon if self.mic_state else self.mic_off_icon,
            bg="#000000",
            bd=0,
            activebackground="#000000",
            command=self.toggle_mic
        )
        self.mic_button.place(relx=1.0, x=-390, rely=1.0, y=-10, anchor="s")

    def toggle_mic(self):
        self.mic_state = not self.mic_state
        new_icon = self.mic_on_icon if self.mic_state else self.mic_off_icon
        self.mic_button.configure(image=new_icon)
        
        if self.mic_state:
            SetMicrophoneStatus("True")
        else:
            SetMicrophoneStatus("False")
        
        print(f"Mic state changed to: {'ON' if self.mic_state else 'OFF'}")
        print(f"File status: {GetMicrophoneStatus()}")

    def status_update_loop(self):
        while True:
            try:
                # Add status label if needed for home screen
                time.sleep(0.1)
            except Exception as e:
                print(f"Status update error: {e}")
                time.sleep(1)

    def play_center_animation(self):
        def animation_thread():
            gif_path = os.path.join("Frontend", "Graphics", "Center.gif")
            if not os.path.exists(gif_path):
                print(f"GIF not found at: {gif_path}")
                return

            gif = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(frame.copy().convert("RGBA").resize((500, 500))) for frame in ImageSequence.Iterator(gif)]

            gif_label = tk.Label(self.center_frame, bg="#000215", bd=0, highlightthickness=0)
            gif_label.place(relx=0.5, rely=0.5, anchor="center")

            def update_gif(ind=0):
                frame = frames[ind]
                gif_label.configure(image=frame)
                gif_label.image = frame
                self.after(50, update_gif, (ind + 1) % len(frames))

            update_gif()

        threading.Thread(target=animation_thread, daemon=True).start()

    def create_left_sidebar_widgets(self):
        font_title = ("Segoe UI", 16, "bold")
        font_value = ("Segoe UI", 14)

        self.status_heading = ctk.CTkLabel(self.left_sidebar, text="System Status", font=("Segoe UI", 20, "bold"))
        self.status_heading.pack(pady=(20, 10), fill="x")
        self.status_heading.configure(justify="left")

        self.cpu_label = ctk.CTkLabel(self.left_sidebar, text="CPU Usage", font=font_title)
        self.cpu_label.pack(pady=(10, 0), anchor="center", padx=10)
        self.cpu_value = ctk.CTkLabel(self.left_sidebar, text="Loading...", font=font_value)
        self.cpu_value.pack(anchor="center", padx=20)

        self.ram_label = ctk.CTkLabel(self.left_sidebar, text="RAM Usage", font=font_title)
        self.ram_label.pack(pady=(15, 0), anchor="center", padx=10)
        self.ram_value = ctk.CTkLabel(self.left_sidebar, text="Loading...", font=font_value)
        self.ram_value.pack(anchor="center", padx=20)
        self.ram_bar = ctk.CTkProgressBar(self.left_sidebar, height=10)
        self.ram_bar.pack(padx=20, fill="x")

        self.disk_label = ctk.CTkLabel(self.left_sidebar, text="Storage", font=font_title)
        self.disk_label.pack(pady=(15, 0), anchor="center", padx=10)
        self.disk_value = ctk.CTkLabel(self.left_sidebar, text="Loading...", font=font_value)
        self.disk_value.pack(anchor="center", padx=20)
        self.disk_bar = ctk.CTkProgressBar(self.left_sidebar, height=10)
        self.disk_bar.pack(padx=20, fill="x")

        self.temp_label = ctk.CTkLabel(self.left_sidebar, text="Temperature", font=font_title)
        self.temp_label.pack(pady=(15, 0), anchor="center", padx=10)
        self.temp_value = ctk.CTkLabel(self.left_sidebar, text="Loading...", font=font_value)
        self.temp_value.pack(anchor="center", padx=20)
        self.temp_bar = ctk.CTkProgressBar(self.left_sidebar, height=10)
        self.temp_bar.pack(padx=20, fill="x")

        self.power_label = ctk.CTkLabel(self.left_sidebar, text="Power", font=font_title)
        self.power_label.pack(pady=(15, 0), anchor="center", padx=10)
        self.power_value = ctk.CTkLabel(self.left_sidebar, text="Loading...", font=font_value)
        self.power_value.pack(anchor="center", padx=20)
        self.battery_bar = ctk.CTkProgressBar(self.left_sidebar, height=10)
        self.battery_bar.pack(padx=20, fill="x")

        self.env_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
        self.env_frame.pack(side="bottom", pady=15)

        self.env_label = ctk.CTkLabel(self.env_frame, text="Environment", font=font_title)
        self.env_label.pack(anchor="center")

        self.weather_row = ctk.CTkFrame(self.env_frame, fg_color="transparent")
        self.weather_row.pack(anchor="center")

        self.weather_icon_label = ctk.CTkLabel(self.weather_row, text="")
        self.weather_icon_label.pack(side="left", padx=(0, 10))

        self.weather_info_frame = ctk.CTkFrame(self.weather_row, fg_color="transparent")
        self.weather_info_frame.pack(side="left")

        self.weather_city = ctk.CTkLabel(self.weather_info_frame, text="Loading...", font=font_value)
        self.weather_city.pack(anchor="w")

        self.weather_temp = ctk.CTkLabel(self.weather_info_frame, text="", font=font_value)
        self.weather_temp.pack(anchor="w")

        self.weather_desc = ctk.CTkLabel(self.weather_info_frame, text="", font=font_value)
        self.weather_desc.pack(anchor="w")

    def create_right_sidebar_widgets(self):
        font_title = ("Segoe UI", 16, "bold")
        font_value = ("Segoe UI", 14)

        self.temporal_heading = ctk.CTkLabel(self.right_sidebar, text="Temporal Synchronization", font=("Segoe UI", 20, "bold"))
        self.temporal_heading.pack(pady=(20, 10), fill="x")
        self.temporal_heading.configure(justify="left")

        self.datetime_frame = ctk.CTkFrame(self.right_sidebar, fg_color="transparent")
        self.datetime_frame.pack(pady=(10, 20), anchor="center")

        self.time_label = ctk.CTkLabel(self.datetime_frame, text="--:--:--", font=("Segoe UI", 22, "bold"))
        self.time_label.pack()

        self.date_label = ctk.CTkLabel(self.datetime_frame, text="Loading date...", font=("Segoe UI", 14))
        self.date_label.pack()

        self.clock_thread = threading.Thread(target=self.update_clock, daemon=True)
        self.clock_thread.start()

        self.network_heading = ctk.CTkLabel(self.right_sidebar, text="Network Interface", font=("Segoe UI", 20, "bold"))
        self.network_heading.pack(pady=(20, 10), fill="x")
        self.network_heading.configure(justify="left")

        self.network_ssid_label = ctk.CTkLabel(self.right_sidebar, text="Network SSID", font=font_title)
        self.network_ssid_label.pack(pady=(5, 0), anchor="center", padx=20)
        self.network_ssid_value = ctk.CTkLabel(self.right_sidebar, text="Detecting...", font=font_value)
        self.network_ssid_value.pack(anchor="center", padx=20)

        self.network_strength_label = ctk.CTkLabel(self.right_sidebar, text="Network Strength", font=font_title)
        self.network_strength_label.pack(pady=(15, 0), anchor="center", padx=20)
        self.network_strength_value = ctk.CTkLabel(self.right_sidebar, text="Detecting...", font=font_value)
        self.network_strength_value.pack(anchor="center", padx=20)

        self.network_traffic_label = ctk.CTkLabel(self.right_sidebar, text="Network Traffic", font=font_title)
        self.network_traffic_label.pack(pady=(15, 0), anchor="center", padx=20)
        self.network_traffic_value = ctk.CTkLabel(self.right_sidebar, text="Calculating...", font=font_value)
        self.network_traffic_value.pack(anchor="center", padx=20)

        self.ip_address_label = ctk.CTkLabel(self.right_sidebar, text="IP Address", font=font_title)
        self.ip_address_label.pack(pady=(15, 0), anchor="center", padx=20)
        self.ip_address_value = ctk.CTkLabel(self.right_sidebar, text="Detecting...", font=font_value)
        self.ip_address_value.pack(anchor="center", padx=20)

        self.visual_input_heading = ctk.CTkLabel(self.right_sidebar, text="Visual Input", font=("Segoe UI", 20, "bold"))
        self.visual_input_heading.pack(pady=(80, 0), anchor="s")

        self.webcam_label = ctk.CTkLabel(self.right_sidebar, text="")
        self.webcam_label.pack(side="right", anchor="s", pady=8, padx=6)

    def webcam_update(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (340, 230))
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.webcam_label.configure(image=img)
            self.webcam_label.image = img
        self.after(30, self.webcam_update)

    def update_clock(self):
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date = now.strftime("%A, %d %B %Y")
            self.time_label.configure(text=current_time)
            self.date_label.configure(text=current_date)
            time.sleep(1)

    def update_stats(self):
        while True:
            try:
                self.cpu_value.configure(text=f"{psutil.cpu_percent()}%")

                mem = psutil.virtual_memory()
                self.ram_value.configure(text=f"{mem.used / (1024 ** 3):.1f} GB / {mem.total / (1024 ** 3):.1f} GB")
                self.ram_bar.set(mem.percent / 100)

                used, total = self.get_total_storage()
                self.disk_value.configure(text=f"{used / (1024 ** 3):.1f} GB / {total / (1024 ** 3):.1f} GB")
                self.disk_bar.set(used / total if total else 0)

                temp = self.get_cpu_temperature()
                if temp is not None:
                    self.temp_value.configure(text=f"{temp:.1f} °C")
                    self.temp_bar.set(min(temp / 100, 1.0))
                else:
                    self.temp_value.configure(text="Unavailable")
                    self.temp_bar.set(0)

                battery = psutil.sensors_battery()
                if battery:
                    status = "Charging" if battery.power_plugged else "On Battery"
                    self.power_value.configure(text=f"{status} ({battery.percent}%)")
                    self.battery_bar.set(battery.percent / 100)
                else:
                    self.power_value.configure(text="N/A")
                    self.battery_bar.set(0)

                weather = self.get_weather_info()
                if weather:
                    self.weather_city.configure(text=weather["city"])
                    self.weather_temp.configure(text=weather["temp"])
                    self.weather_desc.configure(text=weather["desc"])

                    image = Image.open(weather["icon"])
                    image = image.resize((60, 60))
                    icon_ctk = ctk.CTkImage(light_image=image, size=(60, 60))
                    self.weather_icon_label.configure(image=icon_ctk, text="")
                    self.weather_icon_label.image = icon_ctk
                else:
                    self.weather_city.configure(text="Weather Unavailable")
                    self.weather_temp.configure(text="")
                    self.weather_desc.configure(text="")
                    self.weather_icon_label.configure(image=None, text="")

                ssid = self.get_wifi_ssid()
                self.network_ssid_value.configure(text=ssid)

                strength = self.get_wifi_strength()
                self.network_strength_value.configure(text=strength)

                download_speed, upload_speed = self.get_network_speeds()
                self.network_traffic_value.configure(
                    text=f"{download_speed:.2f} MB/s ↓ | {upload_speed:.2f} MB/s ↑")

                ip_address = self.get_ip_address()
                self.ip_address_value.configure(text=ip_address)

            except Exception as e:
                print("Update error:", e)

            time.sleep(1)

    def get_ip_address(self):
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "Unavailable"

    def get_network_speeds(self):
        net1 = psutil.net_io_counters()
        time.sleep(1)
        net2 = psutil.net_io_counters()

        download_speed = (net2.bytes_recv - net1.bytes_recv) / 1024 / 1024
        upload_speed = (net2.bytes_sent - net1.bytes_sent) / 1024 / 1024
        return download_speed, upload_speed

    def get_wifi_ssid(self):
        try:
            result = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True)
            match = re.search(r"^\s*SSID\s*:\s*(.+)$", result, re.MULTILINE)
            return match.group(1).strip() if match else "Not Connected"
        except:
            return "Unavailable"

    def get_wifi_strength(self):
        try:
            result = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True)
            match = re.search(r"^\s*Signal\s*:\s*(\d+)\s*%", result, re.MULTILINE)
            return f"{match.group(1)}%" if match else "Unknown"
        except:
            return "Unavailable"

    def get_total_storage(self):
        total, used = 0, 0
        for partition in psutil.disk_partitions():
            if os.name == 'nt' and 'cdrom' in partition.opts:
                continue
            try:
                usage = shutil.disk_usage(partition.mountpoint)
                total += usage.total
                used += usage.used
            except:
                continue
        return used, total

    def get_cpu_temperature(self):
        try:
            pythoncom.CoInitialize()
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            for sensor in w.Sensor():
                if sensor.SensorType == u'Temperature' and "CPU" in sensor.Name:
                    return float(sensor.Value)
        except:
            return None

    def download_weather_icon(self, icon_id):
        icons_dir = os.path.join("Data", "Icons")
        os.makedirs(icons_dir, exist_ok=True)
        icon_path = os.path.join(icons_dir, f"{icon_id}.png")
        if not os.path.exists(icon_path):
            url = f"http://openweathermap.org/img/wn/{icon_id}@2x.png"
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
        return icon_path

    def get_weather_info(self):
        try:
            env_vars = dotenv_values(".env")
            WeatherAPIKey = env_vars.get("WeatherAPIKey")
            CITY = env_vars.get("CITY", "Delhi")

            if not WeatherAPIKey:
                return None

            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WeatherAPIKey}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                icon_id = data["weather"][0]["icon"]
                icon_path = self.download_weather_icon(icon_id)
                return {
                    "city": data["name"],
                    "temp": f"{data['main']['temp']:.1f}°C",
                    "desc": data["weather"][0]["description"].title(),
                    "icon": icon_path
                }
            return None
        except Exception as e:
            print("Weather error:", e)
            return None

class ChatScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#000000")
        
        # Initialize mic monitoring
        self.mic_monitoring = False
        self.start_mic_monitoring()
        
        # Initialize chat message tracking
        self.old_chat_message = ""
        
        # Create main layout
        self.create_chat_layout()
        
        # Start message loading timer
        self.message_timer = threading.Thread(target=self.message_update_loop, daemon=True)
        self.message_timer.start()
    
    def start_mic_monitoring(self):
        """Start monitoring the Mic.data file"""
        def monitor_mic_file():
            while True:
                try:
                    with open(TempDirectoryPath('Mic.data'), 'r', encoding='utf-8') as file:
                        status = file.read().strip()
                        
                    if status.lower() == "true" and not self.mic_monitoring:
                        self.mic_monitoring = True
                        print("[MIC] Started listening...")
                        # Trigger speech recognition here if needed
                        
                    elif status.lower() == "false" and self.mic_monitoring:
                        self.mic_monitoring = False
                        print("[MIC] Stopped listening...")
                        
                except Exception as e:
                    print(f"[MIC] Error reading Mic.data: {e}")
                
                time.sleep(0.1)  # Check every 100ms
        
        mic_thread = threading.Thread(target=monitor_mic_file, daemon=True)
        mic_thread.start()

    def create_chat_layout(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="#000000")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Chat display area
        self.chat_frame = ctk.CTkFrame(main_container, fg_color="#000000")
        self.chat_frame.pack(fill="both", expand=True)
        
        # Chat text widget with scrollbar
        self.chat_text = tk.Text(
            self.chat_frame,
            bg="#000000",
            fg="white",
            font=("Segoe UI", 13),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bd=0,
            highlightthickness=0,
            insertbackground="white"
        )
        
        # Custom scrollbar
        self.chat_scrollbar = ctk.CTkScrollbar(self.chat_frame, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.chat_scrollbar.set)
        
        # Pack chat components
        self.chat_scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        # Add GIF animation area (similar to old GUI)
        self.gif_frame = ctk.CTkFrame(main_container, fg_color="#000000", height=300)
        self.gif_frame.pack(side="bottom", fill="x", pady=(20, 0))
        self.gif_frame.pack_propagate(False)
        
        # Add Jarvis GIF
        self.add_jarvis_gif()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.gif_frame, 
            text="", 
            font=("Segoe UI", 16),
            text_color="white"
        )
        self.status_label.pack(side="bottom", pady=10)

    def add_jarvis_gif(self):
        """Add Jarvis GIF animation similar to old GUI"""
        def animation_thread():
            gif_path = os.path.join("Frontend", "Graphics", "Jarvis.gif")
            if not os.path.exists(gif_path):
                print(f"Jarvis GIF not found at: {gif_path}")
                return

            try:
                gif = Image.open(gif_path)
                frames = []
                for frame in ImageSequence.Iterator(gif):
                    # Resize to match old GUI dimensions
                    resized_frame = frame.copy().convert("RGBA").resize((480, 270))
                    frames.append(ImageTk.PhotoImage(resized_frame))

                gif_label = tk.Label(self.gif_frame, bg="#000000", bd=0, highlightthickness=0)
                gif_label.pack(side="right", anchor="se", padx=10, pady=10)

                def update_gif(ind=0):
                    if frames:  # Check if frames exist
                        frame = frames[ind]
                        gif_label.configure(image=frame)
                        gif_label.image = frame
                        self.after(100, update_gif, (ind + 1) % len(frames))

                update_gif()
            except Exception as e:
                print(f"Error loading Jarvis GIF: {e}")

        threading.Thread(target=animation_thread, daemon=True).start()

    def message_update_loop(self):
        """Continuously check for new messages and status updates"""
        while True:
            try:
                self.load_messages()
                self.update_status_display()
                time.sleep(0.05)  # Check every 50ms for responsiveness
            except Exception as e:
                print(f"Message update error: {e}")
                time.sleep(1)

    def load_messages(self):
        """Load messages from the responses file"""
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read()
                
                if messages and len(messages) > 1 and str(self.old_chat_message) != str(messages):
                    self.add_message_to_chat(messages)
                    self.old_chat_message = messages
        except Exception as e:
            print(f"Error loading messages: {e}")

    def add_message_to_chat(self, message):
        """Add a message to the chat display with proper formatting"""
        try:
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)  # Clear previous content
            
            # Format message similar to old GUI
            formatted_message = AnswerModifier(message)
            self.chat_text.insert(tk.END, formatted_message + "\n")
            
            self.chat_text.configure(state=tk.DISABLED)
            self.chat_text.see(tk.END)  # Scroll to bottom
        except Exception as e:
            print(f"Error adding message to chat: {e}")

    def update_status_display(self):
        """Update the status display"""
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                status = file.read()
                if status:
                    self.status_label.configure(text=status)
        except Exception as e:
            print(f"Error updating status: {e}")
class JarvisGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S AI")
        self.state("zoomed")
        self.minsize(800, 600)

        self.configure(fg_color="#000000")

        # Create screens
        self.home_screen = HomeScreen(self)
        self.chat_screen = ChatScreen(self)
        
        # Show home screen by default
        self.current_screen = self.home_screen
        self.home_screen.pack(fill="both", expand=True)

        # Create buttons for Home and Chat
        self.create_navigation_buttons()

    def create_navigation_buttons(self):
        # Home Button
        self.home_button = ctk.CTkButton(
            self,
            text="Home",
            command=self.show_home,
            fg_color="#000000",
            text_color="white",
            hover_color="#333333",
            width=100,
            height=40,
            corner_radius=8
        )
        self.home_button.place(relx=0.465, rely=0.05, anchor="center")  # Adjusted relx for horizontal positioning

        # Chat Button
        self.chat_button = ctk.CTkButton(
            self,
            text="Chat",
            command=self.show_chat,
            fg_color="#000000",
            text_color="white",
            hover_color="#333333",
            width=100,
            height=40,
            corner_radius=8
        )
        self.chat_button.place(relx=0.535, rely=0.05, anchor="center")  # Adjusted relx for horizontal positioning

    def show_home(self):
        """Switch to home screen"""
        if self.current_screen:
            self.current_screen.pack_forget()
        
        self.current_screen = self.home_screen
        self.home_screen.pack(fill="both", expand=True)

    def show_chat(self):
        """Switch to chat screen"""
        if self.current_screen:
            self.current_screen.pack_forget()
        
        self.current_screen = self.chat_screen
        self.chat_screen.pack(fill="both", expand=True)

def GraphicalUserInterface():
    app = JarvisGUI()
    app.mainloop()

if __name__ == "__main__":
    GraphicalUserInterface()