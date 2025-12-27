import React, { useState } from 'react'
import { Camera, Upload, Loader2, CheckCircle, AlertCircle, X } from 'lucide-react'
import { api } from '../api/client'

const UploadPhoto = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
      setError(null)
    }
  }
  
  const handleUpload = async () => {
    if (!selectedFile) return
    
    setUploading(true)
    setError(null)
    
    try {
      const response = await api.uploadPhoto(selectedFile, true)
      setResult(response.data)
      setSelectedFile(null)
      setPreview(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }
  
  const handleReset = () => {
    setResult(null)
    setPreview(null)
    setSelectedFile(null)
    setError(null)
  }
  
  const getGlutenRiskColor = (score) => {
    if (score >= 70) return { text: 'text-error-700', bg: 'bg-error-50', border: 'border-error-200' }
    if (score >= 30) return { text: 'text-warning-700', bg: 'bg-warning-50', border: 'border-warning-200' }
    return { text: 'text-success-700', bg: 'bg-success-50', border: 'border-success-200' }
  }
  
  const getGlutenRiskLabel = (score) => {
    if (score >= 70) return 'High Risk'
    if (score >= 30) return 'Moderate Risk'
    return 'Low Risk'
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-3 bg-primary-50 rounded-lg">
              <Camera className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Photo Analysis</h2>
              <p className="text-sm text-neutral-600">AI-powered food detection with gluten risk assessment</p>
            </div>
          </div>
        </div>
        
        {/* Upload Area */}
        {!result && (
          <div className="mb-8">
            <label 
              htmlFor="photo-upload"
              className="flex flex-col items-center justify-center w-full h-80 border-2 border-dashed border-neutral-300 rounded-xl cursor-pointer hover:border-primary-400 hover:bg-primary-50/50 transition-colors bg-neutral-50"
            >
              {preview ? (
                <div className="relative w-full h-full flex items-center justify-center">
                  <img 
                    src={preview} 
                    alt="Preview" 
                    className="max-h-full max-w-full object-contain rounded-lg"
                  />
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleReset()
                    }}
                    className="absolute top-2 right-2 p-2 bg-white rounded-full shadow-lg hover:bg-neutral-100 transition-colors"
                    aria-label="Remove image"
                  >
                    <X className="w-4 h-4 text-neutral-600" />
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <Upload className="w-16 h-16 text-neutral-400 mb-4" />
                  <p className="text-lg font-medium text-slate-900 mb-2">Click to upload photo</p>
                  <p className="text-sm text-neutral-500">PNG, JPG, or WEBP (max 10MB)</p>
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
          <div className="flex justify-center mb-6">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors font-medium shadow-sm"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Camera className="w-5 h-5" />
                  <span>Analyze Photo</span>
                </>
              )}
            </button>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-error-900">Upload Error</p>
              <p className="text-sm text-error-700 mt-1">{error}</p>
            </div>
          </div>
        )}
        
        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Success Header */}
            <div className="flex items-center space-x-3 p-4 bg-success-50 border border-success-200 rounded-lg">
              <CheckCircle className="w-6 h-6 text-success-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-medium text-success-900">Analysis Complete</p>
                <p className="text-sm text-success-700 mt-1">
                  Processed in {result.processing_time?.toFixed(2) || 'N/A'}s
                </p>
              </div>
            </div>
            
            {/* Primary Food & Risk */}
            <div className="p-6 bg-neutral-50 rounded-lg border border-neutral-200">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-medium text-neutral-600 mb-1">Primary Food Detected</h3>
                  <p className="text-2xl font-semibold text-slate-900">{result.primary_food}</p>
                </div>
                <div className={`px-4 py-3 rounded-lg border ${getGlutenRiskColor(result.gluten_risk_score).bg} ${getGlutenRiskColor(result.gluten_risk_score).border}`}>
                  <p className="text-xs font-medium text-neutral-600 mb-1">Gluten Risk</p>
                  <p className={`text-2xl font-semibold ${getGlutenRiskColor(result.gluten_risk_score).text}`}>
                    {result.gluten_risk_score}/100
                  </p>
                  <p className={`text-xs font-medium mt-1 ${getGlutenRiskColor(result.gluten_risk_score).text}`}>
                    {getGlutenRiskLabel(result.gluten_risk_score)}
                  </p>
                </div>
              </div>
            </div>
            
            {/* All Detected Foods */}
            {result.detected_foods && result.detected_foods.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Detected Foods</h3>
                <div className="space-y-3">
                  {result.detected_foods.map((food, idx) => {
                    const riskColor = getGlutenRiskColor(food.gluten_risk)
                    return (
                      <div key={idx} className="p-4 bg-white border border-neutral-200 rounded-lg flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-slate-900">{food.name}</p>
                          <p className="text-sm text-neutral-500 mt-1">
                            Confidence: {(food.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                        <span className={`px-3 py-1.5 rounded-lg font-semibold text-sm ${riskColor.bg} ${riskColor.text} ${riskColor.border} border`}>
                          {food.gluten_risk}/100
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
            
            {/* High Risk Warning */}
            {result.gluten_risk_score >= 70 && (
              <div className="p-4 bg-error-50 border border-error-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-error-900 mb-1">High Gluten Risk Detected</p>
                    <p className="text-sm text-error-700">
                      This meal likely contains gluten and has been automatically logged to your timeline.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Next Action */}
            <div className="flex justify-center pt-4">
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium shadow-sm"
              >
                Analyze Another Photo
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Information Section */}
      <div className="mt-6 p-6 bg-neutral-50 border border-neutral-200 rounded-xl">
        <h3 className="font-semibold text-slate-900 mb-3">How It Works</h3>
        <ul className="text-sm text-neutral-700 space-y-2">
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">1.</span>
            <span>Upload a photo of your meal</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">2.</span>
            <span>AI detects food items with high accuracy</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">3.</span>
            <span>Automatically calculates gluten risk (0-100 scale)</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">4.</span>
            <span>Meal is logged to your timeline for correlation analysis</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">5.</span>
            <span>Processing typically completes in under 2 seconds</span>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default UploadPhoto
