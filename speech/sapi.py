import threading

import pythoncom
import win32com.client


def speak(text: str) -> None:
    if not text:
        return

    def run() -> None:
        pythoncom.CoInitialize()
        speaker = win32com.client.Dispatch('SAPI.SpVoice')
        speaker.Speak(text)
        pythoncom.CoUninitialize()

    threading.Thread(target=run, daemon=True).start()
