import os
import io
import re
from typing import Dict, List
import PyPDF2

# Enhanced COMMON_SKILLS list
COMMON_SKILLS = [
# Programming Languages
"Python", "Java", "JavaScript", "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin", "Go", "Rust",
"TypeScript", "HTML", "CSS", "SQL", "R", "MATLAB", "Perl", "Scala", "Dart", "Haskell", "Lua",
"Assembly", "Bash", "Shell Scripting", "PowerShell", "Objective-C", "Groovy", "Elixir", "Clojure",
"Fortran", "COBOL", "F#", "Julia", "Racket", "Erlang", "Visual Basic", "VBA", "SAS", "Stata",
"SPSS", "APL", "Prolog", "Lisp", "Scheme", "Smalltalk", "Ada", "Delphi", "Pascal",

# Web Development
"React", "Angular", "Vue", "Node.js", "Express.js", "Django", "Flask", "Spring", "Laravel", "Rails",
"Bootstrap", "jQuery", "Sass", "Less", "Tailwind CSS", "Material-UI", "Ant Design", "Webpack",
"Babel", "Gulp", "Grunt", "Next.js", "Nuxt.js", "Gatsby", "Nest.js", "FastAPI", "ASP.NET",
"WordPress", "Drupal", "Joomla", "Magento", "Shopify", "Webflow", "GraphQL", "REST API",
"SOAP", "WebSockets", "PWA", "Web Components", "Web Assembly", "Three.js", "D3.js",

# Mobile Development
"React Native", "Flutter", "Ionic", "Xamarin", "Cordova", "PhoneGap", "Android Studio",
"Xcode", "SwiftUI", "Jetpack Compose", "Appium", "Fastlane",

# Database Technologies
"MySQL", "PostgreSQL", "MongoDB", "Redis", "Oracle", "SQL Server", "SQLite", "MariaDB",
"Cassandra", "Couchbase", "DynamoDB", "Firebase", "Realm", "Neo4j", "ArangoDB", "CouchDB",
"HBase", "BigQuery", "Snowflake", "Redshift", "Databricks", "Elasticsearch", "Solr",
"SQL", "NoSQL", "ETL", "Data Warehousing", "Data Modeling", "Database Design",

# Cloud & DevOps
"AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git", "GitHub", "GitLab", "Bitbucket",
"Ansible", "Terraform", "Puppet", "Chef", "Vagrant", "Prometheus", "Grafana", "Splunk",
"New Relic", "Datadog", "CircleCI", "Travis CI", "GitHub Actions", "GitLab CI", "Azure DevOps",
"Serverless", "Lambda", "EC2", "S3", "RDS", "VPC", "IAM", "CloudFormation", "CloudFront",
"Route53", "Load Balancing", "Auto Scaling", "Containerization", "Microservices", "API Gateway",
"Cloud Security", "Identity Management", "Monitoring", "Logging", "Performance Optimization",

# Data Science & AI/ML
"Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "OpenCV", "NLTK", "spaCy",
"Hugging Face", "Transformers", "LangChain", "OpenAI", "LLM", "Computer Vision", "Natural Language Processing",
"Deep Learning", "Neural Networks", "CNN", "RNN", "LSTM", "GAN", "Reinforcement Learning",
"Data Analysis", "Data Visualization", "Tableau", "Power BI", "Matplotlib", "Seaborn", "Plotly",
"Jupyter", "Colab", "RStudio", "Apache Spark", "Hadoop", "Hive", "Pig", "Kafka", "Airflow",
"MLOps", "Model Deployment", "Feature Engineering", "Statistical Analysis", "Hypothesis Testing",
"Regression", "Classification", "Clustering", "Recommendation Systems", "Time Series Analysis",

# Software Development & Tools
"Linux", "Unix", "Windows", "macOS", "Vim", "Emacs", "VSCode", "IntelliJ", "Eclipse", "PyCharm",
"Android Development", "iOS Development", "Cross-Platform Development", "Desktop Applications",
"Game Development", "Unity", "Unreal Engine", "Blender", "Maya", "3D Modeling", "VR/AR Development",
"Embedded Systems", "IoT", "Firmware", "Device Drivers", "Robotics", "Automation", "Scripting",

# Cybersecurity
"Network Security", "Application Security", "Cloud Security", "Information Security", "Cybersecurity",
"Penetration Testing", "Ethical Hacking", "Vulnerability Assessment", "Security Auditing",
"Cryptography", "Encryption", "PKI", "SSL/TLS", "Firewalls", "IDS/IPS", "SIEM", "SOC",
"Incident Response", "Digital Forensics", "Risk Management", "Compliance", "GDPR", "HIPAA",
"PCI DSS", "NIST", "ISO 27001", "OWASP", "Security Protocols", "Zero Trust", "Multi-factor Authentication",

# Project Management & Methodologies
"Agile", "Scrum", "Kanban", "Waterfall", "DevOps", "CI/CD", "Lean", "Six Sigma", "Prince2",
"PMBOK", "Project Management", "Product Management", "Product Ownership", "Backlog Management",
"Sprint Planning", "User Stories", "Requirements Gathering", "Stakeholder Management",
"Risk Management", "Change Management", "Quality Assurance", "Testing", "QA", "UAT",
"Documentation", "Technical Writing", "Business Analysis", "Process Improvement",

# Business & Professional Skills
"Leadership", "Team Management", "Project Management", "Strategic Planning", "Business Strategy",
"Product Strategy", "Market Research", "Competitive Analysis", "Business Development",
"Partnerships", "Sales", "Marketing", "Digital Marketing", "SEO", "SEM", "Social Media Marketing",
"Content Marketing", "Email Marketing", "Brand Management", "Public Relations", "CRM",
"Customer Relationship Management", "Customer Service", "Client Management", "Account Management",
"Negotiation", "Contract Management", "Vendor Management", "Supply Chain Management",
"Operations Management", "Financial Analysis", "Budgeting", "Forecasting", "Financial Modeling",
"Data Analysis", "Business Intelligence", "KPIs", "Metrics", "Reporting", "Dashboard Creation",

# Soft Skills & Personal Attributes
"Communication", "Verbal Communication", "Written Communication", "Presentation Skills",
"Public Speaking", "Interpersonal Skills", "Teamwork", "Collaboration", "Cross-functional Collaboration",
"Problem Solving", "Critical Thinking", "Analytical Thinking", "Creative Thinking", "Innovation",
"Adaptability", "Flexibility", "Resilience", "Time Management", "Organization", "Multitasking",
"Attention to Detail", "Quality Focus", "Results-oriented", "Goal-oriented", "Self-motivated",
"Initiative", "Proactive", "Decision Making", "Conflict Resolution", "Emotional Intelligence",
"Mentoring", "Coaching", "Training", "Team Building", "Cultural Awareness", "Diversity and Inclusion",

# Design & Creative Skills
"UI/UX Design", "User Interface Design", "User Experience Design", "Wireframing", "Prototyping",
"Figma", "Sketch", "Adobe XD", "InVision", "Photoshop", "Illustrator", "InDesign", "After Effects",
"Premiere Pro", "Final Cut Pro", "Graphic Design", "Visual Design", "Interaction Design",
"Human-Centered Design", "Design Thinking", "Usability Testing", "Accessibility", "WCAG",
"Motion Graphics", "Video Editing", "Animation", "Illustration", "Typography", "Color Theory",
"Brand Identity", "Logo Design", "Print Design", "Packaging Design", "Photography",

# Industry-Specific Skills
"Healthcare IT", "Health Informatics", "Electronic Health Records", "FinTech", "Blockchain",
"Cryptocurrency", "Smart Contracts", "Banking Systems", "Insurance Technology", "EdTech",
"Learning Management Systems", "E-commerce", "Payment Processing", "Supply Chain Technology",
"Logistics", "Manufacturing Systems", "Automotive Technology", "Aerospace Systems",
"Telecommunications", "Network Engineering", "Wireless Technologies", "Satellite Systems",

# Languages
"English", "Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Arabic", "Hindi",
"Portuguese", "Russian", "Italian", "Dutch", "Swedish", "Norwegian", "Danish", "Finnish",
"Polish", "Turkish", "Hebrew", "Greek", "Thai", "Vietnamese", "Malay", "Indonesian"
]

