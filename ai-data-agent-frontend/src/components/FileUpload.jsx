import React, { useState } from 'react';
import apiClient from '../api/apiClient';

const FileUpload = ({ setSessionId, setInitialMessage }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setError('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const allowedExtensions = ['.xlsx', '.xls', '.csv'];
      if (allowedExtensions.some(ext => file.name.endsWith(ext))) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('Please select an Excel or CSV file');
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSessionId(response.data.session_id);
      setInitialMessage(response.data.message);
    } catch (err) {
      // ✅ Improved: show server error if available
      const serverError = err.response?.data?.detail || 'Error uploading file. Please try again.';
      setError(serverError);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>📊 Upload Excel File</h2>
        <p className="upload-description">
          Drop your .xlsx, .xls, or .csv file to get started
        </p>
      </div>

      <div 
        className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'file-selected' : ''}`}
        onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <input 
          id="fileInput"
          type="file" 
          onChange={handleFileChange} 
          accept=".xlsx,.xls,.csv"
          style={{ display: 'none' }}
        />
        
        <div className="drop-zone-content">
          {selectedFile ? (
            <>
              <div className="file-icon">📄</div>
              <p className="file-name">{selectedFile.name}</p>
              <p className="change-file">Click to change</p>
            </>
          ) : (
            <>
              <div className="upload-icon">📁</div>
              <p className="drop-text">
                <strong>Click to browse</strong> or drag & drop
              </p>
            </>
          )}
        </div>
      </div>

      <button 
        className={`upload-button ${isLoading ? 'loading' : ''}`}
        onClick={handleUpload} 
        disabled={isLoading || !selectedFile}
      >
        {isLoading ? (
          <>
            <span className="loading-spinner"></span>
            Analyzing...
          </>
        ) : (
          <>
            <span className="upload-icon-btn">🚀</span>
            Upload & Analyze
          </>
        )}
      </button>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
