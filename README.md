📝 Telugu OCR Post-Processing Tool (Without Ground Truth)
This web application provides a post-processing pipeline for Telugu OCR output without requiring ground truth data. It cleans and corrects predicted words using a frequency-based dictionary and edit distance logic.

🔗 Live App:
👉 https://telugu-ocr-postprocessing-withoutgt.onrender.com

💡 Features
✅ Automatically separates valid vs. invalid Telugu words

🔍 Uses edit distance and word frequency to correct misspellings

📊 Summarizes how many words were corrected, skipped, or left valid

💾 Outputs a downloadable .txt file with corrections and statuses

📂 Input Format
You need to upload two .txt files:

OCR Output File (e.g., ocr_input.txt)

Format: predicted_word <tab or space> confidence_score

Example:

Copy
Edit
మనము 0.92  
తెనుగు 0.85  
Telugu Dictionary File (TSV format, e.g., combined_telugu_dictionary.tsv)

Format: word <tab> frequency

Example:

yaml
Copy
Edit
మనము	1532  
తెలుగు	5021  
📤 Output Format
The app provides a downloadable .txt file with columns:

mathematica
Copy
Edit
Prediction	PostProcessed	Probability	CorrectionStatus
And a summary at the end:

yaml
Copy
Edit
======== SUMMARY ========
✅ Total entries: 2000
⤴️ Corrected Telugu entries: 321
🟢 Valid Telugu entries: 1421
⚠️ Skipped impure/invalid entries: 258
🧪 How It Works
Words not in the dictionary and below confidence threshold are corrected.

Correction is based on edit distance and maximum frequency match.

Words with high confidence or non-Telugu patterns are left unchanged or skipped.

🚀 Deployment Info
Built with: Flask, Bootstrap, Pandas, editdistance

Hosted on: Render

👩‍💻 Author
Likitha Bhavana
GitHub Profile
