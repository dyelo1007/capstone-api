import os
import io
import json
import re
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from extractor import extract_sections_from_pdf_bytes, extract_skills_from_text
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
ALLOWED_EXT = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

RESUMES_FILE = os.path.join(DATA_FOLDER, 'resumes.json')
JOBS_FILE = os.path.join(DATA_FOLDER, 'jobs.json')
MATCHES_FILE = os.path.join(DATA_FOLDER, 'matches.json')

lock = threading.Lock()

CORS(resources={r"/*": {"origins": "*"}})


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB

QUESTIONS = [
    {
        "q": "What is your highest level of education?",
        "type": "choice",
        "options": ["High School", "Associate", "Bachelor", "Master", "PhD"],
        "values": [10, 15, 25, 35, 45],
     

    },
    {
        "q": "How many years of professional experience do you have in your field?",
        "type": "choice",
        "options": ["0-1 years", "2-3 years", "4-5 years", "6+ years"],
        "values": [10, 20, 30, 40],
     
    },
    {
        "q": "How would you rate your relevant skills for your field?",
        "type": "choice",
        "options": ["Beginner", "Intermediate", "Advanced", "Expert"],
        "values": [10, 20, 30, 40],
      
    },
    {
        "q": "Do you have any professional certifications or licenses?",
        "type": "choice",
        "options": ["No", "1-2 certifications", "3-4 certifications", "5+ certifications"],
        "values": [0, 15, 25, 35],
        
    },
    {
        "q": "How comfortable are you with working in a team environment?",
        "type": "choice",
        "options": ["Not comfortable", "Somewhat comfortable", "Comfortable", "Very comfortable"],
        "values": [5, 15, 25, 35],
    
    },
    {
        "q": "How would you rate your communication skills?",
        "type": "choice",
        "options": ["Poor", "Fair", "Good", "Excellent"],
        "values": [5, 15, 25, 35],
 
    },
    {
        "q": "Are you willing to relocate for a job opportunity?",
        "type": "choice",
        "options": ["No", "Maybe", "Yes"],
        "values": [0, 10, 20],
       
    },
    {
        "q": "How many relevant tools or software are you proficient in for your field?",
        "type": "choice",
        "options": ["None", "1-2", "3-4", "5+"],
        "values": [0, 10, 20, 30],
     
    },
    {
        "q": "How would you rate your ability to adapt to new processes and systems?",
        "type": "choice",
        "options": ["Poor", "Fair", "Good", "Excellent"],
        "values": [5, 15, 25, 35],
        
    },
    {
        "q": "How would you rate your problem-solving abilities?",
        "type": "choice",
        "options": ["Poor", "Fair", "Good", "Excellent"],
        "values": [5, 15, 25, 35],
       
    },
    {
        "q": "Have you worked on projects or tasks with tight deadlines?",
        "type": "choice",
        "options": ["Never", "Rarely", "Sometimes", "Frequently"],
        "values": [0, 10, 20, 30],
        
    },
    {
        "q": "How would you rate your ability to learn new skills quickly?",
        "type": "choice",
        "options": ["Slow", "Average", "Fast", "Very Fast"],
        "values": [5, 15, 25, 35],
     
    }
]

def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def compute_employability_score(resume: dict, job_text: str) -> float:
    """
    Score components:
      - skill_overlap_ratio (0..1) = matched_skills / required_skills
      - tfidf_cosine (0..1) between job_text and resume['combined_text']
      - title_keyword_boost (0..0.15) if job title keywords appear in resume
    Weighted sum normalized to 0..100:
      score = 100 * (0.6*skill_overlap + 0.35*cos_sim + title_boost)
    """
    job_skills = extract_skills_from_text(job_text)
    resume_skills = resume.get('skills', []) or []
    job_skills_set = set([s.lower() for s in job_skills])
    resume_skills_set = set([s.lower() for s in resume_skills])

    matched = resume_skills_set.intersection(job_skills_set)
    skill_overlap = (len(matched) / max(1, len(job_skills_set))) if job_skills_set else 0.0

    txts = [job_text or "", resume.get('combined_text','') or ""]
    try:
        vec = TfidfVectorizer(stop_words='english', max_features=2000)
        X = vec.fit_transform(txts)
        cos = float(cosine_similarity(X[0], X[1])[0,0])
    except Exception:
        cos = 0.0

    title_boost = 0.0
    title_tokens = re.findall(r'\b([A-Za-z]{3,})\b', job_text)
    for tk in ['developer','engineer','manager','analyst','designer','scientist','administrator','consultant']:
        if re.search(r'\b' + re.escape(tk) + r'\b', job_text, re.IGNORECASE):
            if re.search(r'\b' + re.escape(tk) + r'\b', resume.get('raw_text',''), re.IGNORECASE):
                title_boost = 0.1
                break
    score_raw = 0.6*skill_overlap + 0.35*cos + title_boost
    score = max(0.0, min(1.0, score_raw))
    return round(score * 100.0, 2)


