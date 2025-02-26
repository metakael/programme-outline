// src/components/SpecificationForm.js
import React, { useState } from 'react';
import './SpecificationForm.css';

const SpecificationForm = ({ references, onGenerate, loading }) => {
  const [formData, setFormData] = useState({
    title: '',
    objectives: '',
    totalDuration: 120,
    segments: [],
    styleAdherence: 0.8,
    referenceIds: []
  });
  
  const [newSegment, setNewSegment] = useState({
    title: '',
    duration: 15,
    description: ''
  });
  
  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  // Handle segment input changes
  const handleSegmentChange = (e) => {
    const { name, value } = e.target;
    setNewSegment({
      ...newSegment,
      [name]: name === 'duration' ? parseInt(value, 10) || 0 : value
    });
  };
  
  // Add a segment to the list
  const addSegment = () => {
    if (newSegment.title.trim()) {
      const updatedSegments = [...formData.segments, { ...newSegment }];
      setFormData({
        ...formData,
        segments: updatedSegments
      });
      
      // Reset new segment form
      setNewSegment({
        title: '',
        duration: 15,
        description: ''
      });
    }
  };
  
  // Remove a segment from the list
  const removeSegment = (index) => {
    const updatedSegments = formData.segments.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      segments: updatedSegments
    });
  };
  
  // Handle reference selection
  const handleReferenceSelect = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => parseInt(option.value, 10));
    setFormData({
      ...formData,
      referenceIds: selectedOptions
    });
  };
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(formData);
  };
  
  return (
    <div className="specification-form">
      <h2>Workshop Specifications</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Workshop Title</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Enter workshop title"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="objectives">Objectives</label>
          <textarea
            id="objectives"
            name="objectives"
            value={formData.objectives}
            onChange={handleChange}
            required
            placeholder="Enter workshop objectives"
            rows={4}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="totalDuration">Total Duration (minutes)</label>
          <input
            type="number"
            id="totalDuration"
            name="totalDuration"
            value={formData.totalDuration}
            onChange={handleChange}
            required
            min={15}
            max={480}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="styleAdherence">Style Adherence</label>
          <input
            type="range"
            id="styleAdherence"
            name="styleAdherence"
            value={formData.styleAdherence}
            onChange={handleChange}
            min={0}
            max={1}
            step={0.1}
          />
          <div className="range-labels">
            <span>More Creative</span>
            <span>More Strict</span>
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="referenceIds">Reference Outlines</label>
          <select
            id="referenceIds"
            name="referenceIds"
            multiple
            value={formData.referenceIds}
            onChange={handleReferenceSelect}
          >
            {references.map(ref => (
              <option key={ref.id} value={ref.id}>
                {ref.title}
              </option>
            ))}
          </select>
          <small>Hold Ctrl/Cmd to select multiple</small>
        </div>
        
        <h3>Segments</h3>
        
        <div className="segments-list">
          {formData.segments.length === 0 ? (
            <p>No segments added yet. Add segments below or leave empty for AI to determine.</p>
          ) : (
            <ul>
              {formData.segments.map((segment, index) => (
                <li key={index} className="segment-item">
                  <div className="segment-header">
                    <strong>{segment.title}</strong> ({segment.duration} min)
                    <button 
                      type="button" 
                      className="remove-button"
                      onClick={() => removeSegment(index)}
                    >
                      &times;
                    </button>
                  </div>
                  {segment.description && (
                    <div className="segment-description">{segment.description}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <div className="add-segment-form">
          <h4>Add Segment</h4>
          <div className="segment-form-row">
            <div className="segment-form-group">
              <label htmlFor="segment-title">Title</label>
              <input
                type="text"
                id="segment-title"
                name="title"
                value={newSegment.title}
                onChange={handleSegmentChange}
                placeholder="Segment title"
              />
            </div>
            
            <div className="segment-form-group">
              <label htmlFor="segment-duration">Duration (min)</label>
              <input
                type="number"
                id="segment-duration"
                name="duration"
                value={newSegment.duration}
                onChange={handleSegmentChange}
                min={1}
                max={240}
              />
            </div>
          </div>
          
          <div className="segment-form-group">
            <label htmlFor="segment-description">Description (optional)</label>
            <textarea
              id="segment-description"
              name="description"
              value={newSegment.description}
              onChange={handleSegmentChange}
              placeholder="Segment description or requirements"
              rows={2}
            />
          </div>
          
          <button
            type="button"
            className="add-segment-button"
            onClick={addSegment}
            disabled={!newSegment.title.trim()}
          >
            Add Segment
          </button>
        </div>
        
        <div className="form-actions">
          <button 
            type="submit" 
            className="generate-button"
            disabled={loading || !formData.title || !formData.objectives}
          >
            {loading ? 'Generating...' : 'Generate Outline'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SpecificationForm;

// src/components/OutlinePreview.js
import React, { useState } from 'react';
import './OutlinePreview.css';

const OutlinePreview = ({ outline, onUpdate, onRegenerateSegment, onExport, loading }) => {
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [segmentToRegenerate, setSegmentToRegenerate] = useState(null);
  const [segmentSpecs, setSegmentSpecs] = useState({
    title: '',
    duration: 0,
    description: ''
  });
  
  // Enter edit mode
  const handleEdit = () => {
    setEditContent(outline.content);
    setEditMode(true);
  };
  
  // Save edited content
  const handleSave = () => {
    onUpdate(outline.id, { content: editContent });
    setEditMode(false);
  };
  
  // Cancel editing
  const handleCancel = () => {
    setEditContent('');
    setEditMode(false);
  };
  
  // Handle content changes in edit mode
  const handleContentChange = (e) => {
    setEditContent(e.target.value);
  };
  
  // Open segment regeneration modal
  const openRegenerateModal = (segmentIndex, segmentTitle) => {
    setSegmentToRegenerate(segmentIndex);
    setSegmentSpecs({
      title: segmentTitle,
      duration: 0,
      description: ''
    });
  };
  
  // Close segment regeneration modal
  const closeRegenerateModal = () => {
    setSegmentToRegenerate(null);
    setSegmentSpecs({
      title: '',
      duration: 0,
      description: ''
    });
  };
  
  // Handle segment spec changes
  const handleSegmentSpecChange = (e) => {
    const { name, value } = e.target;
    setSegmentSpecs({
      ...segmentSpecs,
      [name]: name === 'duration' ? parseInt(value, 10) || 0 : value
    });
  };
  
  // Regenerate segment
  const handleRegenerateSegment = () => {
    onRegenerateSegment(outline.id, segmentToRegenerate, segmentSpecs);
    closeRegenerateModal();
  };
  
  // Parse outline to identify segments (a simple implementation)
  const parseSegments = (content) => {
    if (!content) return [];
    
    const lines = content.split('\n');
    const segments = [];
    let currentIndex = -1;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Look for numbered segments (e.g., "1. Introduction")
      if (/^\d+\.\s+/.test(line)) {
        currentIndex++;
        segments.push({
          index: currentIndex,
          title: line.replace(/^\d+\.\s+/, '').split('(')[0].trim(),
          line: i
        });
      }
    }
    
    return segments;
  };
  
  // If no outline is selected, show empty state
  if (!outline) {
    return (
      <div className="outline-preview empty-state">
        <h2>Outline Preview</h2>
        <p>No outline generated yet. Use the form to generate a new outline.</p>
      </div>
    );
  }
  
  // Parse segments for the regeneration feature
  const segments = parseSegments(outline.content);
  
  return (
    <div className="outline-preview">
      <div className="preview-header">
        <h2>{outline.title}</h2>
        <div className="preview-actions">
          {editMode ? (
            <>
              <button onClick={handleSave} disabled={loading}>Save</button>
              <button onClick={handleCancel}>Cancel</button>
            </>
          ) : (
            <>
              <button onClick={handleEdit}>Edit</button>
              <button onClick={() => onExport(outline.id, 'pdf')}>Export PDF</button>
              <button onClick={() => onExport(outline.id, 'docx')}>Export DOCX</button>
            </>
          )}
        </div>
      </div>
      
      <div className="preview-objectives">
        <h3>Objectives:</h3>
        <p>{outline.objectives}</p>
      </div>
      
      <div className="preview-content">
        {editMode ? (
          <textarea
            value={editContent}
            onChange={handleContentChange}
            rows