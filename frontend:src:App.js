// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';

// Import components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import SpecificationForm from './components/SpecificationForm';
import OutlinePreview from './components/OutlinePreview';
import ReferenceLibrary from './components/ReferenceLibrary';
import OutlineList from './components/OutlineList';

// Import styles
import './App.css';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

function App() {
  // State variables
  const [currentOutline, setCurrentOutline] = useState(null);
  const [references, setReferences] = useState([]);
  const [outlines, setOutlines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Fetch reference outlines on component mount
  useEffect(() => {
    fetchReferences();
    fetchOutlines();
  }, []);
  
  // Fetch reference outlines
  const fetchReferences = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/references`);
      setReferences(response.data.references || []);
      setError('');
    } catch (err) {
      console.error('Error fetching references:', err);
      setError('Failed to load reference outlines');
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch generated outlines
  const fetchOutlines = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/outlines`);
      setOutlines(response.data.outlines || []);
      setError('');
    } catch (err) {
      console.error('Error fetching outlines:', err);
      setError('Failed to load generated outlines');
    } finally {
      setLoading(false);
    }
  };
  
  // Generate a new outline
  const generateOutline = async (specifications) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/generate`, specifications);
      
      if (response.data.success) {
        const newOutline = {
          ...response.data.outline,
          content: response.data.content
        };
        
        setCurrentOutline(newOutline);
        setOutlines([newOutline, ...outlines]);
        setError('');
        return newOutline;
      } else {
        throw new Error(response.data.error || 'Failed to generate outline');
      }
    } catch (err) {
      console.error('Error generating outline:', err);
      setError(err.message || 'Failed to generate outline');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  // Regenerate a specific segment
  const regenerateSegment = async (outlineId, segmentIndex, segmentSpecs) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/outlines/${outlineId}/regenerate-segment`, {
        segmentIndex,
        segmentSpecs
      });
      
      if (response.data.success) {
        const updatedOutline = {
          ...response.data.outline,
          content: response.data.content
        };
        
        setCurrentOutline(updatedOutline);
        
        // Update outlines list
        const updatedOutlines = outlines.map(outline => 
          outline.id === outlineId ? updatedOutline : outline
        );
        setOutlines(updatedOutlines);
        
        setError('');
        return updatedOutline;
      } else {
        throw new Error(response.data.error || 'Failed to regenerate segment');
      }
    } catch (err) {
      console.error('Error regenerating segment:', err);
      setError(err.message || 'Failed to regenerate segment');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  // Update an outline
  const updateOutline = async (outlineId, updates) => {
    try {
      setLoading(true);
      const response = await axios.put(`${API_BASE_URL}/outlines/${outlineId}`, updates);
      
      if (response.data.success) {
        const updatedOutline = {
          ...response.data.outline,
          content: response.data.content
        };
        
        setCurrentOutline(updatedOutline);
        
        // Update outlines list
        const updatedOutlines = outlines.map(outline => 
          outline.id === outlineId ? updatedOutline : outline
        );
        setOutlines(updatedOutlines);
        
        setError('');
        return updatedOutline;
      } else {
        throw new Error(response.data.error || 'Failed to update outline');
      }
    } catch (err) {
      console.error('Error updating outline:', err);
      setError(err.message || 'Failed to update outline');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  // Delete an outline
  const deleteOutline = async (outlineId) => {
    try {
      setLoading(true);
      const response = await axios.delete(`${API_BASE_URL}/outlines/${outlineId}`);
      
      if (response.data.success) {
        // Remove from outlines list
        const updatedOutlines = outlines.filter(outline => outline.id !== outlineId);
        setOutlines(updatedOutlines);
        
        // Clear current outline if it was deleted
        if (currentOutline && currentOutline.id === outlineId) {
          setCurrentOutline(null);
        }
        
        setError('');
        return true;
      } else {
        throw new Error(response.data.error || 'Failed to delete outline');
      }
    } catch (err) {
      console.error('Error deleting outline:', err);
      setError(err.message || 'Failed to delete outline');
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  // Export an outline
  const exportOutline = (outlineId, format) => {
    window.open(`${API_BASE_URL}/outlines/${outlineId}/export?format=${format}`, '_blank');
  };
  
  return (
    <Router>
      <div className="app">
        <Header />
        
        <div className="app-container">
          <Sidebar />
          
          <main className="content">
            {error && <div className="error-message">{error}</div>}
            
            <Routes>
              <Route 
                path="/" 
                element={
                  <div className="two-column-layout">
                    <SpecificationForm 
                      references={references}
                      onGenerate={generateOutline}
                      loading={loading}
                    />
                    <OutlinePreview 
                      outline={currentOutline}
                      onUpdate={updateOutline}
                      onRegenerateSegment={regenerateSegment}
                      onExport={exportOutline}
                      loading={loading}
                    />
                  </div>
                } 
              />
              <Route 
                path="/references" 
                element={
                  <ReferenceLibrary 
                    references={references}
                    onRefresh={fetchReferences}
                    loading={loading}
                  />
                } 
              />
              <Route 
                path="/outlines" 
                element={
                  <OutlineList 
                    outlines={outlines}
                    onSelect={setCurrentOutline}
                    onDelete={deleteOutline}
                    onExport={exportOutline}
                    loading={loading}
                  />
                } 
              />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
