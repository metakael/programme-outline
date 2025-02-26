# Programme Outline Generator

A web application that generates training workshop programme outlines based on reference styles and user specifications.

## Overview

The Programme Outline Generator helps workshop designers quickly create new programme outlines that maintain a consistent style and structure while adapting to new objectives. Using Retrieval-Augmented Generation (RAG), the application ensures that new outlines adhere to established style guidelines from reference documents.

## Features

- **Reference Library Management:** Upload and maintain a library of reference outlines.
- **Custom Specification Input:** Input workshop objectives, durations, and segment requirements.
- **AI-Driven Outline Generation:** Generate outlines that match your style using RAG technology.
- **Style Adherence Control:** Adjust how closely the generated outline follows reference styles.
- **Segment Regeneration:** Regenerate specific segments for fine-tuning.
- **Preview & Edit:** View and edit generated outlines in real-time.
- **Multiple Export Formats:** Export in PDF, DOCX, and text formats.

## Tech Stack

### Backend
- Flask (Python web framework)
- SQLAlchemy (ORM)
- OpenAI API (GPT models for RAG)
- NLTK (Natural Language Toolkit)
- scikit-learn (for vector similarity)

### Frontend
- React
- React Router
- Axios (for API calls)

### Database
- SQLite (development)
- PostgreSQL (production)

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/programme-outline-generator.git
   cd programme-outline-generator
   ```

2. Set up the backend:
   ```
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file with your configuration
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   echo "FLASK_ENV=development" >> .env
   echo "SECRET_KEY=your_secret_key" >> .env
   
   # Initialize database
   flask db init
   flask db migrate
   flask db upgrade
   ```

3. Set up the frontend:
   ```
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```
   # From project root
   flask run
   ```

2. Start the frontend development server:
   ```
   # From frontend directory
   npm start
   ```

3. Open your browser and navigate to `http://localhost:3000`

## Usage

### 1. Upload Reference Outlines
- Go to the Reference Library page
- Upload example outlines in TXT, MD, or DOCX formats
- These will be used as style references for generation

### 2. Generate a New Outline
- On the Generate page, fill in the specification form
- Add workshop title, objectives, and duration
- Optionally add specific segments with durations
- Select reference outlines to use as style guides
- Adjust the style adherence slider as needed
- Click Generate Outline

### 3. Edit and Export
- View the generated outline in the preview pane
- Edit the outline manually if needed
- Regenerate specific segments using the Regenerate button
- Export the outline to PDF, DOCX, or text format

## Deployment

### Using Docker
```
# Build the Docker image
docker build -t programme-outline-generator .

# Run the container
docker run -p 5000:5000 --env-file .env programme-outline-generator
```

### On Replit
1. Create a new Replit from GitHub
2. Set up secrets for environment variables
3. Run the application using the provided start command

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for the GPT API
- Flask and React communities for the excellent frameworks
- All contributors and testers who help improve this application

# PDF Support in Programme Outline Generator

## Overview

The Programme Outline Generator now fully supports PDF files as reference outlines. The application includes specialized processing for PDF documents to ensure that their structure and formatting are correctly captured for the RAG (Retrieval-Augmented Generation) system.

## PDF Features

- **Enhanced PDF Extraction**: The application uses advanced text extraction and processing to preserve the structure of PDF outlines.
- **Structure Detection**: The system automatically detects segments, durations, bullet points, and other formatting elements in PDF documents.
- **PDF-specific RAG Integration**: The AI generator includes special handling for PDF-sourced reference outlines to ensure their style is accurately reflected in generated outputs.

## Using PDF Files

1. **Upload PDF References**: In the Reference Library, you can now upload PDF files alongside TXT, MD, and DOCX formats.
2. **Automatic Processing**: The system will automatically extract and process the content of PDF files.
3. **Style Analysis**: The application will analyze the style and structure of PDF outlines for use in generation.
4. **RAG Generation**: When you generate new outlines, the system will incorporate the style and structure of PDF references into the generation process.

## Technical Details

The PDF processing system includes:

- Text extraction using PyPDF2
- Enhanced parsing for workshop outline structures
- Specialized segmentation and formatting detection
- Integration with the embedding system for retrieving style information
- PDF-specific context for the OpenAI RAG system

## Requirements

- PyPDF2 version 3.0.1 or later

## Troubleshooting

If you encounter issues with PDF processing:

1. **Structure Detection**: Some PDFs with complex layouts may not be parsed correctly. In such cases, try converting to a simpler format like DOCX first.
2. **Formatting Issues**: If the generated outlines don't match the PDF style, try adjusting the style adherence slider to a higher value.
3. **Text Extraction**: If text isn't properly extracted from the PDF, ensure the PDF contains actual text and not just images of text.

