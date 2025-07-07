# 📝 Telugu OCR Post-Processing Tool (Without Ground Truth)

This web app processes raw Telugu OCR output without needing ground truth. It corrects low-confidence or invalid Telugu words using a frequency-based dictionary and edit distance logic.

🔗 **Live Demo**:  
👉 [https://telugu-ocr-postprocessing-withoutgt.onrender.com](https://telugu-ocr-postprocessing-withoutgt.onrender.com)

---

## 🎥 Setup Tutorial (📽️ Video Guide)

▶️ [Watch the tutorial video on Google Drive](https://drive.google.com/file/d/1mlWLx0e1LPqfl3JSUh4gt2AhdY4W6wY3/view?usp=sharing)

> 📌 You can stream the video online without downloading.

---

## ✅ Features

- Automatically separates valid vs. invalid Telugu words
- Uses edit distance and word frequency to correct misspellings
- Summarizes how many words were corrected, skipped, or marked valid
- Outputs a downloadable `.txt` file with corrections and status

---

## 📂 Input Format

To use the **Telugu OCR Correction Tool**, upload the following files through the interface:

### 1. OCR JSON File  
**(e.g., `input_1.json`)**  
A JSON file containing OCR results. Each entry includes:
- Predicted word (`pred`)
- Confidence score (`word_prob`)
- Bounding box coordinates (`coordinates`)
- Line number (`line_number`)

**Example:**
```json
{
  "0a0da77d-ffe9-486d-b7f1-6467421a73e2_000001_word_1.jpg": {
    "pred": "ఊహించని",
    "word_prob": 0.99918133,
    "coordinates": [726, 737, 478, 115],
    "line_number": 1
  },
  "0a0da77d-ffe9-486d-b7f1-6467421a73e2_000001_word_10.jpg": {
    "pred": "అతడిలో",
    "word_prob": 0.9928844,
    "coordinates": [352, 1170, 227, 80],
    "line_number": 5
  }
}

### 2. Page Images (ZIP) (e.g., `inputimages_1.zip`)

A ZIP archive containing all input page images. The filenames in this archive should match the keys in the OCR JSON file. These images are used to crop and display word-level image regions for manual verification.


### 3. Telugu Dictionary File (e.g., `combined_telugu_dictionary.tsv`)

A TSV (tab-separated) file with two columns:

word frequency


**Example:**

మనము 1532

తెలుగు 5021

## 🖨️ Output Format

The app provides a downloadable file with the following columns:

Prediction PostProcessed Probability CorrectionStatus


At the end of the file, a summary is included:

======== SUMMARY ========

✅ Total entries: 2000

🟦 Corrected Telugu entries: 321

🟢 Valid Telugu entries: 1421

⚠️ Skipped impure/invalid entries: 258


---

## ⚙️ How It Works

- Words that are not in the dictionary and have low confidence are corrected.
- Correction is based on **minimum edit distance** and **maximum frequency**.
- High-confidence words or those with non-Telugu characters are left unchanged or skipped.

---

## 🧰 Built With

- Flask
- Bootstrap (for frontend)
- Pandas
- editdistance (library)

---

## 👩‍💻 Author

**Likitha Bhavana**  
GitHub: [@likitha-b-1120](https://github.com/likitha-b-1120)

---

## 🌐 Hosted on

[Render](https://render.com)
