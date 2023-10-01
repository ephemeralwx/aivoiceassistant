import os
import pvleopard as pvleopard
import pvporcupine
import pyaudio
import struct
import wave
import openai
import pyttsx3

porcupine = pvporcupine.create(
    access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==',
    keywords=['jarvis']
)

leopard = pvleopard.create(access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==')

openai.api_key = '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'

# Initialize the voice library
engine = pyttsx3.init()

# Saying some fun welcome message with instructions for the user
engine.say("Hello, I'm Jarvis, your personal assistant. Say my name and ask me anything:")
engine.runAndWait()

# Initialize PyAudio
audio = pyaudio.PyAudio()
stream = audio.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length * 2,
)

def record_audio(filename, duration):
    frames = []

    for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * duration)):
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_data)
        frames.append(audio_data)

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(porcupine.sample_rate)
        wf.writeframes(b''.join(frames))

# Main loop
print("Listening for keywords...")
try:
    while True:
        # Read audio data from the microphone
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_data)

        # Process audio frame with Porcupine
        keyword_index = porcupine.process(audio_frame)

        if keyword_index == 0:
            print("Keyword detected! Recording speech...")

            # Record speech for a fixed duration
            duration_seconds = 5
            audio_file = "recorded_audio.wav"
            record_audio(audio_file, duration_seconds)

            # Transcribe the recorded speech using Leopard
            print("Transcribing speech...")
            transcript, words = leopard.process_file(os.path.abspath(audio_file))
            print("Transcript:", transcript)

            response = openai.ChatCompletion.create(

                model="gpt-3.5-turbo",
                messages=[{"role": "assistant",
                           "content": ("Formulate a very short reply for the question. Here is the question:"+transcript)}],

                temperature=0.6,
            )

            print(response.choices[0].message.content)

            # This pretty line of the code reads openAI response
            pyttsx3.speak(response.choices[0].message.content)

            # Remove the audio file if you don't need it
            os.remove(audio_file)

finally:
    # Clean up resources
    stream.stop_stream()
    stream.close()
    audio.terminate()
    porcupine.delete()