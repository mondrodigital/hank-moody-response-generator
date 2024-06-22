from flask import Flask, request, render_template, redirect, url_for
import openai
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

# Ensure you have Tesseract installed and its path is configured correctly
# pytesseract.pytesseract.tesseract_cmd = r'path_to_tesseract_executable'

# Read OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text

# Function to get a Hank Moody response from OpenAI's GPT-4
def get_hank_moody_response(conversation_texts):
    openai.api_key = OPENAI_API_KEY

    conversation_text = ' '.join(conversation_texts)
    system_message = {
        "role": "system",
        "content": "You are Hank Moody from the TV show Californication. Hank is witty, charming, and often sarcastic. His responses are short, playful, and always lead the conversation forward. He should address the girl when it makes sense, but always lead the conversation, making her try to catch up. Never write more than she does; write the same amount or less."
    }

    user_message = {
        "role": "user",
        "content": f"Girl: {conversation_text}"
    }

    messages = [system_message, user_message]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=60,  # Adjusted to allow for appropriate length
        temperature=0.7
    )

    response_text = response.choices[0].message['content'].strip()
    response_length = len(response_text.split())

    girl_message_length = len(conversation_text.split())

    if response_length > girl_message_length:
        response_text = ' '.join(response_text.split()[:girl_message_length])

    return response_text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'images' in request.files:
            files = request.files.getlist('images')
            if len(files) > 5:
                return redirect(request.url)

            conversation_texts = []
            image_urls = []

            for file in files:
                if file.filename == '':
                    continue
                if file:
                    filename = file.filename
                    file_path = os.path.join('static/uploads', filename)
                    file.save(file_path)
                    conversation_text = extract_text_from_image(file_path)
                    conversation_texts.append(conversation_text)
                    image_urls.append(url_for('static', filename=f'uploads/{filename}'))

            if conversation_texts:
                response = get_hank_moody_response(conversation_texts)
                return render_template('index.html', response=response, image_urls=image_urls)
        elif 'existing_image_urls' in request.form:
            image_urls = request.form.getlist('existing_image_urls')
            conversation_texts = [extract_text_from_image(os.path.join('static', 'uploads', url.split('/')[-1])) for url in image_urls]

            if conversation_texts:
                response = get_hank_moody_response(conversation_texts)
                return render_template('index.html', response=response, image_urls=image_urls)

    return render_template('index.html', response=None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
