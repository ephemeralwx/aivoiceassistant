import os
import pvleopard as pvleopard
import pvporcupine
import pyaudio
import struct
import wave
import openai
import pyttsx3
import io

porcupine = pvporcupine.create(
    access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==',
    keywords=['jarvis']
)

leopard = pvleopard.create(access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==')

openai.api_key = 'your_openai_key'

engine = pyttsx3.init()
engine.say("Hello, I'm Jarvis, your personal assistant. Say my name and ask me anything:")
engine.runAndWait()

audio = pyaudio.PyAudio()
stream = audio.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length * 2,
)

def record_audio(duration):
    frames = []

    for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * duration)):
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        frames.append(audio_data)

    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(porcupine.sample_rate)
        wf.writeframes(b''.join(frames))

    return audio_buffer

print("Listening for keywords...")
try:
    while True:
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_data)

        keyword_index = porcupine.process(audio_frame)

        if keyword_index == 0:
            print("Keyword detected! Recording speech...")
            duration_seconds = 5
            audio_buffer = record_audio(duration_seconds)

            print("Transcribing speech...")
            audio_buffer.seek(0)  # Reset buffer position to beginning
            transcript, words = leopard.process_file(audio_buffer)
            print("Transcript:", transcript)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "assistant",
                    "content": ("Formulate a very short reply for the question. Here is the question:"+transcript)
                }],
                temperature=0.6,
            )

            print(response.choices[0].message.content)
            pyttsx3.speak(response.choices[0].message.content)

finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()
    porcupine.delete()
