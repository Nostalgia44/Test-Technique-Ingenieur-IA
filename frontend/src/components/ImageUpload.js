import React, { useState } from 'react';
import './ImageUpload.css';

const ImageUpload = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [question, setQuestion] = useState('Describe this image in detail');
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      
      // Créer un aperçu
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const analyzeImage = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setAnalysis('');

    const formData = new FormData();
    formData.append('image', selectedImage);
    formData.append('question', question);

    try {
      const response = await fetch('http://localhost:5000/api/analyze-image', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setAnalysis(data.analysis);
      } else {
        setAnalysis(`Error: ${data.error}`);
      }
    } catch (error) {
      setAnalysis(`Connection error: ${error.message}`);
    }

    setLoading(false);
  };

  const clearAll = () => {
    setSelectedImage(null);
    setPreview(null);
    setAnalysis('');
    setQuestion('Describe this image in detail');
  };

  return (
    <div className="image-upload-container">
      <div className="image-upload-header">
        <h2>🖼️ Image Analysis with AI</h2>
        <p>Upload an image and ask a question to analyse it</p>
      </div>

      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            type="file"
            id="image-input"
            accept="image/*"
            onChange={handleImageChange}
            className="file-input"
          />
          <label htmlFor="image-input" className="file-input-label">
            📁 Choose an image
          </label>
        </div>

        {preview && (
          <div className="image-preview">
            <img src={preview} alt="Preview" className="preview-image" />
          </div>
        )}
      </div>

      <div className="question-section">
        <label htmlFor="question-input">Question to ask about the image:</label>
        <textarea
          id="question-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What do you want to know about this image?"
          rows="3"
          className="question-input"
        />
      </div>

      <div className="action-buttons">
        <button 
          onClick={analyzeImage} 
          disabled={!selectedImage || loading}
          className="analyze-button"
        >
          {loading ? '🔄 Analysing...' : '🔍 Analyse Image'}
        </button>
        
        <button onClick={clearAll} className="clear-button">
          🗑️ Clear
        </button>
      </div>

      {analysis && (
        <div className="analysis-result">
          <h3>📊 Analysis results :</h3>
          <div className="analysis-content">
            {analysis}
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;