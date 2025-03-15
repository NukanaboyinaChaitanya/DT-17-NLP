from flask import Flask, request, jsonify, render_template
import pickle
import os
import pdfplumber
import docx
import re
from collections import Counter

# ✅ Define ResumeScorer before loading model.pkl
class ResumeScorer:
    def __init__(self):
        self.weights = {
            "skills": 0.3,
            "experience": 0.3,
            "education": 0.2,
            "projects": 0.1,
            "certifications": 0.1
        }
        self.skill_keywords = ["python", "machine learning", "nlp", "flask", "tensorflow", "django", "sql", "data science"]
        self.experience_keywords = ["experience", "worked", "intern", "developer", "software engineer", "business analyst"]
        self.education_keywords = ["bachelor", "master", "phd", "degree", "university", "college"]
        self.projects_keywords = ["project", "developed", "built", "created", "implemented"]
        self.certifications_keywords = ["certification", "certified", "course", "completed"]

    def extract_text(self, file_path):
        text = ""
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + " "
        return text.lower().strip() if text else "no_text_found"

    def extract_words(self, text):
        """Extract words and count their frequency."""
        words = re.findall(r'\b[a-zA-Z]+\b', text)  # Extract words only
        return Counter(words)  # Return word frequency dictionary

    def score_resume(self, text):
        if text == "no_text_found":
            return 0  # If no text is extracted, score is 0

        word_counts = self.extract_words(text)

        category_scores = {
            "skills": sum(word_counts[word] for word in self.skill_keywords if word in word_counts),
            "experience": sum(word_counts[word] for word in self.experience_keywords if word in word_counts),
            "education": sum(word_counts[word] for word in self.education_keywords if word in word_counts),
            "projects": sum(word_counts[word] for word in self.projects_keywords if word in word_counts),
            "certifications": sum(word_counts[word] for word in self.certifications_keywords if word in word_counts)
        }

        total_score = sum(category_scores[cat] * self.weights[cat] for cat in category_scores)
        return round(total_score * 10, 2)  # Convert to a 0-100 scale

# ✅ Load the trained model after defining ResumeScorer
with open("model.pkl", "rb") as model_file:
    scorer = pickle.load(model_file)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/score", methods=["POST"])
def score_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    file_path = "temp_resume." + file.filename.split(".")[-1]
    file.save(file_path)

    text = scorer.extract_text(file_path)

    if text == "no_text_found":
        return jsonify({"error": "Could not extract text from resume"}), 400

    score = scorer.score_resume(text)

    os.remove(file_path)

    return jsonify({"score": score})  # ✅ Now returns only the score

if __name__ == "__main__":
    app.run(debug=True)
