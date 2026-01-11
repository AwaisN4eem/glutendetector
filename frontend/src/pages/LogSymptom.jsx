import React, { useState } from 'react'
import { Loader2, AlertCircle, Clock, Activity, CheckCircle2 } from 'lucide-react'
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
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-rose-500/20 border border-rose-500/30 rounded-xl flex items-center justify-center glow-green">
            <Activity className="w-6 h-6 text-rose-400 stroke-2" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Log Symptom</h1>
            <p className="text-sm text-gray-400 mt-1">Track symptoms with AI-powered analysis</p>
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Description */}
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-3">
              Symptom Description
            </label>
            <textarea
              id="description"
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Example: Bloating 3 hours after lunch"
              className="w-full px-4 py-3 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white placeholder-gray-500 resize-y min-h-[120px] transition-all"
              required
            />
          </div>
          
          {/* Severity Slider */}
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
            <label htmlFor="severity" className="block text-sm font-medium text-gray-300 mb-4">
              Severity (0-10)
            </label>
            <div className="mb-4">
              <div className="inline-block px-5 py-2.5 bg-emerald-500/20 border border-emerald-500/30 rounded-xl shadow-lg glow-green">
                <span className="font-semibold text-emerald-400 text-sm">
                  Current: {severity}
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
              className="w-full h-3 bg-[#0a0e1a] rounded-full appearance-none cursor-pointer shadow-inner"
              style={{
                background: `linear-gradient(to right, #10b981 0%, #10b981 ${(severity / 10) * 100}%, #1a1f2e ${(severity / 10) * 100}%, #1a1f2e 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-400 mt-3">
              <span>0 - None</span>
              <span>5 - Moderate</span>
              <span>10 - Severe</span>
            </div>
          </div>
          
          {/* Analysis Preview */}
          {description.trim() && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 glow-green">
              <p className="text-xs text-gray-400 mb-2 font-medium">Analysis Preview</p>
              <p className="text-sm text-gray-300">
                Analysis will appear after submission
              </p>
            </div>
          )}
          
          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !description.trim()}
            className="w-full px-6 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all duration-300 font-medium shadow-xl glow-green-strong hover:scale-105 transform"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Activity className="w-5 h-5" />
                <span>Save Symptom</span>
              </>
            )}
          </button>
        </form>
        
        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start space-x-3 glow-green">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
            <div>
              <p className="font-medium text-white">Error</p>
              <p className="text-sm text-gray-400 mt-1">{error}</p>
            </div>
          </div>
        )}
        
        {/* Success + Results */}
        {success && result && (
          <div className="space-y-4">
            <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-xl p-4 flex items-center space-x-3 shadow-xl glow-green">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
              <div>
                <p className="font-medium text-white">Symptom logged successfully</p>
                <p className="text-xs text-gray-400 mt-1">Analysis complete</p>
              </div>
            </div>
            
            {/* Analysis Results */}
            <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 space-y-4 shadow-xl glow-green">
              <div className="flex items-center justify-between pb-4 border-b border-emerald-500/20">
                <h3 className="text-lg font-bold text-white">Analysis Results</h3>
                <span className="px-4 py-2 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl text-xs font-medium text-emerald-400 shadow-sm glow-green">
                  {result.severity}/10
                </span>
              </div>
              
              {result.symptom_type && (
                <div className="bg-[#0a0e1a] rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-xs text-gray-400 mb-2 font-medium">Detected Symptom</p>
                  <p className="text-sm text-white capitalize font-medium">
                    {result.symptom_type.replace('_', ' ')}
                  </p>
                </div>
              )}
              
              {result.time_context && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 glow-green">
                  <div className="flex items-start space-x-3">
                    <Clock className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5 stroke-2" />
                    <div>
                      <p className="text-xs text-gray-400 mb-1 font-medium">Time Context</p>
                      <p className="text-sm text-gray-300 capitalize">{result.time_context}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {result.sentiment_score !== null && (
                <div className="bg-[#0a0e1a] rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-xs text-gray-400 mb-2 font-medium">Sentiment Analysis</p>
                  <p className="text-sm text-white">{result.sentiment_score.toFixed(2)}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LogSymptom
