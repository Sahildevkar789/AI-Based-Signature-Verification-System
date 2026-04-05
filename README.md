# AI-Based Signature Verification System

A Flask-based web application that uses Machine Learning (ORB similarity + SVM/RandomForest) to verify student signatures against a database of genuine samples.

## Features
- **Student Management:** Add new students and upload their genuine signature samples.
- **Real-time Verification:** Upload a signature to verify whether it is genuine or forged.
- **Verification History:** View a log of all previous verification attempts.
- **Secure Authentication:** User signup/login system to protect historical data.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd signature_project
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   # Create virtual environment
   python -m venv venv
   # Activate virtual environment (Windows)
   .\venv\Scripts\activate
   # Activate virtual environment (Unix/macOS)
   source venv/bin/activate

   # Install required packages
   pip install -r requirements.txt
   ```

## Running the Application

1. **Ensure the model exists:**
   Make sure `model/cedar_student_model.pkl` is present in the project directory.

2. **Start the Flask server:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:5000/`.

## Deployment
For production deployment, use a WSGI server like **gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```