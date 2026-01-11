import React, { useState, useRef, useEffect } from 'react'
import { Loader2, AlertCircle, Mic, MicOff, Calendar, Clock, Edit2, X, Utensils, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'

const LogMeal = ({ editMeal = null, onCancelEdit = null }) => {
  const [description, setDescription] = useState('')
  const [mealType, setMealType] = useState('lunch')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  // Voice recording state
  const [isRecording, setIsRecording] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [recognition, setRecognition] = useState(null)
  const recognitionRef = useRef(null)
  const [usedVoiceInput, setUsedVoiceInput] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)
  
  // Date/time state
  const [useCustomDateTime, setUseCustomDateTime] = useState(false)
  const [customDate, setCustomDate] = useState(new Date().toISOString().split('T')[0])
  const [customTime, setCustomTime] = useState(new Date().toTimeString().slice(0, 5))
  
  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(!!editMeal)
  
  // Check browser compatibility
  useEffect(() => {
    const isSpeechSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
    setSpeechSupported(isSpeechSupported)
    
    if (isSpeechSupported) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognitionInstance = new SpeechRecognition()
      recognitionInstance.continuous = false
      recognitionInstance.interimResults = true
      recognitionInstance.lang = 'en-US'
      
      recognitionInstance.onstart = () => {
        setIsListening(true)
      }
      
      recognitionInstance.onresult = (event) => {
        let finalTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          }
        }
        
        if (finalTranscript) {
          setDescription(prev => prev + (prev ? ' ' : '') + finalTranscript.trim())
          setUsedVoiceInput(true)
        }
      }
      
      recognitionInstance.onerror = (event) => {
        setIsRecording(false)
        setIsListening(false)
        
        let errorMessage = ''
        switch (event.error) {
          case 'not-allowed':
            errorMessage = 'Microphone access denied. Enable in browser settings.'
            break
          case 'no-speech':
            errorMessage = 'No speech detected. Speak clearly and try again.'
            break
          case 'audio-capture':
            errorMessage = 'No microphone found. Connect a microphone and try again.'
            break
          default:
            errorMessage = `Speech recognition error: ${event.error}`
        }
        
        if (errorMessage) {
          setError(errorMessage)
          setTimeout(() => setError(null), 5000)
        }
      }
      
      recognitionInstance.onend = () => {
        setIsRecording(false)
        setIsListening(false)
      }
      
      setRecognition(recognitionInstance)
      recognitionRef.current = recognitionInstance
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [])
  
  // Load meal data if in edit mode
  useEffect(() => {
    if (editMeal) {
      setDescription(editMeal.description || '')
      setMealType(editMeal.meal_type || 'lunch')
      setIsEditMode(true)
      
      if (editMeal.timestamp) {
        const mealDate = new Date(editMeal.timestamp)
        setCustomDate(mealDate.toISOString().split('T')[0])
        setCustomTime(mealDate.toTimeString().slice(0, 5))
        setUseCustomDateTime(true)
      }
    }
  }, [editMeal])
  
  // Voice recording handlers
  const startRecording = () => {
    if (!speechSupported) {
      setError('Voice input is not supported in this browser. Use Chrome or Edge for voice input.')
      setTimeout(() => setError(null), 5000)
      return
    }
    
    if (!recognitionRef.current) {
      setError('Speech recognition failed to initialize. Refresh the page and try again.')
      return
    }
    
    try {
      setIsRecording(true)
      setError(null)
      recognitionRef.current.start()
    } catch (err) {
      if (err.message?.includes('already started') || err.name === 'InvalidStateError') {
        try {
          recognitionRef.current.stop()
          setTimeout(() => {
            recognitionRef.current.start()
          }, 100)
        } catch (retryErr) {
          setError('Voice recognition is already running. Wait a moment and try again.')
          setIsRecording(false)
        }
      } else {
        setError('Failed to start voice recording. Check microphone permissions.')
        setIsRecording(false)
      }
    }
  }
  
  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsRecording(false)
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (isRecording) {
      stopRecording()
    }
    
    if (!description.trim()) {
      setError('Please enter a meal description')
      return
    }
    
    setLoading(true)
    setError(null)
    setSuccess(false)
    
    try {
      let timestamp = null
      if (useCustomDateTime) {
        const dateTimeString = `${customDate}T${customTime}:00`
        timestamp = new Date(dateTimeString).toISOString()
      }
      
      let response
      if (isEditMode && editMeal) {
        response = await api.updateMeal(editMeal.id, {
          description: description.trim(),
          meal_type: mealType,
          input_method: usedVoiceInput ? 'voice' : 'text',
          timestamp: timestamp
        })
      } else {
        response = await api.createMeal({
          description: description.trim(),
          meal_type: mealType,
          input_method: usedVoiceInput ? 'voice' : 'text',
          timestamp: timestamp
        })
      }
      
      setResult(response.data)
      setSuccess(true)
      
      if (!isEditMode) {
        setDescription('')
        setUseCustomDateTime(false)
        setCustomDate(new Date().toISOString().split('T')[0])
        setCustomTime(new Date().toTimeString().slice(0, 5))
        setUsedVoiceInput(false)
      }
      
      setTimeout(() => {
        setSuccess(false)
        setResult(null)
        if (isEditMode && onCancelEdit) {
          onCancelEdit()
        }
      }, 5000)
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${isEditMode ? 'update' : 'log'} meal`)
    } finally {
      setLoading(false)
    }
  }
  
  const getGlutenRiskBadge = (score) => {
    if (score >= 100) {
      return { bg: 'bg-error', text: 'text-white', border: 'border-error', label: 'Critical' }
    }
    if (score >= 71) {
      return { bg: 'bg-error-light', text: 'text-error', border: 'border-error-border', label: 'High' }
    }
    if (score >= 31) {
      return { bg: 'bg-warning-light', text: 'text-warning', border: 'border-warning-border', label: 'Medium' }
    }
    return { bg: 'bg-success-light', text: 'text-success', border: 'border-success-border', label: 'Low' }
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500/30 rounded-xl flex items-center justify-center glow-green">
            <Utensils className="w-6 h-6 text-emerald-400 stroke-2" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Log Meal</h1>
            {isEditMode && editMeal && (
              <p className="text-sm text-gray-400 mt-1">
                Editing meal from {new Date(editMeal.timestamp).toLocaleString()}
              </p>
            )}
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Meal Description */}
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-3">
              Meal Description
            </label>
            <textarea
              id="description"
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Example: Roti with chicken curry and dal"
              className="w-full px-4 py-3 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white placeholder-gray-500 resize-y min-h-[120px] transition-all"
              required
            />
            
            {/* Voice Input Button */}
            {speechSupported && (
              <div className="mt-4">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={loading}
                  className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl border transition-all font-medium glow-green ${
                    isRecording || isListening
                      ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400 shadow-lg animate-pulse'
                      : 'bg-transparent border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/50'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isRecording || isListening ? (
                    <>
                      <MicOff className="w-5 h-5" />
                      <span>Listening...</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-5 h-5" />
                      <span>Voice Input</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
          
          {/* Meal Type */}
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Meal Type
            </label>
            <div className="grid grid-cols-4 gap-3">
              {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setMealType(type)}
                  className={`px-4 py-3 rounded-xl font-medium capitalize transition-all border ${
                    mealType === type
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white border-emerald-500 shadow-lg glow-green'
                      : 'bg-transparent text-gray-400 border border-emerald-500/20 hover:bg-emerald-500/10 hover:text-emerald-400'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          {/* Custom Date/Time */}
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl glow-green">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useCustomDateTime}
                onChange={(e) => setUseCustomDateTime(e.target.checked)}
                className="w-5 h-5 text-emerald-500 border-emerald-500/30 rounded focus:ring-emerald-500 focus:ring-2 bg-[#0a0e1a]"
              />
              <span className="text-sm text-gray-300 flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-emerald-400" />
                <span>Use custom date and time</span>
              </span>
            </label>
            
            {useCustomDateTime && (
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="customDate" className="block text-xs font-medium text-gray-400 mb-2">
                    Date
                  </label>
                  <input
                    type="date"
                    id="customDate"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white"
                  />
                </div>
                <div>
                  <label htmlFor="customTime" className="block text-xs font-medium text-gray-400 mb-2">
                    Time
                  </label>
                  <input
                    type="time"
                    id="customTime"
                    value={customTime}
                    onChange={(e) => setCustomTime(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white"
                  />
                </div>
              </div>
            )}
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
          <div className="flex space-x-3">
            {isEditMode && onCancelEdit && (
              <button
                type="button"
                onClick={onCancelEdit}
                className="flex-1 px-6 py-3 bg-transparent text-gray-400 border border-emerald-500/20 rounded-xl hover:bg-emerald-500/10 hover:text-emerald-400 transition-colors font-medium glow-green"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={loading || !description.trim() || isRecording}
              className={`${isEditMode && onCancelEdit ? 'flex-1' : 'w-full'} px-6 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all duration-300 font-medium shadow-xl glow-green-strong hover:scale-105 transform`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  {isEditMode ? (
                    <>
                      <Edit2 className="w-5 h-5" />
                      <span>Update Meal</span>
                    </>
                  ) : (
                    <>
                      <Utensils className="w-5 h-5" />
                      <span>Save Meal</span>
                    </>
                  )}
                </>
              )}
            </button>
          </div>
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
                <p className="font-medium text-white">Meal logged successfully</p>
                <p className="text-xs text-gray-400 mt-1">Analysis complete</p>
              </div>
            </div>
            
            {/* Analysis Results */}
            <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 space-y-4 shadow-xl glow-green">
              <div className="flex items-center justify-between pb-4 border-b border-emerald-500/20">
                <h3 className="text-lg font-bold text-white">Analysis Results</h3>
                <span className={`px-4 py-2 rounded-xl text-xs font-medium border shadow-sm glow-green ${getGlutenRiskBadge(result.gluten_risk_score).bg} ${getGlutenRiskBadge(result.gluten_risk_score).text} ${getGlutenRiskBadge(result.gluten_risk_score).border}`}>
                  {result.gluten_risk_score}/100
                </span>
              </div>
              
              {result.detected_foods && result.detected_foods.length > 0 && (
                <div className="bg-[#0a0e1a] rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-xs text-gray-400 mb-2 font-medium">Detected Foods</p>
                  <p className="text-sm text-gray-300">
                    {result.detected_foods.map(f => typeof f === 'string' ? f : f.name).join(', ')}
                  </p>
                </div>
              )}
              
              {result.contains_gluten && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 shadow-sm">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
                    <div>
                      <p className="text-sm font-medium text-white">Contains Gluten</p>
                      {result.gluten_sources && result.gluten_sources.length > 0 && (
                        <p className="text-xs text-gray-400 mt-1">
                          Sources: {result.gluten_sources.join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LogMeal
