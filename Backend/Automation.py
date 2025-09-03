# Import required libraries
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import pyautogui
import time
import pyttsx3
import send2trash
import win32gui
import win32process
import win32con

# Text-to-speech engine setup
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

def DeleteFile(file_path, permanent=False):
    """Delete a file with confirmation"""
    try:
        if not os.path.exists(file_path):
            speak(f"File {file_path} not found")
            return False
        
        speak(f"Do you want to delete {os.path.basename(file_path)}?")
        from Backend.SpeechToText import SpeechRecognition
        confirmation = SpeechRecognition().lower()
        
        # Check for affirmative responses
        affirmative_words = ["yes", "yeah", "yep", "sure", "okay", "ok", "confirm", "delete", "do it", "go ahead"]
        if any(word in confirmation for word in affirmative_words):
            if permanent:
                os.remove(file_path)
                speak(f"Permanently deleted {os.path.basename(file_path)}")
            else:
                send2trash.send2trash(file_path)
                speak(f"Moved {os.path.basename(file_path)} to recycle bin")
            return True
        else:
            speak("Delete operation cancelled")
            return False
            
    except Exception as e:
        speak(f"Failed to delete {os.path.basename(file_path)}")
        print(f"[ERROR] {e}")
        return False

def SelectFile(file_path):
    """Select a file in Windows Explorer"""
    try:
        if os.path.exists(file_path):
            subprocess.run(['explorer', '/select,', file_path])
            speak(f"Selected {os.path.basename(file_path)} in explorer")
            return True
        else:
            speak(f"File {file_path} not found")
            return False
    except Exception as e:
        speak(f"Failed to select {os.path.basename(file_path)}")
        print(f"[ERROR] {e}")
        return False

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Define CSS classes for parsing specific elements in HTML content.
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "O5uRdC LTKOO", "vLzY6d", "webanswers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority, feel free to reach out if there's anything else I can help you with.",
    "I’m at your service for any additional questions or support you may need—don’t hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc."}]

# --------------------- Functionalities ------------------------

def GoogleSearch(Topic):
    search(Topic)
    return True

def Content(Topic):
    def OpenNotepad(File):
        subprocess.Popen(['notepad.exe', File])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        Answer = Answer.replace("</s>", "")
        messages.append({'role': 'assistant', 'content': Answer})
        return Answer

    Topic: str = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)
    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")
    return True

def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app_name):
    try:
        keyboard.press("windows")
        time.sleep(0.2)
        keyboard.release("windows")
        time.sleep(0.5)
        keyboard.write(app_name)
        time.sleep(1.5)
        keyboard.press("enter")
        time.sleep(0.2)
        keyboard.release("enter")
        time.sleep(3)
        speak(f"{app_name} has been opened")
        return True
    except Exception as e:
        speak(f"Failed to open {app_name}. It might not be installed.")
        print(f"[ERROR] {e}")
        return False

def CloseApp(app):
    """Close application using multiple methods"""
    try:
        app_closed = False
        
        # Method 1: Try taskkill with .exe extension
        result1 = os.system(f"taskkill /f /im {app}.exe")
        if result1 == 0:
            speak(f"{app} has been closed")
            return True
            
        # Method 2: Try taskkill without .exe extension
        result2 = os.system(f"taskkill /f /im {app}")
        if result2 == 0:
            speak(f"{app} has been closed")
            return True
            
        # Method 3: Try with common app names
        app_mappings = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "explorer": "explorer.exe",
            "recycle bin": "explorer.exe",
            "settings": "SystemSettings.exe",
            "control panel": "control.exe"
        }
        
        if app.lower() in app_mappings:
            result3 = os.system(f"taskkill /f /im {app_mappings[app.lower()]}")
            if result3 == 0:
                speak(f"{app} has been closed")
                return True
                
        # Method 4: Use win32gui to find and close windows
        def enum_windows_callback(hwnd, app_name):
            window_text = win32gui.GetWindowText(hwnd)
            if app_name.lower() in window_text.lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return False
            return True
            
        win32gui.EnumWindows(enum_windows_callback, app)
        speak(f"Attempted to close {app}")
        return True
        
    except:
        speak(f"Failed to close {app}")
        return False

def System(command):
    def mute():
        keyboard.press_and_release("volume mute")
        speak("System muted")
    def unmute():
        keyboard.press_and_release("volume mute")
        speak("System unmuted")
    def volume_up():
        keyboard.press_and_release("volume up")
        speak("Volume increased")
    def volume_down():
        keyboard.press_and_release("volume down")
        speak("Volume decreased")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True

# ---------------------- Answering ------------------------

def AnswerQueryWithGroq(prompt: str):
    messages.append({"role": "user", "content": f"{prompt}"})
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=SystemChatBot + messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )
    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
    response = response.replace("</s>", "")
    messages.append({'role': 'assistant', 'content': response})
    speak(response)
    print(f"[AI] {response}")
    return response

# ---------------------- Command Interpreter -----------------------

async def TranslateAndExecute(commands: list[str]):

    funcs = []

    for command in commands:

        if command.startswith("open "):
            if "open it" in command or "open file" == command:
                continue
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)

        elif command.startswith("general "):
            pass  # Reserved for later

        elif command.startswith("realtime "):
            pass  # Reserved for later

        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)

        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)

        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)

        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)
            
        elif command.startswith("delete "):
            file_path = command.removeprefix("delete ")
            fun = asyncio.to_thread(DeleteFile, file_path, permanent=False)
            funcs.append(fun)
            
        elif command.startswith("permanently delete "):
            file_path = command.removeprefix("permanently delete ")
            fun = asyncio.to_thread(DeleteFile, file_path, permanent=True)
            funcs.append(fun)
            
        elif command.startswith("select "):
            file_path = command.removeprefix("select ")
            fun = asyncio.to_thread(SelectFile, file_path)
            funcs.append(fun)

        else:
            # This is a question or general query. Use Groq to answer.
            fun = asyncio.to_thread(AnswerQueryWithGroq, command)
            funcs.append(fun)

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True
