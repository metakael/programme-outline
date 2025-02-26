"""
AI Outline Generator with RAG
----------------------------
Uses Retrieval-Augmented Generation to create new outlines based on
reference styles and user specifications.
"""

import json
import openai
from typing import Dict, List, Any, Optional

from app import app
from app.models import ReferenceOutline, GeneratedOutline

class OutlineGenerator:
    """
    Generate new workshop outlines using a RAG approach.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or app.config['OPENAI_API_KEY']
        
    def generate_outline(self, 
                         specifications: Dict[str, Any], 
                         reference_outlines: List[ReferenceOutline],
                         style_adherence: float = 0.8) -> str:
        """
        Generate a new outline based on specifications and reference styles.
        
        Args:
            specifications: User requirements including objectives, duration, etc.
            reference_outlines: List of reference outlines to base style on
            style_adherence: 0-1 float indicating how closely to follow reference style
            
        Returns:
            Generated outline text
        """
        # Extract key specifications
        title = specifications.get('title', 'Workshop Outline')
        objectives = specifications.get('objectives', '')
        total_duration = specifications.get('total_duration', 120)  # Default 2 hours
        segments = specifications.get('segments', [])
        
        # Extract style and structure information from references
        reference_data = self._extract_reference_data(reference_outlines)
        
        # Build the prompt for the GPT model
        prompt = self._build_generation_prompt(
            title, objectives, total_duration, segments, reference_data, style_adherence
        )
        
        try:
            # Generate the outline using GPT
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",  # Or appropriate model
                messages=[
                    {"role": "system", "content": "You are a specialized assistant that creates workshop programme outlines. You strictly adhere to the style and structure of reference outlines. Pay close attention to the formatting, segment structure, and language style of the references."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Lower temperature for more predictable outputs
                max_tokens=2000
            )
            
            generated_outline = response.choices[0].message.content.strip()
            return generated_outline
            
        except Exception as e:
            app.logger.error(f"Error generating outline: {str(e)}")
            return f"Error generating outline: {str(e)}"
    
    def _extract_reference_data(self, reference_outlines: List[ReferenceOutline]) -> Dict[str, Any]:
        """Extract style and structure data from reference outlines"""
        if not reference_outlines:
            return {"style": "standard", "examples": []}
            
        # Extract format styles
        styles = []
        examples = []
        segments_by_outline = {}
        
        for outline in reference_outlines:
            # Extract the structure
            structure = outline.structure if outline.structure else {}
            
            # Get format style
            style = structure.get('format_style', {})
            if style:
                styles.append(style)
            
            # Add content as example
            examples.append(outline.content)
            
            # Store segments for more detailed analysis
            if 'segments' in structure:
                segments_by_outline[outline.id] = structure['segments']
        
        # Determine the dominant style by merging
        dominant_style = self._merge_styles(styles) if styles else {}
        
        # Extract common structural patterns from segments
        segment_patterns = self._extract_segment_patterns(segments_by_outline)
        
        return {
            "style": dominant_style,
            "examples": examples,
            "segment_patterns": segment_patterns
        }
        
    def _extract_segment_patterns(self, segments_by_outline):
        """Extract common patterns from segments across outlines"""
        # This function analyzes segments to find common patterns
        # Important for RAG to understand PDF-extracted content structure
        
        patterns = {
            "common_durations": set(),
            "segment_types": set(),
            "typical_sequence": []
        }
        
        # Collect common durations
        for outline_id, segments in segments_by_outline.items():
            for segment in segments:
                if 'duration' in segment and segment['duration'] > 0:
                    patterns["common_durations"].add(segment['duration'])
                
                # Detect segment type from title
                title = segment.get('title', '').lower()
                if 'introduction' in title or 'welcome' in title:
                    patterns["segment_types"].add("introduction")
                elif 'break' in title or 'pause' in title:
                    patterns["segment_types"].add("break")
                elif 'conclusion' in title or 'closing' in title or 'summary' in title:
                    patterns["segment_types"].add("conclusion")
                elif 'activity' in title or 'exercise' in title or 'workshop' in title:
                    patterns["segment_types"].add("activity")
                elif 'discussion' in title:
                    patterns["segment_types"].add("discussion")
                elif 'presentation' in title or 'lecture' in title:
                    patterns["segment_types"].add("presentation")
        
        # Convert sets to lists for JSON serialization
        patterns["common_durations"] = list(sorted(patterns["common_durations"]))
        patterns["segment_types"] = list(patterns["segment_types"])
        
        # Detect typical sequence (if any)
        if segments_by_outline:
            # Use the first outline as a template for sequence
            first_outline_id = next(iter(segments_by_outline))
            patterns["typical_sequence"] = [
                seg.get('title', '').lower() 
                for seg in segments_by_outline[first_outline_id]
            ]
            
        return patterns
    
    def _merge_styles(self, styles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple format styles to determine the dominant style"""
        if not styles:
            return {}
            
        # Count style features
        uses_bullets = sum(1 for s in styles if s.get('uses_bullets', False))
        uses_numbered = sum(1 for s in styles if s.get('uses_numbered_sections', False))
        uses_timing = sum(1 for s in styles if s.get('uses_timing', False))
        uses_colons = sum(1 for s in styles if s.get('uses_colons', False))
        
        # Count capitalization styles
        cap_styles = {}
        for s in styles:
            cap = s.get('capitalization', 'unknown')
            cap_styles[cap] = cap_styles.get(cap, 0) + 1
        
        # Determine dominant capitalization
        dominant_cap = max(cap_styles.items(), key=lambda x: x[1])[0] if cap_styles else "title_case"
        
        # Return merged style
        return {
            "uses_bullets": uses_bullets > len(styles) / 2,
            "uses_numbered_sections": uses_numbered > len(styles) / 2,
            "uses_timing": uses_timing > len(styles) / 2,
            "capitalization": dominant_cap,
            "uses_colons": uses_colons > len(styles) / 2
        }
    
    def _build_generation_prompt(self, 
                               title: str, 
                               objectives: str, 
                               total_duration: int,
                               segments: List[Dict[str, Any]],
                               reference_data: Dict[str, Any],
                               style_adherence: float) -> str:
        """Build the prompt for the GPT model"""
        # Format the style guidelines
        style = reference_data.get('style', {})
        style_guidelines = []
        
        if style.get('uses_bullets', False):
            style_guidelines.append("- Use bullet points (•) for subsections")
        if style.get('uses_numbered_sections', True):
            style_guidelines.append("- Use numbered sections (1., 2., etc.) for main segments")
        if style.get('uses_timing', True):
            style_guidelines.append("- Include duration in minutes for each segment in parentheses")
        
        cap_style = style.get('capitalization', 'title_case')
        if cap_style == 'uppercase':
            style_guidelines.append("- Use UPPERCASE for main section titles")
        elif cap_style == 'title_case':
            style_guidelines.append("- Use Title Case for main section titles")
            
        if style.get('uses_colons', False):
            style_guidelines.append("- Use colons after section titles")
        
        # Format examples (limited to save tokens)
        examples = reference_data.get('examples', [])
        example_text = ""
        
        if examples and style_adherence > 0.5:
            # Process examples for RAG
            processed_examples = []
            
            # If we have multiple examples, include relevant portions from each
            if len(examples) > 1 and style_adherence > 0.7:
                # Use segments from different examples for better RAG performance
                for i, example in enumerate(examples[:3]):  # Limit to first 3 examples
                    # Extract a meaningful portion (first 1500 chars) to save tokens
                    excerpt = example[:1500] + ("..." if len(example) > 1500 else "")
                    processed_examples.append(f"EXAMPLE {i+1}:\n{excerpt}\n")
                
                example_text = "\nREFERENCE EXAMPLES:\n\n" + "\n".join(processed_examples) + "\n"
            else:
                # Take just the first example to save tokens
                example_text = f"\nREFERENCE EXAMPLE:\n\n{examples[0]}\n\n"
                
        # Add pattern information for better RAG performance
        pattern_info = reference_data.get('segment_patterns', {})
        if pattern_info and style_adherence > 0.6:
            common_durations = pattern_info.get('common_durations', [])
            segment_types = pattern_info.get('segment_types', [])
            
            if common_durations or segment_types:
                pattern_text = "\nCOMMON PATTERNS:\n"
                
                if common_durations:
                    pattern_text += f"- Typical durations: {', '.join(map(str, common_durations))} minutes\n"
                
                if segment_types:
                    pattern_text += f"- Typical segment types: {', '.join(segment_types)}\n"
                
                example_text += pattern_text
            
        # Format segment requirements
        segment_reqs = []
        for seg in segments:
            seg_title = seg.get('title', '')
            seg_duration = seg.get('duration', 0)
            seg_description = seg.get('description', '')
            
            if seg_title and seg_duration:
                segment_reqs.append(f"- {seg_title} ({seg_duration} min): {seg_description}")
            elif seg_title:
                segment_reqs.append(f"- {seg_title}: {seg_description}")
        
        segment_text = "\n".join(segment_reqs) if segment_reqs else "No specific segment requirements."
        
        # Build the final prompt
        prompt = f"""
Create a workshop programme outline with the following specifications:

TITLE: {title}

WORKSHOP OBJECTIVES:
{objectives}

TOTAL DURATION: {total_duration} minutes

REQUIRED SEGMENTS:
{segment_text}

STYLE GUIDELINES:
{"".join(f"{guideline}\n" for guideline in style_guidelines)}

Your task is to create a complete workshop outline that follows the style and structure of the reference examples with a style adherence level of {style_adherence * 100}%. 
The outline should incorporate all the specified objectives and segment requirements while maintaining the total duration of {total_duration} minutes.
{example_text}

IMPORTANT FORMATTING INSTRUCTIONS:
1. Pay careful attention to the numbering and indentation patterns in the reference examples
2. Maintain the exact same format for specifying durations (e.g., "(15 min)" or "(15 minutes)")
3. Use consistent capitalization and punctuation as shown in the references
4. Follow the bullet point style exactly as shown in the references
5. Preserve any special sections like introductions, breaks, or closing segments in the same style

Generate ONLY the outline itself without additional explanations or comments.
"""
        return prompt
    
    def regenerate_segment(self, 
                          outline_content: str, 
                          segment_index: int,
                          specifications: Dict[str, Any],
                          reference_outlines: List[ReferenceOutline]) -> str:
        """
        Regenerate a specific segment within an existing outline.
        
        Args:
            outline_content: The existing outline content
            segment_index: Index of the segment to regenerate
            specifications: Updated specifications for the segment
            reference_outlines: Reference outlines for style
            
        Returns:
            The updated outline with the regenerated segment
        """
        # Parse the existing outline
        from app.outline_parser import OutlineParser
        parser = OutlineParser()
        structure = parser.parse_outline(outline_content)
        
        # Check if segment index is valid
        segments = structure.get('segments', [])
        if segment_index < 0 or segment_index >= len(segments):
            return outline_content
            
        # Extract the segment to regenerate
        segment = segments[segment_index]
        segment_title = segment.get('title', f"Segment {segment_index+1}")
        segment_content = "\n".join(segment.get('content', []))
        
        # Get segment specifications
        seg_specs = specifications.get('segment', {})
        new_title = seg_specs.get('title', segment_title)
        new_duration = seg_specs.get('duration', segment.get('duration', 0))
        new_description = seg_specs.get('description', '')
        
        # Extract style information
        reference_data = self._extract_reference_data(reference_outlines)
        
        # Build prompt for segment regeneration
        prompt = f"""
I have a workshop outline and need to regenerate the following segment:

CURRENT SEGMENT:
{segment_content}

NEW SPECIFICATIONS:
- Title: {new_title}
- Duration: {new_duration} minutes
- Description: {new_description}

Please regenerate this segment while maintaining the style and structure consistency with the rest of the outline. The output should only include the regenerated segment, not the entire outline.
"""

        try:
            # Generate the segment using GPT
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a specialized assistant that creates workshop programme outlines. You strictly adhere to the style and structure of reference outlines."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
            
            new_segment = response.choices[0].message.content.strip()
            
            # Replace the segment in the outline
            lines = outline_content.split('\n')
            
            # Find the start and end of the segment
            start_line = -1
            end_line = -1
            in_segment = False
            current_seg_idx = -1
            
            for i, line in enumerate(lines):
                # Check if this is a new segment
                segment_match = parser._patterns.get('segment_title')
                if segment_match and re.search(segment_match, line):
                    if in_segment:
                        # End of previous segment
                        end_line = i - 1
                        if current_seg_idx == segment_index:
                            break
                    
                    # Start of new segment
                    in_segment = True
                    current_seg_idx += 1
                    
                    if current_seg_idx == segment_index:
                        start_line = i
            
            # If it's the last segment, end is the last line
            if current_seg_idx == segment_index and end_line == -1:
                end_line = len(lines) - 1
                
            # Replace the segment if found
            if start_line >= 0 and end_line >= start_line:
                new_segment_lines = new_segment.split('\n')
                lines = lines[:start_line] + new_segment_lines + lines[end_line+1:]
                
            return "\n".join(lines)
            
        except Exception as e:
            app.logger.error(f"Error regenerating segment: {str(e)}")
            return outline_content

