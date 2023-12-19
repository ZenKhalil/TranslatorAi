import os
import openai
import pysubs2
from flask import Flask, request, render_template, send_file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_dialogues(subs):
    return [line for line in subs if not line.is_comment and line.style != "Default"]

def create_contextual_groups(dialogues, max_group_size=5):
    groups = []
    current_group = []
    for line in dialogues:
        current_group.append(line)
        if len(current_group) >= max_group_size:
            groups.append(current_group)
            current_group = []
    if current_group:
        groups.append(current_group)
    return groups

def translate_group(group, target_language):
    combined_text = " || ".join([line.text for line in group])
    prompt = f"Translate the following text to {target_language}:\n\n{combined_text}"
    max_tokens = 1049 - len(prompt.split())
    if max_tokens < 100:
        return None
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.5,
            stop=None,
        )
        return response.choices[0].text.strip().split(" || ")
    except openai.error.OpenAIError as e:
        print(f"OpenAI Error: {e}")
        return None

def reinsert_translations(subs, translated_groups):
    line_index = 0
    for group in translated_groups:
        if group is None:
            continue
        for translated_line in group:
            subs[line_index].text = translated_line
            line_index += 1

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    target_language = request.form['language']
    file_path = os.path.join('uploads', uploaded_file.filename)
    uploaded_file.save(file_path)

    if uploaded_file.filename.endswith('.ass'):
        subs = pysubs2.load(file_path)
        dialogues = extract_dialogues(subs)
        groups = create_contextual_groups(dialogues)
        translated_groups = [translate_group(group, target_language) for group in groups]
        reinsert_translations(subs, translated_groups)
        new_file_path = file_path[:-4] + f"_{target_language}.ass"
        subs.save(new_file_path)
        return send_file(new_file_path, as_attachment=True)
    else:
        return "Unsupported file format", 400

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
