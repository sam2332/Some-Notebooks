import keyboard
import speech_recognition as sr
import pyaudio
import io

# Callback function to handle audio frames
def callback(in_data, frame_count, time_info, status):
    audio_buffer.write(in_data)
    return (in_data, pyaudio.paContinue)

def on_key_press(e):
    global is_recording
    global audio_buffer
    if not is_recording:
        print("Start speaking...")
        is_recording = True
        audio_buffer = io.BytesIO()
        # Start the PyAudio stream
        stream.start_stream()

def on_key_release(e):
    global is_recording
    global audio_buffer
    if is_recording:
        print("Finished speaking")
        is_recording = False
        # Stop the PyAudio stream
        stream.stop_stream()
        # Use the recognizer to transcribe the audio
        audio_data = sr.AudioData(audio_buffer.getvalue(), sample_rate, sample_width)
        try:
            text = recognizer.recognize_google(audio_data)
            print("You said:", text)
        except sr.UnknownValueError:
            print("Could not understand audio")

recognizer = sr.Recognizer()
key_to_listen = 'ctrl'  # Change this key as needed

# Define recording parameters
sample_width = 2
channels = 1

# Common sample rates
sample_rates = [44100, 48000, 32000, 16000, 8000]

# Create a PyAudio instance
p = pyaudio.PyAudio()

# Get the default input device
input_device = p.get_default_input_device_info()['index']

# Determine the supported sample rate
for rate in sample_rates:
    if p.is_format_supported(rate, input_device=input_device, input_channels=channels, input_format=pyaudio.paInt16):
        sample_rate = rate
        break
else:
    print("No supported sample rate found.")
    p.terminate()
    exit()

# Open a streaming stream
stream = p.open(format=p.get_format_from_width(sample_width),
                channels=channels,
                rate=sample_rate,
                input=True,
                stream_callback=callback,
                frames_per_buffer=1024)

is_recording = False
audio_buffer = None

# Bind the key press and release events
keyboard.on_press_key(key_to_listen, on_key_press)
keyboard.on_release_key(key_to_listen, on_key_release)

# Keep the script running
keyboard.wait()

# Stop and close the PyAudio stream
stream.stop_stream()
stream.close()
p.terminate()