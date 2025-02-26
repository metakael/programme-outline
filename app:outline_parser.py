"""
Outline Parser and Embedding Generator
-------------------------------------
Extracts structured data from reference outlines and generates embeddings
for similarity search.
"""

import re
import json
import numpy as np
from typing import Dict, List, Any, Tuple
import openai

from app import app

class OutlineParser:
    """
    Parse workshop outlines to extract structure, segments, durations, and other metadata.
    """
    
    def __init__(self):
        self.patterns = {
            'segment_title': r'^\s*\d+\.\s+(.*?)(?:\s+\(\d+\s*(?:min|minutes)\)|\s*$)',
            'duration': r'\((\d+)\s*(?:min|minutes)\)',
            'subsection': r'^\s*•\s+(.*?)$',
            'break': r'(?i)break|pause|rest'
        }
    
    def parse_outline(self, content: str) -> Dict[str, Any]:
        """
        Parse an outline into a structured format.
        
        Args:
            content: The raw text content of the outline
            
        Returns:
            A dictionary containing the parsed structure
        """
        lines = content.split('\n')
        structure = {
            'title': self._extract_title(lines),
            'segments': self._extract_segments(lines),
            'total_duration': 0,
            'has_breaks': False,
            'segment_count': 0,
            'format_style': self._detect_format_style(content)
        }
        
        # Calculate aggregate data
        structure['total_duration'] = sum(seg.get('duration', 0) for seg in structure['segments'])
        structure['has_breaks'] = any('break' in seg.get('title', '').lower() for seg in structure['segments'])
        structure['segment_count'] = len(structure['segments'])
        
        return structure
    
    def _extract_title(self, lines: List[str]) -> str:
        """Extract the title from the first few lines of the outline"""
        for line in lines[:5]:  # Check first 5 lines for title
            if line and not line.startswith(('#', '•', '-', '*')):
                return line.strip()
        return "Untitled Workshop"
    
    def _extract_segments(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract all segments from the outline"""
        segments = []
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new segment
            segment_match = re.search(self.patterns['segment_title'], line)
            if segment_match:
                # Save previous segment if it exists
                if current_segment:
                    segments.append(current_segment)
                
                # Start new segment
                title = segment_match.group(1).strip()
                duration_match = re.search(self.patterns['duration'], line)
                duration = int(duration_match.group(1)) if duration_match else 0
                
                current_segment = {
                    'title': title,
                    'duration': duration,
                    'content': [line],
                    'is_break': bool(re.search(self.patterns['break'], title, re.IGNORECASE)),
                    'subsections': []
                }
            
            # Check if this is a subsection
            elif current_segment and re.search(self.patterns['subsection'], line):
                subsection = re.search(self.patterns['subsection'], line).group(1).strip()
                current_segment['subsections'].append(subsection)
                current_segment['content'].append(line)
            
            # Otherwise, add to current segment content
            elif current_segment:
                current_segment['content'].append(line)
        
        # Add the last segment
        if current_segment:
            segments.append(current_segment)
            
        return segments
    
    def _detect_format_style(self, content: str) -> Dict[str, Any]:
        """Detect formatting style from the outline"""
        style = {
            'uses_bullets': '•' in content,
            'uses_numbered_sections': bool(re.search(r'^\s*\d+\.', content, re.MULTILINE)),
            'uses_timing': bool(re.search(self.patterns['duration'], content)),
            'capitalization': self._detect_capitalization(content),
            'uses_colons': ':' in content
        }
        return style
    
    def _detect_capitalization(self, content: str) -> str:
        """Detect capitalization style in section headers"""
        title_case_count = 0
        uppercase_count = 0
        
        segment_titles = re.findall(self.patterns['segment_title'], content, re.MULTILINE)
        if not segment_titles:
            return "unknown"
            
        for title in segment_titles:
            if title.isupper():
                uppercase_count += 1
            elif title.istitle():
                title_case_count += 1
                
        if uppercase_count > title_case_count:
            return "uppercase"
        elif title_case_count > 0:
            return "title_case"
        else:
            return "mixed"


class EmbeddingGenerator:
    """
    Generate and manage embeddings for reference outlines.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or app.config['OPENAI_API_KEY']
        
    def generate_embedding(self, content: str, structure: Dict[str, Any]) -> np.ndarray:
        """
        Generate an embedding vector for a reference outline.
        
        Args:
            content: The raw outline content
            structure: The parsed structure of the outline
            
        Returns:
            A numpy array containing the embedding vector
        """
        # Prepare a concise representation of the outline for embedding
        embedding_text = self._prepare_embedding_text(content, structure)
        
        try:
            # Generate embedding using OpenAI's API
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=embedding_text
            )
            embedding = np.array(response['data'][0]['embedding'], dtype=np.float32)
            return embedding
            
        except Exception as e:
            app.logger.error(f"Error generating embedding: {str(e)}")
            # Fallback: Create a simple TF-IDF style embedding (in a real app, we'd use a better fallback)
            words = set(re.findall(r'\w+', content.lower()))
            # Return a simple dummy embedding (zeros) in case of error
            return np.zeros(1536, dtype=np.float32)  # Ada embeddings are 1536 dimensions
    
    def _prepare_embedding_text(self, content: str, structure: Dict[str, Any]) -> str:
        """Prepare a concise text representation for embedding"""
        # Include key structural elements that define the style
        segments = structure.get('segments', [])
        segment_titles = [seg.get('title', '') for seg in segments]
        format_style = structure.get('format_style', {})
        
        # Create a descriptive representation
        parts = [
            f"Workshop title: {structure.get('title', 'Untitled')}",
            f"Format style: {json.dumps(format_style)}",
            f"Segments: {' | '.join(segment_titles)}",
            f"Total duration: {structure.get('total_duration', 0)} minutes",
            f"Segment count: {structure.get('segment_count', 0)}"
        ]
        
        return "\n".join(parts)
        
    def find_similar_outlines(self, embedding: np.ndarray, reference_embeddings: List[Tuple[int, np.ndarray]], top_n=3) -> List[int]:
        """
        Find the most similar reference outlines based on embedding similarity.
        
        Args:
            embedding: The query embedding
            reference_embeddings: List of (id, embedding) tuples
            top_n: Number of similar outlines to return
            
        Returns:
            List of reference outline IDs sorted by similarity
        """
        if not reference_embeddings:
            return []
            
        # Extract IDs and embeddings
        ids = [ref[0] for ref in reference_embeddings]
        embeddings = np.vstack([ref[1] for ref in reference_embeddings])
        
        # Calculate cosine similarity
        similarities = cosine_similarity([embedding], embeddings)[0]
        
        # Get indices of top_n most similar
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        
        # Return reference IDs
        return [ids[i] for i in top_indices]
