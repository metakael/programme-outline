"""
Enhanced PDF processing for Programme Outline Generator
------------------------------------------------------
Additional utilities to improve RAG with PDF documents
"""

import re
import io
import PyPDF2
from typing import Dict, List, Any, Optional, Tuple

def enhance_pdf_extraction(pdf_path: str) -> str:
    """
    Enhanced PDF extraction that preserves structure better than PyPDF2 alone
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted and processed text content
    """
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text_content = []
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            # Extract raw text
            text = page.extract_text()
            
            # Process text to better identify structure
            processed_text = _process_pdf_page(text, page_num)
            text_content.append(processed_text)
    
    # Join all pages and further process for structure
    full_content = "\n\n".join(text_content)
    return _post_process_content(full_content)

def _process_pdf_page(text: str, page_num: int) -> str:
    """Process a single PDF page to preserve structure"""
    
    # Ensure line breaks at section numbers (common in outlines)
    text = re.sub(r'(\d+)\.\s*([A-Z])', r'\n\1. \2', text)
    
    # Fix bullet points that might be merged
    text = re.sub(r'([^\n])•', r'\1\n•', text)
    
    # Fix durations in parentheses
    text = re.sub(r'\((\d+)\s*(min|minutes|minute)\)', r'(\1 min)', text)
    
    # Add spacing after bullet points for readability
    text = re.sub(r'•\s*([^\n])', r'• \1', text)
    
    return text

def _post_process_content(content: str) -> str:
    """Final processing of the full content"""
    
    # Remove excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Fix potential issues with section numbering
    content = re.sub(r'([^\d])(\.|\))\s*([A-Z])', r'\1\2\n\3', content)
    
    # Ensure proper spacing between sections
    content = re.sub(r'(\d+\.\s+[^\n]+)(\d+\.)', r'\1\n\n\2', content)
    
    # Fix potential OCR issues with numbers
    content = re.sub(r'([Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive)\s+(\w+)', r'1. \2', content)
    
    return content

def extract_outline_structure(content: str) -> Dict[str, Any]:
    """
    Extract structured information from the PDF content
    specifically for workshop outlines
    
    Returns a dictionary with:
    - title
    - segments (with durations if available)
    - format style
    """
    structure = {
        "title": "",
        "segments": [],
        "format_style": {}
    }
    
    # Extract title (usually at the beginning)
    lines = content.split('\n')
    for i, line in enumerate(lines[:5]):
        if line and not re.match(r'^\d+\.|^•|^-', line):
            structure["title"] = line.strip()
            break
    
    # Extract segments
    segments = []
    current_segment = None
    
    # Common patterns in workshop outlines
    segment_pattern = re.compile(r'^\s*(\d+)\.\s+(.*?)(?:\s*\((\d+)\s*(?:min|minutes|minute)\))?', re.MULTILINE)
    bullet_pattern = re.compile(r'^\s*[•\-]\s+(.*?)$', re.MULTILINE)
    
    # Find all segments
    for match in segment_pattern.finditer(content):
        number, title, duration_str = match.groups()
        
        # Save previous segment if exists
        if current_segment:
            segments.append(current_segment)
        
        # Parse duration
        duration = int(duration_str) if duration_str else 0
        
        # Create new segment
        current_segment = {
            "title": title.strip(),
            "duration": duration,
            "subsections": [],
            "content": []
        }
    
    # Add the last segment
    if current_segment:
        segments.append(current_segment)
    
    # Extract subsections
    for i, segment in enumerate(segments):
        # Get segment content
        if i < len(segments) - 1:
            segment_pattern = re.compile(fr'{segment["title"]}.*?(?={segments[i+1]["title"]})', re.DOTALL)
        else:
            segment_pattern = re.compile(fr'{segment["title"]}.*', re.DOTALL)
        
        segment_match = segment_pattern.search(content)
        if segment_match:
            segment_content = segment_match.group(0)
            
            # Find bullet points
            for bullet_match in bullet_pattern.finditer(segment_content):
                subsection = bullet_match.group(1).strip()
                segment["subsections"].append(subsection)
    
    structure["segments"] = segments
    
    # Detect format style
    structure["format_style"] = {
        "uses_bullets": '•' in content,
        "uses_numbered_sections": bool(segment_pattern.search(content)),
        "uses_timing": bool(re.search(r'\(\d+\s*(?:min|minutes|minute)\)', content)),
        "capitalization": _detect_capitalization_style(segments)
    }
    
    return structure

def _detect_capitalization_style(segments: List[Dict[str, Any]]) -> str:
    """Detect capitalization style from segments"""
    if not segments:
        return "unknown"
    
    uppercase_count = 0
    titlecase_count = 0
    
    for segment in segments:
        title = segment.get("title", "")
        if title.isupper():
            uppercase_count += 1
        elif title[0].isupper() and not title.isupper():
            titlecase_count += 1
    
    if uppercase_count > titlecase_count:
        return "uppercase"
    elif titlecase_count > 0:
        return "title_case"
    else:
        return "mixed"

def chunk_pdf_for_embeddings(content: str) -> List[str]:
    """
    Split PDF content into smaller chunks for better embeddings
    
    Returns a list of chunks suitable for embedding generation
    """
    # Split by segments first
    segment_pattern = re.compile(r'(\d+\.\s+.*?)(?=\d+\.\s+|$)', re.DOTALL)
    segments = segment_pattern.findall(content)
    
    chunks = []
    for segment in segments:
        # If segment is too long, split further
        if len(segment) > 1000:
            # Split by paragraphs
            paragraphs = re.split(r'\n\s*\n', segment)
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < 1000:
                    current_chunk += para + "\n\n"
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks.append(segment.strip())
    
    return chunks

# Additional utility function to be used in the outline generator
def process_pdf_for_rag(pdf_path: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process PDF for RAG system
    
    Returns:
        Tuple containing:
        - Full content
        - Structure
        - Embedding chunks with metadata
    """
    # Extract content
    content = enhance_pdf_extraction(pdf_path)
    
    # Extract structure
    structure = extract_outline_structure(content)
    
    # Create chunks for embeddings
    raw_chunks = chunk_pdf_for_embeddings(content)
    
    # Prepare chunks with metadata
    chunks_with_metadata = []
    for i, chunk in enumerate(raw_chunks):
        chunks_with_metadata.append({
            "content": chunk,
            "index": i,
            "source": "pdf",
            "segment_info": _identify_segment_info(chunk, structure)
        })
    
    return content, structure, chunks_with_metadata

def _identify_segment_info(chunk: str, structure: Dict[str, Any]) -> Dict[str, Any]:
    """Identify which segment(s) this chunk belongs to"""
    segment_info = {
        "segment_titles": [],
        "segment_indices": []
    }
    
    for i, segment in enumerate(structure.get("segments", [])):
        title = segment.get("title", "")
        if title and title in chunk:
            segment_info["segment_titles"].append(title)
            segment_info["segment_indices"].append(i)
    
    return segment_info