@app.route('/')
def index():
    return jsonify({'status':'resume-matcher API running'}), 200


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """
    multipart/form-data: field 'resume' (PDF), optional 'applicant_name'
    Saves resume and computes matches against existing jobs.
    """
    if 'resume' not in request.files:
        return jsonify({'error':'No resume file provided (field name resume).'}), 400
    f = request.files['resume']
    if f.filename == '':
        return jsonify({'error':'Empty filename'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error':'Only PDF allowed'}), 400

    applicant_name = request.form.get('applicant_name') or request.form.get('name') or "Applicant"
    filename = secure_filename(f.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(save_path)

    with open(save_path,'rb') as fh:
        pdf_bytes = fh.read()

    parsed = extract_sections_from_pdf_bytes(pdf_bytes)
    resume_id = f"{applicant_name}_{int(datetime.utcnow().timestamp())}"

    with lock:
        resumes = _load_json(RESUMES_FILE)
        resumes[resume_id] = {
            'id': resume_id,
            'name': applicant_name,
            'filename': filename,
            'uploaded_at': datetime.utcnow().isoformat(),
            'parsed': parsed
        }
        _save_json(RESUMES_FILE, resumes)

    matches_updated = []
    with lock:
        jobs = _load_json(JOBS_FILE)
        matches = _load_json(MATCHES_FILE)
        for job_id, job in jobs.items():
            score = compute_employability_score(parsed, job.get('job_text',''))
            matches.setdefault(job_id, {})
            matches[job_id][resume_id] = {
                'resume_id': resume_id,
                'job_id': job_id,
                'applicant_name': applicant_name,
                'score': score,
                'timestamp': datetime.utcnow().isoformat()
            }
            matches_updated.append({'job_id': job_id, 'resume_id': resume_id, 'score': score})
        _save_json(MATCHES_FILE, matches)

    response = {
        'resume_id': resume_id,
        'parsed': parsed,
        'matches_created': matches_updated
    }
    return jsonify(response), 201


@app.route('/upload_job', methods=['POST'])
def upload_job():
    """
    Accepts:
      - multipart/form-data 'job' (text file) OR 'job_text' form field OR JSON {"job_text": "...", "title": "..."}
    Saves job and computes matches against existing resumes, returns job_id.
    """
    job_text = ""
    title = request.form.get('title') or request.form.get('job_title') or ""
    if request.is_json:
        job_text = request.json.get('job_text','')
        title = title or request.json.get('title','')
    elif 'job' in request.files:
        blob = request.files['job'].read()
        try:
            job_text = blob.decode('utf-8', errors='ignore')
        except:
            job_text = str(blob)
    elif 'job_text' in request.form:
        job_text = request.form.get('job_text')
    else:
        return jsonify({'error':'No job text provided: send job_text in form or JSON, or upload job file under "job"'}), 400

    job_id = f"job_{int(datetime.utcnow().timestamp())}"
    job_entry = {
        'id': job_id,
        'title': title,
        'job_text': job_text,
        'uploaded_at': datetime.utcnow().isoformat()
    }

    with lock:
        jobs = _load_json(JOBS_FILE)
        jobs[job_id] = job_entry
        _save_json(JOBS_FILE, jobs)

        resumes = _load_json(RESUMES_FILE)
        matches = _load_json(MATCHES_FILE)
        matches.setdefault(job_id, {})
        for resume_id, rdata in resumes.items():
            parsed = rdata.get('parsed', {})
            score = compute_employability_score(parsed, job_text)
            matches[job_id][resume_id] = {
                'resume_id': resume_id,
                'job_id': job_id,
                'applicant_name': rdata.get('name',''),
                'score': score,
                'timestamp': datetime.utcnow().isoformat()
            }
        _save_json(MATCHES_FILE, matches)

    return jsonify({'job_id': job_id, 'title': title, 'matches_count': len(matches.get(job_id, {}))}), 201


@app.route('/jobs', methods=['GET'])
def list_jobs():
    with lock:
        jobs = _load_json(JOBS_FILE)
    return jsonify(jobs), 200


@app.route('/resumes', methods=['GET'])
def list_resumes():
    with lock:
        resumes = _load_json(RESUMES_FILE)
    return jsonify(resumes), 200


@app.route('/job_matches/<job_id>', methods=['GET'])
def job_matches(job_id):
    """
    Return ranked list of applicants for a job_id
    """
    with lock:
        matches = _load_json(MATCHES_FILE).get(job_id, {})
    sorted_list = sorted(matches.values(), key=lambda x: x.get('score',0), reverse=True)
    return jsonify(sorted_list), 200


@app.route('/resume_matches/<resume_id>', methods=['GET'])
def resume_matches(resume_id):
    """
    Return list of jobs and scores for a given resume_id
    """
    with lock:
        matches = _load_json(MATCHES_FILE)
    out = []
    for job_id, job_matches in matches.items():
        if resume_id in job_matches:
            out.append(job_matches[resume_id])
    out = sorted(out, key=lambda x: x.get('score',0), reverse=True)
    return jsonify(out), 200
@app.route("/chatbot_score", methods=["POST"])
def chatbot_score():
    data = request.get_json(force=True)
    answers = data.get("answers", [])

    total = 0
    for item in answers:
        q = item.get("question")
        idx = item.get("option_index", 0)

        for qset in QUESTIONS:
            if qset["q"] == q:
                total += qset["values"][idx]

    MAX_SCORE = sum([max(q["values"]) for q in QUESTIONS])  # 160

    normalized = (total / MAX_SCORE) * 100
    normalized = round(normalized, 2)

    return jsonify({"total_score": normalized})

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)