from flask import Flask, request, jsonify, send_file
import threading
import os
import pvleopard as pvleopard
import pvporcupine
import pyaudio
import struct
import wave
import openai
import pyttsx3
import io

app = Flask(__name__)

porcupine = pvporcupine.create(
    access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==',
    keywords=['jarvis']
)

leopard = pvleopard.create(access_key='H8GJLYocyCtrfBQFgUXj73P71rka1Lk5LUSbfPqpQPMD1CdnwZYCeA==')
openai.api_key = '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'

audio = pyaudio.PyAudio()
stream = audio.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length * 2,
)

listening = False

def convert_text_to_audio_stream(text):
    engine = pyttsx3.init()
    audio_buffer = io.BytesIO()
    engine.save_to_file(text, audio_buffer)
    engine.runAndWait()
    audio_buffer.seek(0)
    return audio_buffer

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "Audio file is required."}), 400

    audio_file = request.files['audio']
    audio_buffer = io.BytesIO()
    audio_file.save(audio_buffer)

    transcript, words = leopard.process_file(audio_buffer)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "assistant",
            "content": ("Formulate a very short reply for the question. Here is the question:" + transcript)
        }],
        temperature=0.6,
    )

    audio_response = convert_text_to_audio_stream(response.choices[0].message.content)
    
    return send_file(
        audio_response,
        mimetype='audio/wav',
        as_attachment=True,
        attachment_filename='response.wav'
    )

@app.route('/start', methods=['POST'])
def start_listening():
    global listening
    if not listening:
        listening = True
        threading.Thread(target=listening_function).start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already running"})

@app.route('/stop', methods=['POST'])
def stop_listening():
    global listening
    listening = False
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True)