HEADER_PATTERNS = [
    r'(?i)experience', r'(?i)work experience', r'(?i)professional experience',
    r'(?i)education', r'(?i)academic', r'(?i)skills', r'(?i)technical skills',
    r'(?i)certifications', r'(?i)projects', r'(?i)summary', r'(?i)objective'
]

def extract_text_from_pdf(file_stream: io.BytesIO) -> str:
    try:
        reader = PyPDF2.PdfReader(file_stream)
        pages = []
        for p in reader.pages:
            try:
                text = p.extract_text() or ""
            except Exception:
                text = ""
            pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def split_by_header(full_text: str) -> Dict[str, str]:
    """
    Try to split by common section headers. Return dict with Experience, Education, Skills.
    """
    keys = {}
    # create header regex that captures known headers
    pattern = re.compile(r'^\s*(?P<header>(?:Experience|Work Experience|Professional Experience|Education|Academic|Skills|Technical Skills|Certifications|Projects|Summary|Objective))\s*[:\-\n]*',
                         re.IGNORECASE | re.MULTILINE)
    matches = list(pattern.finditer(full_text))
    if matches:
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(full_text)
            header = m.group('header').strip().lower()
            block = full_text[start:end].strip()
            if 'experience' in header:
                keys.setdefault('Experience', '')
                keys['Experience'] += "\n" + block if keys['Experience'] else block
            elif 'education' in header or 'academic' in header:
                keys.setdefault('Education', '')
                keys['Education'] += "\n" + block if keys['Education'] else block
            elif 'skill' in header:
                keys.setdefault('Skills', '')
                keys['Skills'] += ", " + block if keys['Skills'] else block
            elif 'summary' in header or 'objective' in header:
                keys.setdefault('Summary', '')
                keys['Summary'] += "\n" + block if keys['Summary'] else block
            else:
                keys.setdefault('Other', '')
                keys['Other'] += "\n" + block if keys['Other'] else block
    return keys

