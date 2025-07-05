from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session
import os, json, pandas as pd, editdistance, re, cv2, zipfile, uuid, pickle
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'pages')
CROPPED_FOLDER = os.path.join(UPLOAD_FOLDER, 'cropped')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(CROPPED_FOLDER, exist_ok=True)

# --- Helpers ---
def contains_telugu_chars(word):
    return any('ఀ' <= ch <= '౿' for ch in word)

def strip_specials(word):
    match_prefix = re.match(r'^[^ఁ-ౖౠ-౿ఀ-౿]+', word)
    match_suffix = re.search(r'[^ఁ-ౖౠ-౿ఀ-౿]+$', word)
    start = match_prefix.group() if match_prefix else ''
    end = match_suffix.group() if match_suffix else ''
    core = word[len(start): len(word) - len(end)] if end else word[len(start):]
    return start, core, end

def read_dictionary(dict_path):
    df = pd.read_csv(dict_path, sep="\t", header=None, names=["word", "frequency"])
    df = df[df["word"].apply(contains_telugu_chars)]
    return dict(zip(df["word"], df["frequency"]))

def parse_json_by_page(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    page_data = {}
    for idx, (fname, details) in enumerate(data.items()):
        match = re.search(r'_(\d{6})_', fname)
        if not match:
            continue
        page_num = match.group(1)
        if page_num not in page_data:
            page_data[page_num] = []
        entry = (idx, fname, details['pred'], float(details['word_prob']), details['coordinates'])
        page_data[page_num].append(entry)
    return page_data

def find_image_file(folder, page_id):
    for root, dirs, files in os.walk(folder):
        for f in files:
            if page_id in f:
                return os.path.join(root, f)
    return None

def post_process_and_crop(entries, dictionary, image_path, dist_thresh, prob_thresh):
    dict_words = list(dictionary.keys())
    img = cv2.imread(image_path)
    rows = []
    summary = {"total": 0, "corrected": 0, "valid": 0, "skipped": 0}

    for idx, fname, pred, prob, coords in entries:
        summary["total"] += 1
        start, core, end = strip_specials(pred)

        if not contains_telugu_chars(pred):
            status = "skipped"
            summary["skipped"] += 1
            post = pred
            image_name = None
        elif core in dictionary or prob > prob_thresh:
            post = pred
            status = "valid"
            summary["valid"] += 1
            image_name = None
        else:
            distances = [(w, editdistance.eval(core, w)) for w in dict_words]
            min_dist = min(d[1] for d in distances)
            tied = [w for w, d in distances if d == min_dist]
            if min_dist > dist_thresh or not tied:
                post = pred
                status = "valid"
                summary["valid"] += 1
                image_name = None
            else:
                best = max(tied, key=lambda w: dictionary.get(w, 0))
                post = start + best + end
                status = "corrected"
                summary["corrected"] += 1
                x, y, w, h = coords
                cropped = img[y:y+h, x:x+w]
                image_name = f"{fname.replace('/', '_')}.png"
                cv2.imwrite(os.path.join(CROPPED_FOLDER, image_name), cropped)

        rows.append((image_name, pred, post, prob, status))
    return rows, summary

@app.route('/')
def index():
    return render_template_string('''
    <html><head><title>OCR Post-Processing</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script>
    function showSpinner() {
        document.getElementById('spinner').style.display = 'inline-block';
        document.getElementById('form').submit();
    }
    </script>
    </head><body class="bg-light">
    <div class="container py-5">
        <h2 class="text-center mb-4 text-primary">📜 Telugu OCR Correction Tool</h2>
        <form id="form" method="POST" action="/upload" enctype="multipart/form-data" class="bg-white p-4 rounded shadow">
            <div class="mb-3">
                <label>OCR JSON</label>
                <input type="file" name="json_file" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>All Page Images (.zip)</label>
                <input type="file" name="images_zip" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>Dictionary TSV</label>
                <input type="file" name="dict_file" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>Edit Distance Threshold</label>
                <input type="text" name="edit_dist_threshold" class="form-control" value="3">
            </div>
            <div class="mb-3">
                <label>Probability Threshold</label>
                <input type="text" name="prob_threshold" class="form-control" value="0.90">
            </div>
            <button type="button" class="btn btn-primary w-100" onclick="showSpinner()">🚀 Upload and Start</button>
            <div class="d-flex justify-content-center mt-3">
                <div id="spinner" class="spinner-border text-primary" role="status" style="display:none">
                    <span class="visually-hidden">Processing...</span>
                </div>
            </div>
        </form></div></body></html>
    ''')

@app.route('/upload', methods=['POST'])
def upload():
    json_file = request.files['json_file']
    images_zip = request.files['images_zip']
    dict_file = request.files['dict_file']

    json_path = os.path.join(UPLOAD_FOLDER, secure_filename(json_file.filename))
    zip_path = os.path.join(UPLOAD_FOLDER, secure_filename(images_zip.filename))
    dict_path = os.path.join(UPLOAD_FOLDER, secure_filename(dict_file.filename))

    json_file.save(json_path)
    images_zip.save(zip_path)
    dict_file.save(dict_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(IMAGE_FOLDER)

    page_data = parse_json_by_page(json_path)
    session_id = str(uuid.uuid4())
    session_file = os.path.join(UPLOAD_FOLDER, f'session_{session_id}.pkl')
    with open(session_file, 'wb') as f:
        pickle.dump(page_data, f)

    session['json_path'] = json_path
    session['dict_path'] = dict_path
    session['pages'] = sorted(page_data.keys())
    session['session_id'] = session_id
    return redirect(url_for('process_page', page=0))

@app.route('/uploads/cropped/<path:filename>')
def serve_cropped(filename):
    return send_from_directory(CROPPED_FOLDER, filename)

@app.route('/download_page/<page_id>')
def download_page_csv(page_id):
    filename = f"output_page_{page_id}.csv"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    return "File not found.", 404

@app.route('/process_page/<int:page>')
def process_page(page):
    page_keys = session.get('pages', [])
    if page >= len(page_keys):
        return "All pages processed."

    page_id = page_keys[page]
    session_id = session.get('session_id')
    session_file = os.path.join(UPLOAD_FOLDER, f'session_{session_id}.pkl')
    if not os.path.exists(session_file):
        return "Session data not found."

    with open(session_file, 'rb') as f:
        entries_by_page = pickle.load(f)

    entries = entries_by_page[page_id]
    dict_path = session['dict_path']
    dictionary = read_dictionary(dict_path)

    image_path = find_image_file(IMAGE_FOLDER, page_id)
    if not image_path:
        return f"Image for page {page_id} not found."

    dist_thresh = 3
    prob_thresh = 0.90
    rows, summary = post_process_and_crop(entries, dictionary, image_path, dist_thresh, prob_thresh)

    # Save to CSV for current page
    page_csv_path = os.path.join(UPLOAD_FOLDER, f"output_page_{page_id}.csv")
    df = pd.DataFrame(rows, columns=["Image", "Prediction", "Post-Processed", "Probability", "Status"])
    df.to_csv(page_csv_path, index=False)

    next_page = page + 1
    prev_page = page - 1 if page > 0 else None
    return render_template_string('''
    <html><head><title>Results</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script>
    function showSpinnerAndNavigate(href) {
        document.getElementById('nextspinner').style.display = 'inline-block';
        window.location.href = href;
    }
    </script>
    <style>
        img.thumb {
            height: 40px;
            padding: 1px;
            border: 2px solid red;
            background-color: white;
        }
    </style>
    </head><body class="bg-light">
    <div class="container py-4">
        <h3 class="mb-4 text-center text-success">🧾 OCR Correction Results — Page {{ page_id }}</h3>
        <table class="table table-bordered">
            <thead class="table-primary">
                <tr><th>Image</th><th>Prediction</th><th>Post-Processed</th><th>Probability</th><th>Status</th></tr>
            </thead>
            <tbody>
                {% for img, pred, post, prob, status in rows %}
                <tr>
                    <td>{% if img %}<img src="/uploads/cropped/{{ img }}" class="thumb">{% else %}-{% endif %}</td>
                    <td>{{ pred }}</td>
                    <td>{{ post }}</td>
                    <td>{{ "%.6f"|format(prob) }}</td>
                    <td>{{ status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="alert alert-info">
            <p>Total: {{ summary.total }}, Corrected: {{ summary.corrected }}, Valid: {{ summary.valid }}, Skipped: {{ summary.skipped }}</p>
        </div>
        <div class="d-flex justify-content-between align-items-center">
            <a href="/download_page/{{ page_id }}" class="btn btn-outline-primary">⬇️ Download This Page's Output</a>
            <div>
                {% if prev_page is not none %}
                    <a href="/process_page/{{ prev_page }}" class="btn btn-secondary me-2">⬅️ Previous Page</a>
                {% endif %}
                {% if next_page < pages|length %}
                    <button class="btn btn-success" onclick="showSpinnerAndNavigate('/process_page/{{ next_page }}')">➡️ Process Next Page</button>
                    <div id="nextspinner" class="spinner-border text-success ms-2" role="status" style="display:none">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                {% endif %}
            </div>
        </div>
    </div></body></html>
    ''', rows=rows, summary=summary, page_id=page_id, next_page=next_page, prev_page=prev_page, pages=page_keys)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
