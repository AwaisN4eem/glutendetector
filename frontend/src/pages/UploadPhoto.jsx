import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Upload, Loader2, AlertCircle, X, Camera, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import ExplainButton from '../components/ExplainButton'

const UploadPhoto = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const dropZoneRef = useRef(null)
  const previewUrlRef = useRef(null)
  
  // Process file from various sources (file input, drag-drop, paste)
  const processFile = useCallback((file) => {
    if (!file) return false
    
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPG, PNG, etc.)')
      return false
    }
    
    if (file.size > 10 * 1024 * 1024) {
      setError('Image upload failed. Check file size (<10MB).')
      return false
    }
    
    // Clean up previous preview URL
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }
    
    // Create new preview URL
    const previewUrl = URL.createObjectURL(file)
    previewUrlRef.current = previewUrl
    
    setSelectedFile(file)
    setPreview(previewUrl)
    setResult(null)
    setError(null)
    return true
  }, [])
  
  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    processFile(file)
  }
  
  // Handle drag and drop
  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (dropZoneRef.current) {
      dropZoneRef.current.classList.add('border-emerald-500', 'bg-emerald-500/10')
    }
  }
  
  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (dropZoneRef.current) {
      dropZoneRef.current.classList.remove('border-emerald-500', 'bg-emerald-500/10')
    }
  }
  
  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (dropZoneRef.current) {
      dropZoneRef.current.classList.remove('border-emerald-500', 'bg-emerald-500/10')
    }
    
    const files = e.dataTransfer?.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }
  
  // Add paste event listener when component mounts
  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items
      if (!items) return
      
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.indexOf('image') !== -1) {
          e.preventDefault()
          const file = item.getAsFile()
          if (file) {
            processFile(file)
          }
          break
        }
      }
    }
    
    window.addEventListener('paste', handlePaste)
    return () => {
      window.removeEventListener('paste', handlePaste)
    }
  }, [processFile])
  
  const handleUpload = async () => {
    if (!selectedFile) return
    
    setUploading(true)
    setError(null)
    
    try {
      const response = await api.uploadPhoto(selectedFile, true)
      // Clean up preview URL before clearing state
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
        previewUrlRef.current = null
      }
      setResult(response.data)
      setSelectedFile(null)
      setPreview(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Image upload failed. Check file size (<10MB).')
    } finally {
      setUploading(false)
    }
  }
  
  const handleReset = () => {
    // Clean up preview URL to prevent memory leaks
    if (preview) {
      URL.revokeObjectURL(preview)
    }
    setResult(null)
    setPreview(null)
    setSelectedFile(null)
    setError(null)
  }
  
  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview)
      }
    }
  }, [preview])
  
  const getGlutenRiskBadge = (score) => {
    if (score >= 100) {
      return { bg: 'bg-error', text: 'text-white', border: 'border-error', label: 'Critical', gradient: 'from-red-600 to-red-700' }
    }
    if (score >= 71) {
      return { bg: 'bg-error-light', text: 'text-error', border: 'border-error-border', label: 'High', gradient: 'from-red-50 to-red-100' }
    }
    if (score >= 31) {
      return { bg: 'bg-warning-light', text: 'text-warning', border: 'border-warning-border', label: 'Medium', gradient: 'from-amber-50 to-amber-100' }
    }
    return { bg: 'bg-success-light', text: 'text-success', border: 'border-success-border', label: 'Low', gradient: 'from-green-50 to-green-100' }
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white">Upload Food Photo</h1>
          <p className="text-sm text-gray-400 mt-2">
            Computer vision analysis for automatic food detection and gluten risk assessment
          </p>
        </div>
        
        {/* Upload Area */}
        {!result && (
          <div>
            <label 
              htmlFor="photo-upload"
              ref={dropZoneRef}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className="flex flex-col items-center justify-center w-full h-96 border-2 border-dashed border-emerald-500/30 rounded-2xl cursor-pointer hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all bg-[#1a1f2e] shadow-xl"
            >
              {preview ? (
                <div className="relative w-full h-full flex items-center justify-center p-4">
                  <img 
                    src={preview} 
                    alt="Preview" 
                    className="max-h-full max-w-full object-contain rounded-card shadow-lg"
                  />
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleReset()
                    }}
                    className="absolute top-4 right-4 p-2 bg-[#0a0e1a] rounded-xl hover:bg-[#1a1f2e] transition-colors border border-emerald-500/20 shadow-lg"
                    aria-label="Remove image"
                  >
                    <X className="w-4 h-4 text-gray-400 hover:text-emerald-400" />
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-20 h-20 bg-emerald-500/20 border border-emerald-500/30 rounded-full flex items-center justify-center mb-6">
                    <Camera className="w-10 h-10 text-emerald-400" />
                  </div>
                  <p className="text-base font-medium text-white mb-2">Drag and drop, paste, or select photo</p>
                  <p className="text-xs text-gray-400">Supported: JPG, PNG (max 10MB)</p>
                </div>
              )}
              <input 
                id="photo-upload"
                type="file" 
                className="hidden" 
                accept="image/*"
                onChange={handleFileSelect}
              />
            </label>
          </div>
        )}
        
        {/* Upload Button */}
        {selectedFile && !result && (
          <div className="flex justify-center">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-all duration-300 font-medium shadow-xl hover:scale-105 transform"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Processing image...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 stroke-2" />
                  <span>Upload Photo</span>
                </>
              )}
            </button>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start space-x-3 shadow-xl">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
            <div className="flex-1">
              <p className="font-medium text-white">Upload Error</p>
              <p className="text-sm text-gray-400 mt-1">{error}</p>
            </div>
          </div>
        )}
        
        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Success Header */}
            <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3 shadow-xl">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-medium text-white">Analysis Complete</p>
                <p className="text-xs text-gray-400 mt-1">
                  Processed in {result.processing_time?.toFixed(2) || 'N/A'}s
                </p>
              </div>
            </div>
            
            {/* Image Preview */}
            {result.photo_url && (
              <div className="border border-emerald-500/20 rounded-2xl p-4 bg-[#1a1f2e] shadow-xl glow-green">
                <img 
                  src={result.photo_url} 
                  alt="Uploaded food" 
                  className="w-full max-h-96 object-contain rounded-xl"
                />
              </div>
            )}
            
            {/* Detection Results */}
            <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
              <h2 className="text-lg font-bold text-white mb-6 flex items-center space-x-2">
                <Camera className="w-5 h-5 text-emerald-400" />
                <span>Detection Results</span>
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-[#0a0e1a] rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-xs text-gray-400 mb-2">Detected Foods</p>
                  <p className="text-sm text-white font-medium">
                    {result.detected_foods && result.detected_foods.length > 0
                      ? result.detected_foods.map(f => typeof f === 'string' ? f : f.name).join(', ')
                      : result.primary_food || 'Unknown'}
                  </p>
                </div>
                
                <div className={`bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 rounded-xl p-4 border border-emerald-500/30 glow-green`}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-gray-400">Gluten Risk</p>
                    <ExplainButton
                      type="gluten-risk"
                      foodName={result.detected_foods && result.detected_foods.length > 0
                        ? (typeof result.detected_foods[0] === 'string' ? result.detected_foods[0] : result.detected_foods[0].name)
                        : result.primary_food || 'Unknown'}
                      glutenRisk={result.gluten_risk_score}
                      mealDescription={result.detected_foods && result.detected_foods.length > 0
                        ? result.detected_foods.map(f => typeof f === 'string' ? f : f.name).join(', ')
                        : result.primary_food || 'Unknown'}
                      className="text-xs"
                    />
                  </div>
                  <div className="flex items-center space-x-3">
                    <p className="text-[32px] font-semibold text-emerald-400">
                      {result.gluten_risk_score}/100
                    </p>
                    <span className={`px-3 py-1.5 rounded-xl text-xs font-medium border shadow-sm glow-green ${getGlutenRiskBadge(result.gluten_risk_score).bg} ${getGlutenRiskBadge(result.gluten_risk_score).text} ${getGlutenRiskBadge(result.gluten_risk_score).border}`}>
                      {getGlutenRiskBadge(result.gluten_risk_score).label}
                    </span>
                  </div>
                </div>
              </div>
              
              {result.processing_time && (
                <div className="mt-4 pt-4 border-t border-emerald-500/20">
                  <p className="text-xs text-gray-400">Processing Time: {result.processing_time.toFixed(2)}s</p>
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="flex justify-center space-x-3">
              <button
                onClick={handleReset}
                className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 font-medium shadow-xl glow-green hover:scale-105 transform"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default UploadPhoto
