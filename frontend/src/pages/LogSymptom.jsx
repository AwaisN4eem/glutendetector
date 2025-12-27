import React, { useState } from 'react'
import { Activity, Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { api } from '../api/client'

const LogSymptom = () => {
  const [description, setDescription] = useState('')
  const [severity, setSeverity] = useState(5)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!description.trim()) {
      setError('Please describe your symptom')
      return
    }
    
    setLoading(true)
    setError(null)
    setSuccess(false)
    
    try {
      const response = await api.createSymptom({
        description: description.trim(),
        severity: parseFloat(severity),
        input_method: 'text'
      })
      
      setResult(response.data)
      setSuccess(true)
      setDescription('')
      setSeverity(5)
      
      setTimeout(() => {
        setSuccess(false)
        setResult(null)
      }, 5000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to log symptom')
    } finally {
      setLoading(false)
    }
  }
  
  const getSeverityColor = (sev) => {
    if (sev >= 7) return { text: 'text-error-700', bg: 'bg-error-50', border: 'border-error-200' }
    if (sev >= 4) return { text: 'text-warning-700', bg: 'bg-warning-50', border: 'border-warning-200' }
    return { text: 'text-success-700', bg: 'bg-success-50', border: 'border-success-200' }
  }
  
  const getSeverityLabel = (sev) => {
    if (sev >= 8) return 'Severe'
    if (sev >= 6) return 'Moderate-High'
    if (sev >= 4) return 'Moderate'
    if (sev >= 2) return 'Mild'
    return 'Very Mild'
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-3 bg-error-50 rounded-lg">
              <Activity className="w-6 h-6 text-error-600" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Log Symptom</h2>
              <p className="text-sm text-neutral-600">Track symptoms with AI-powered analysis</p>
            </div>
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-slate-900 mb-2">
              Symptom Description
            </label>
            <textarea
              id="description"
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Experiencing bloating about 3 hours after lunch. Also feeling tired and slightly nauseous."
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none text-slate-900 placeholder-neutral-400"
              required
            />
            <p className="text-xs text-neutral-500 mt-2">
              Include: symptom type, timing (when it started), severity, and any relevant context.
            </p>
          </div>
          
          {/* Severity Slider */}
          <div>
            <label htmlFor="severity" className="block text-sm font-medium text-slate-900 mb-3">
              Severity Level
            </label>
            <div className="mb-3">
              <div className={`inline-block px-4 py-2 rounded-lg border ${getSeverityColor(severity).bg} ${getSeverityColor(severity).border}`}>
                <span className={`font-semibold ${getSeverityColor(severity).text}`}>
                  {severity}/10 - {getSeverityLabel(severity)}
                </span>
              </div>
            </div>
            <input
              type="range"
              id="severity"
              min="0"
              max="10"
              step="0.5"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-error-600"
              style={{
                background: `linear-gradient(to right, #E53935 0%, #E53935 ${(severity / 10) * 100}%, #E0E0E0 ${(severity / 10) * 100}%, #E0E0E0 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-neutral-500 mt-2">
              <span>0 - None</span>
              <span>5 - Moderate</span>
              <span>10 - Severe</span>
            </div>
          </div>
          
          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !description.trim()}
            className="w-full px-6 py-3 bg-error-600 text-white rounded-lg hover:bg-error-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors font-medium shadow-sm"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Activity className="w-5 h-5" />
                <span>Log Symptom</span>
              </>
            )}
          </button>
        </form>
        
        {/* Error */}
        {error && (
          <div className="mt-6 p-4 bg-error-50 border border-error-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-error-900">Error</p>
              <p className="text-sm text-error-700 mt-1">{error}</p>
            </div>
          </div>
        )}
        
        {/* Success + Results */}
        {success && result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-success-50 border border-success-200 rounded-lg flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-success-900">Symptom Logged Successfully</p>
                <p className="text-sm text-success-700 mt-1">AI analysis complete</p>
              </div>
            </div>
            
            {/* Analysis Results */}
            <div className="p-6 bg-neutral-50 border border-neutral-200 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">AI Analysis</h3>
                <div className={`px-4 py-2 rounded-lg border ${getSeverityColor(result.severity).bg} ${getSeverityColor(result.severity).border}`}>
                  <span className={`font-semibold text-xl ${getSeverityColor(result.severity).text}`}>
                    {result.severity}/10
                  </span>
                </div>
              </div>
              
              {result.symptom_type && (
                <div>
                  <p className="text-sm font-medium text-neutral-700 mb-2">Primary Symptom Type:</p>
                  <span className="px-3 py-1.5 bg-white border border-neutral-300 rounded-lg text-sm text-slate-900 font-medium capitalize">
                    {result.symptom_type.replace('_', ' ')}
                  </span>
                </div>
              )}
              
              {result.extracted_symptoms && result.extracted_symptoms.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-neutral-700 mb-2">All Detected Symptoms:</p>
                  <div className="flex flex-wrap gap-2">
                    {result.extracted_symptoms.map((symptom, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-white border border-neutral-300 rounded-lg text-sm text-slate-900 capitalize">
                        {symptom.type.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {result.time_context && (
                <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <Clock className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-primary-900 mb-1">Time Context Detected</p>
                      <p className="text-sm text-primary-700 capitalize">{result.time_context}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {result.sentiment_score !== null && (
                <div>
                  <p className="text-sm font-medium text-neutral-700 mb-2">Emotional Impact:</p>
                  <div className="flex items-center space-x-3">
                    <div className="flex-1 h-2 bg-neutral-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          result.sentiment_score < -0.3 ? 'bg-error-500' : 
                          result.sentiment_score > 0.3 ? 'bg-success-500' : 'bg-warning-500'
                        }`}
                        style={{ width: `${Math.abs(result.sentiment_score) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-neutral-600 whitespace-nowrap">
                      {result.sentiment_score < -0.3 ? 'Negative' : result.sentiment_score > 0.3 ? 'Positive' : 'Neutral'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Common Symptoms Reference */}
      <div className="mt-6 p-6 bg-neutral-50 border border-neutral-200 rounded-xl">
        <h3 className="font-semibold text-slate-900 mb-3">Common Gluten-Related Symptoms</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-neutral-700">
          <div>• Bloating</div>
          <div>• Diarrhea</div>
          <div>• Constipation</div>
          <div>• Abdominal pain</div>
          <div>• Nausea</div>
          <div>• Fatigue</div>
          <div>• Headaches</div>
          <div>• Brain fog</div>
          <div>• Skin issues</div>
          <div>• Joint pain</div>
          <div>• Mood changes</div>
          <div>• Anxiety</div>
        </div>
      </div>
    </div>
  )
}

export default LogSymptom
