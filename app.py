from flask import Flask, render_template_string, request, send_file
import os
import pandas as pd
import editdistance
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

telugu_pattern = re.compile(r'^[\u0C00-\u0C7F]+$')
def is_telugu_word(word):
    return bool(telugu_pattern.fullmatch(word))

def read_dictionary(dict_path):
    df = pd.read_csv(dict_path, sep="\t", header=None, names=["word", "frequency"])
    df = df[df["word"].apply(is_telugu_word)]
    return dict(zip(df["word"], df["frequency"]))

def read_and_separate_data(input_file):
    telugu_entries, impure_entries = [], []
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'\s+', line)
            if len(parts) != 2:
                continue
            word, conf = parts
            conf = float(conf)
            if is_telugu_word(word):
                telugu_entries.append((idx, word, conf))
            else:
                impure_entries.append((idx, word, conf))
    return telugu_entries, impure_entries

def post_process_telugu(telugu_entries, dictionary, edit_dist_threshold=3, prob_threshold=0.95):
    corrected_entries, dict_words = [], list(dictionary.keys())
    for idx, word, prob in telugu_entries:
        if word in dictionary or prob > prob_threshold:
            corrected_entries.append((idx, word, word, prob))
            continue
        distances = [(w, editdistance.eval(word, w)) for w in dict_words]
        min_dist = min(d[1] for d in distances)
        tied = [w for w, d in distances if d == min_dist]
        if min_dist > edit_dist_threshold or not tied:
            corrected_entries.append((idx, word, word, prob))
        else:
            best = max(tied, key=lambda w: dictionary.get(w, 0))
            corrected_entries.append((idx, word, best, prob))
    return corrected_entries

def merge_and_write_output(output_path, corrected_telugu, impure_entries):
    all_entries = corrected_telugu + [(idx, word, word, prob) for idx, word, prob in impure_entries]
    all_entries.sort(key=lambda x: x[0])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Prediction\tPostProcessed\tProbability\tCorrectionStatus\n")
        for _, pred, post, prob in all_entries:
            status = "skipped" if not is_telugu_word(pred) else ("valid" if pred == post else "corrected")
            f.write(f"{pred}\t{post}\t{prob:.6f}\t{status}\n")
        total = len(all_entries)
        corrected = sum(1 for entry in all_entries if entry[1] != entry[2] and is_telugu_word(entry[1]))
        skipped = sum(1 for entry in all_entries if not is_telugu_word(entry[1]))
        valid = total - corrected - skipped
        f.write("\n======== SUMMARY ========\n")
        f.write(f"✅ Total entries: {total}\n")
        f.write(f"⤴️ Corrected Telugu entries: {corrected}\n")
        f.write(f"🟢 Valid Telugu entries: {valid}\n")
        f.write(f"⚠️ Skipped impure/invalid entries: {skipped}\n")

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Telugu Word Correction</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container py-5">
                <h2 class="text-center mb-4 text-primary">🧠 Telugu OCR Post-Processing Tool</h2>
                <form method="POST" action="/process" enctype="multipart/form-data" class="bg-white p-4 rounded shadow">
                    <div class="mb-3">
                        <label class="form-label">📂 OCR Output File (.txt)</label>
                        <input type="file" name="input_file" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">📖 Dictionary File (.tsv)</label>
                        <input type="file" name="dict_file" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">✂️ Edit Distance Threshold</label>
                        <input type="text" name="edit_dist_threshold" class="form-control" value="3">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">🎯 Probability Threshold</label>
                        <input type="text" name="prob_threshold" class="form-control" value="0.95">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">🚀 Process and Download Output</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route('/process', methods=['POST'])
def process():
    input_file = request.files['input_file']
    dict_file = request.files['dict_file']
    dist_threshold = int(request.form.get('edit_dist_threshold', 3))
    prob_threshold = float(request.form.get('prob_threshold', 0.95))

    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(input_file.filename))
    dict_path = os.path.join(UPLOAD_FOLDER, secure_filename(dict_file.filename))
    input_file.save(input_path)
    dict_file.save(dict_path)

    telugu_entries, impure_entries = read_and_separate_data(input_path)
    dictionary = read_dictionary(dict_path)
    corrected_telugu = post_process_telugu(telugu_entries, dictionary, dist_threshold, prob_threshold)

    output_path = os.path.join(OUTPUT_FOLDER, "final_output.txt")
    merge_and_write_output(output_path, corrected_telugu, impure_entries)

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
