import numpy as np
import sounddevice as sd

def beep(freq=440, duration=0.5, volume=0.5, fs=44100):
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    waveform = volume * np.sin(2 * np.pi * freq * t)
    sd.play(waveform, fs)
    sd.wait()

# Example: play a short A4 tone
beep(440, 1)
