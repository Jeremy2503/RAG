import { useState } from 'react'
import { Upload, File, X, CheckCircle, AlertCircle, Loader, FileText, Sparkles } from 'lucide-react'
import { documentAPI } from '../services/api'

const DocumentUpload = ({ onUploadComplete }) => {
  const [file, setFile] = useState(null)
  const [documentType, setDocumentType] = useState('general')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''))
      }
      setError('')
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''))
      }
      setError('')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleRemoveFile = () => {
    setFile(null)
    setTitle('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select a file')
      return
    }

    setUploading(true)
    setError('')
    setSuccess(false)

    try {
      const tagList = tags ? tags.split(',').map((t) => t.trim()) : []
      
      const result = await documentAPI.upload(
        file,
        documentType,
        title,
        description,
        tagList
      )

      setSuccess(true)
      setFile(null)
      setTitle('')
      setDescription('')
      setTags('')
      
      if (onUploadComplete) {
        onUploadComplete(result)
      }

      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="modern-upload-container">
      <div className="upload-header">
        <div className="upload-header-content">
          <div className="upload-icon-large">
            <FileText size={32} />
          </div>
          <div>
            <h2 className="upload-title">Upload Document</h2>
            <p className="upload-subtitle">Add documents to your knowledge base</p>
          </div>
        </div>
      </div>

      <div className="upload-content">
        <form onSubmit={handleSubmit} className="modern-upload-form">
          {/* File Drop Zone */}
          <div
            className={`modern-drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {file ? (
              <div className="file-preview-modern">
                <div className="file-icon-wrapper">
                  <File size={40} />
                </div>
                <div className="file-details">
                  <div className="file-name-modern">{file.name}</div>
                  <div className="file-size-modern">{formatFileSize(file.size)}</div>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="remove-file-btn"
                  title="Remove file"
                >
                  <X size={20} />
                </button>
              </div>
            ) : (
              <div className="drop-zone-modern-content">
                <div className="upload-icon-wrapper">
                  <Upload size={48} />
                </div>
                <h3>Drop your file here</h3>
                <p>or click to browse from your computer</p>
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt,.md,.jpg,.jpeg,.png,.webp,.bmp,.tiff"
                  id="file-input-modern"
                  className="file-input-hidden"
                />
                <label htmlFor="file-input-modern" className="choose-file-btn">
                  Choose File
                </label>
                <div className="supported-formats">
                  <span>Supported: PDF, DOCX, TXT, MD, Images (JPG, PNG, WEBP, etc.)</span>
                </div>
              </div>
            )}
          </div>

          {/* Form Fields */}
          <div className="upload-fields-grid">
            {/* Document Type */}
            <div className="form-group-modern full-width">
              <label htmlFor="documentType">Document Type</label>
              <div className="select-wrapper">
                <select
                  id="documentType"
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="modern-select"
                >
                  <option value="general">General Document</option>
                  <option value="hr_policy">HR Policy</option>
                  <option value="it_policy">IT Policy</option>
                </select>
              </div>
            </div>

            {/* Title */}
            <div className="form-group-modern full-width">
              <label htmlFor="title">Document Title</label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter document title (optional)"
                className="modern-input-upload"
              />
            </div>

            {/* Description */}
            <div className="form-group-modern full-width">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of the document (optional)"
                rows="4"
                className="modern-textarea"
              />
            </div>

            {/* Tags */}
            <div className="form-group-modern full-width">
              <label htmlFor="tags">Tags</label>
              <input
                id="tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="policy, guidelines, security (comma-separated)"
                className="modern-input-upload"
              />
            </div>
          </div>

          {/* Alerts */}
          {error && (
            <div className="modern-alert error">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="modern-alert success">
              <CheckCircle size={20} />
              <span>Document uploaded successfully! AI agents can now use this information.</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || uploading}
            className="modern-upload-submit"
          >
            {uploading ? (
              <>
                <Loader size={20} className="spinner" />
                <span>Processing & Embedding...</span>
              </>
            ) : (
              <>
                <Sparkles size={20} />
                <span>Upload & Embed Document</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default DocumentUpload
