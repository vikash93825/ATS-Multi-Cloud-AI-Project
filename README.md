# ATS Resume Scanner (AWS + GCP + Gemini AI)

AI-powered ATS Resume Scanner built using **Streamlit + Python + Google Gemini + AWS EC2**.

Users can:
- Upload Resume PDF
- Paste Job Description (JD)
- Get ATS Match Score
- Resume Review
- Keyword Analysis

---

# Architecture

```text
User
 ↓
Streamlit UI
 ↓
Resume PDF Processing
(pdf2image)
 ↓
Google Gemini AI
 ↓
ATS Review + Match Score
```

---

# Prerequisites

- AWS Account
- Ubuntu EC2 Instance
- Python 3.7+
- Google Gemini API Key

---

# Part 1 — Launch AWS EC2 Instance

Create:

- Ubuntu Server 20.04 LTS
- Open Port:
  - 22 (SSH)
  - 8501 (Streamlit)

Connect:

```bash
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

Switch root:

```bash
sudo -i
```

---

# Part 2 — Install Dependencies

Update:

```bash
apt update && apt upgrade -y
```

Install Python:

```bash
apt install python3 python3-pip python3-venv -y
```

Verify:

```bash
python3 --version
pip3 --version
```

Install Git:

```bash
apt install git -y
```

Verify:

```bash
git --version
```

Install Poppler:

```bash
apt install poppler-utils -y
```

Verify:

```bash
pdftoppm -v
```

---

# Part 3 — Clone Repository

```bash
git clone https://github.com/CloudDevOpsHub/Application-Tracking-System.git

cd Application-Tracking-System
```

---

# Part 4 — Create Virtual Environment

Create:

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Expected:

```bash
(venv)
```

---

# Part 5 — Install Packages

Upgrade pip:

```bash
pip install --upgrade pip
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Gemini SDK:

```bash
pip install google-generativeai
```

---

# Part 6 — Configure Gemini API

## Generate API Key

### Google AI Studio

1. Open Google AI Studio
2. Create Project
3. API Keys
4. Create API Key

Copy key.

---

# Part 7 — Configure Streamlit Secrets

Create folder:

```bash
mkdir -p .streamlit
```

Open:

```bash
vi .streamlit/secrets.toml
```

Add:

```toml
GOOGLE_API_KEY="YOUR_API_KEY"
```

Save:

```text
ESC
:wq
```

---

# Part 8 — Run Application

Start:

```bash
streamlit run app.py \
--server.port 8501 \
--server.enableCORS false
```

Output:

```text
Local URL:
http://localhost:8501

Network URL:
http://PUBLIC_IP:8501
```

Open:

```text
http://YOUR_PUBLIC_IP:8501
```

---

# Project Structure

```text
Application-Tracking-System/
│
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│    └── secrets.toml
│
├── uploads/
├── assets/
├── utils/
└── venv/
```

---

# Features

✅ Resume Upload  
✅ ATS Analysis  
✅ Gemini Integration  
✅ Match Score  
✅ Resume Review  
✅ Keywords Analysis  
✅ AWS Deployment  

---

# Troubleshooting

## Port issue

```bash
sudo ufw allow 8501
sudo ufw reload
```

---

## Missing poppler

```bash
sudo apt install poppler-utils
```

---

## Verify Gemini Key

```bash
cat .streamlit/secrets.toml
```

Expected:

```toml
GOOGLE_API_KEY="YOUR_KEY"
```

---

# Author

Vikash Kumar
