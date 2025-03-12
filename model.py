import os
import zipfile
import docx2txt
import pandas as pd
import numpy as np
import PyPDF2
from sentence_transformers import SentenceTransformer, util

# Load pre-trained BERT model
bert_model = SentenceTransformer('all-MiniLM-L6-v2')  # Efficient BERT variant

def extract_text_from_resume(resume_path):
    """Extracts text from PDF or DOCX resumes."""
    if resume_path.endswith('.pdf'):
        text = ""
        with open(resume_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + " "
        return text.strip()
    
    elif resume_path.endswith('.docx'):
        return docx2txt.process(resume_path)

    return ""

def compute_similarity(resume_texts, job_description):
    """Computes similarity scores using BERT embeddings."""
    resume_embeddings = bert_model.encode(resume_texts, convert_to_tensor=True)
    jd_embedding = bert_model.encode(job_description, convert_to_tensor=True)

    similarity_scores = util.pytorch_cos_sim(resume_embeddings, jd_embedding)
    return similarity_scores.squeeze().tolist()

def resumemain(zip_path, job_description_path=None):
    """Processes resumes and ranks them based on similarity with job description."""
    
    # Extract resumes from ZIP
    extracted_data = []
    temp_dir = os.path.splitext(zip_path)[0] + "_unzipped"
    os.makedirs(temp_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Read job description
    job_description_text = ""
    if job_description_path:
        with open(job_description_path, 'r', encoding='utf-8') as jd_file:
            job_description_text = jd_file.read()

    # Process resumes
    resume_texts = []
    resume_filenames = []
    for file_name in os.listdir(temp_dir):
        resume_path = os.path.join(temp_dir, file_name)
        if file_name.endswith(('.pdf', '.docx')):
            text_content = extract_text_from_resume(resume_path)
            if text_content:
                resume_texts.append(text_content)
                resume_filenames.append(file_name)

    # Compute similarity scores
    if job_description_text and resume_texts:
        similarity_scores = compute_similarity(resume_texts, job_description_text)
    else:
        similarity_scores = [0] * len(resume_texts)

    # Store results in DataFrame
    results = pd.DataFrame({
        "ID": range(1, len(resume_filenames) + 1),
        "Filename": resume_filenames,
        "Similarity Score": similarity_scores
    })

    results = results.sort_values(by="Similarity Score", ascending=False).reset_index(drop=True)
    return results