def extract_skills_from_text(text: str, skills_list: List[str] = None) -> List[str]:
    if skills_list is None:
        skills_list = COMMON_SKILLS
    
    found = set()
    text_lower = text.lower()
    
    # Direct skill matching from common skills list
    for skill in skills_list:
        skill_lower = skill.lower()
        # Match whole words only
        if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
            found.add(skill)
    
    # Extract from skills sections more aggressively
    skills_sections = re.findall(r'(?i)(?:skills?|technical skills?|competencies?|expertise)[:\-]\s*([^\n]+(?:\n[^\n]+)*)', text)
    for section in skills_sections:
        # Split by common separators
        potential_skills = re.split(r'[,\|;/•\-•\n]', section)
        for potential in potential_skills:
            skill_candidate = potential.strip()
            if len(skill_candidate) > 2 and skill_candidate not in ['', 'and', 'or']:
                # Check if it matches any common skill
                skill_lower = skill_candidate.lower()
                for common_skill in skills_list:
                    if common_skill.lower() in skill_lower or skill_lower in common_skill.lower():
                        found.add(common_skill)
                        break
                else:
                    # If not in common list but looks like a skill, add it
                    if len(skill_candidate) < 50 and not skill_candidate[0].isdigit():
                        found.add(skill_candidate)
    
    # Also look for skills in the entire text using keyword patterns
    for skill in skills_list:
        if skill not in found:
            # More flexible matching for the entire text
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found.add(skill)
    
    return sorted(list(found))

def extract_sections_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, str]:
    stream = io.BytesIO(pdf_bytes)
    full_text = extract_text_from_pdf(stream)
    sections = split_by_header(full_text)
    # Normalize output
    experience = sections.get('Experience', '')
    education = sections.get('Education', '')
    skills_text = sections.get('Skills', '') or ""
    # If no explicit skills header, search whole text
    skills = extract_skills_from_text(full_text) if not skills_text else extract_skills_from_text(skills_text)
    # Compose concise combined text for similarity checks
    combined = " ".join([sections.get('Summary',''), experience, education])
    combined = combined.strip() or full_text[:1000]
    return {
        'raw_text': full_text,
        'experience': experience.strip(),
        'education': education.strip(),
        'skills': skills,
        'combined_text': combined
    }