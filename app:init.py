"""
Programme Outline Generator Web App
-----------------------------------
A web application that generates training workshop programme outlines
based on reference outlines and user specifications.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Flask for web framework
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from flask_cors import CORS

# Database
from flask_sqlalchemy import SQLAlchemy

# Vector database for embeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# NLP and embedding generation
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import openai  # For GPT integration

# PDF and DOCX handling (import/export)
from docx import Document
from fpdf import FPDF
import PyPDF2

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///outline_generator.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_session_management')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')

# Initialize extensions
db = SQLAlchemy(app)
openai.api_key = app.config['OPENAI_API_KEY']

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Download NLTK data (if needed)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