"""
Enhancements to the AI Generator to better support PDF-sourced reference outlines
"""

# Add/update these methods in the OutlineGenerator class

def _process_pdf_references(self, reference_outlines):
    """Process references that came from PDF files for better RAG performance"""
    pdf_references = []
    
    for outline in reference_outlines:
        # Check if this was a PDF reference
        if hasattr(outline, 'filename') and outline.filename.endswith('.pdf'):
            pdf_references.append(outline)
    
    # Extract additional context from PDF references if available
    pdf_context = ""
    if pdf_references:
        pdf_context = self._extract_pdf_context(pdf_references)
    
    return pdf_context

def _extract_pdf_context(self, pdf_references):
    """Extract context information specific to PDF references"""
    context_parts = []
    
    for ref in pdf_references:
        structure = ref.structure if ref.structure else {}
        
        # Extract key style elements that might be harder to detect in PDFs
        if 'format_style' in structure:
            style = structure['format_style']
            style_desc = []
            
            if style.get('uses_bullets', False):
                style_desc.append("Uses bullet points for subsections")
            if style.get('uses_numbered_sections', False):
                style_desc.append("Uses numbered sections for main segments")
            if style.get('uses_timing', False):
                style_desc.append("Includes duration in minutes for segments")
            if 'capitalization' in style:
                cap_style = style['capitalization']
                if cap_style == 'uppercase':
                    style_desc.append("Uses UPPERCASE for section titles")
                elif cap_style == 'title_case':
                    style_desc.append("Uses Title Case for section titles")
            
            # Add to context
            if style_desc:
                context_parts.append(f"PDF Reference '{ref.title}' Style: " + "; ".join(style_desc))
        
        # Extract segment structure
        if 'segments' in structure and structure['segments']:
            segments = structure['segments']
            segment_desc = []
            
            for i, seg in enumerate(segments[:5]):  # Limit to first 5 segments
                title = seg.get('title', f"Segment {i+1}")
                duration = seg.get('duration', 0)
                if duration > 0:
                    segment_desc.append(f"{title} ({duration} min)")
                else:
                    segment_desc.append(title)
            
            if segment_desc:
                context_parts.append(f"PDF Reference '{ref.title}' Segments: " + "; ".join(segment_desc))
    
    return "\n".join(context_parts)

# Update the generate_outline method to include PDF-specific context
"""
def generate_outline(self, 
                    specifications: Dict[str, Any], 
                    reference_outlines: List[ReferenceOutline],
                    style_adherence: float = 0.8) -> str:
    ...
    
    # Extract style and structure information from references
    reference_data = self._extract_reference_data(reference_outlines)
    
    # Extract additional context from PDF references if any
    pdf_context = self._process_pdf_references(reference_outlines)
    
    # Build the prompt for the GPT model
    prompt = self._build_generation_prompt(
        title, objectives, total_duration, segments, reference_data, style_adherence, pdf_context
    )
    
    ...
"""

# Update the _build_generation_prompt method to include PDF context
"""
def _build_generation_prompt(self, 
                           title: str, 
                           objectives: str, 
                           total_duration: int,
                           segments: List[Dict[str, Any]],
                           reference_data: Dict[str, Any],
                           style_adherence: float,
                           pdf_context: str = "") -> str:
    ...
    
    # Add PDF-specific context if available
    if pdf_context:
        prompt += f"\nADDITIONAL PDF REFERENCE CONTEXT:\n{pdf_context}\n"
    
    prompt += "\nIMPORTANT FORMATTING INSTRUCTIONS:\n..."
    
    return prompt
"""
