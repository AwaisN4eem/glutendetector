import React, { useState, useRef, useEffect } from 'react'
import { Utensils, Loader2, CheckCircle, AlertCircle, Mic, MicOff, Calendar, Clock, Edit2, X } from 'lucide-react'
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
  const [micAvailable, setMicAvailable] = useState(false)
  
  // Date/time state
  const [useCustomDateTime, setUseCustomDateTime] = useState(false)
  const [customDate, setCustomDate] = useState(new Date().toISOString().split('T')[0])
  const [customTime, setCustomTime] = useState(new Date().toTimeString().slice(0, 5))
  
  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(!!editMeal)
  
  // Check browser compatibility and microphone availability
  useEffect(() => {
    // Check if Web Speech API is supported
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
        setMicAvailable(true)
      }
      
      recognitionInstance.onresult = (event) => {
        let interimTranscript = ''
        let finalTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          } else {
            interimTranscript += transcript
          }
        }
        
        if (finalTranscript) {
          setDescription(prev => prev + (prev ? ' ' : '') + finalTranscript.trim())
          setUsedVoiceInput(true)
        }
      }
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsRecording(false)
        setIsListening(false)
        
        let errorMessage = ''
        switch (event.error) {
          case 'not-allowed':
            errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings and try again.'
            setMicAvailable(false)
            break
          case 'no-speech':
            errorMessage = 'No speech detected. Please speak clearly and try again.'
            break
          case 'audio-capture':
            errorMessage = 'No microphone found. Please connect a microphone and try again.'
            setMicAvailable(false)
            break
          case 'network':
            errorMessage = 'Network error. Please check your internet connection.'
            break
          case 'service-not-allowed':
            errorMessage = 'Speech recognition service is not available. Please try again later.'
            break
          default:
            errorMessage = `Speech recognition error: ${event.error}. Please try again.`
        }
        
        if (errorMessage) {
          setError(errorMessage)
          // Clear error after 5 seconds
          setTimeout(() => setError(null), 5000)
        }
      }
      
      recognitionInstance.onend = () => {
        setIsRecording(false)
        setIsListening(false)
      }
      
      setRecognition(recognitionInstance)
      recognitionRef.current = recognitionInstance
      
      // Check microphone availability
      navigator.mediaDevices?.getUserMedia({ audio: true })
        .then(() => {
          setMicAvailable(true)
        })
        .catch((err) => {
          console.log('Microphone check:', err)
          // Don't set error here, just mark as unavailable
          // User will get error when they try to use it
        })
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
  
  // Get browser name for better error messages
  const getBrowserName = () => {
    const userAgent = navigator.userAgent.toLowerCase()
    if (userAgent.includes('chrome') && !userAgent.includes('edg')) return 'Chrome'
    if (userAgent.includes('edg')) return 'Edge'
    if (userAgent.includes('firefox')) return 'Firefox'
    if (userAgent.includes('safari') && !userAgent.includes('chrome')) return 'Safari'
    return 'your browser'
  }
  
  // Voice recording handlers
  const startRecording = () => {
    if (!speechSupported) {
      const browserName = getBrowserName()
      setError(`Voice input is not supported in ${browserName}. Please use Google Chrome or Microsoft Edge for voice input, or type your meal description instead.`)
      setTimeout(() => setError(null), 8000)
      return
    }
    
    if (!recognitionRef.current) {
      setError('Speech recognition failed to initialize. Please refresh the page and try again.')
      return
    }
    
    try {
      setIsRecording(true)
      setError(null)
      recognitionRef.current.start()
    } catch (err) {
      console.error('Error starting recognition:', err)
      
      // Check if recognition is already running
      if (err.message?.includes('already started') || err.name === 'InvalidStateError') {
        // Try to stop and restart
        try {
          recognitionRef.current.stop()
          setTimeout(() => {
            recognitionRef.current.start()
          }, 100)
        } catch (retryErr) {
          setError('Voice recognition is already running. Please wait a moment and try again.')
          setIsRecording(false)
        }
      } else {
        setError('Failed to start voice recording. Please check your microphone permissions and try again.')
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
    
    // Stop recording if active
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
      // Build timestamp if custom date/time is used
      let timestamp = null
      if (useCustomDateTime) {
        const dateTimeString = `${customDate}T${customTime}:00`
        timestamp = new Date(dateTimeString).toISOString()
      }
      
      let response
      if (isEditMode && editMeal) {
        // Update existing meal
        response = await api.updateMeal(editMeal.id, {
          description: description.trim(),
          meal_type: mealType,
          input_method: usedVoiceInput ? 'voice' : 'text',
          timestamp: timestamp
        })
      } else {
        // Create new meal
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
  
  const getGlutenRiskColor = (score) => {
    if (score >= 70) return { text: 'text-error-700', bg: 'bg-error-50', border: 'border-error-200' }
    if (score >= 30) return { text: 'text-warning-700', bg: 'bg-warning-50', border: 'border-warning-200' }
    return { text: 'text-success-700', bg: 'bg-success-50', border: 'border-success-200' }
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-3 bg-primary-50 rounded-lg">
              <Utensils className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">
                {isEditMode ? 'Edit Meal' : 'Log Meal'}
              </h2>
              <p className="text-sm text-neutral-600">
                {isEditMode ? 'Update meal details and AI will re-analyze' : 'Track your food intake with AI-powered gluten detection'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Custom Date/Time Toggle */}
          <div>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useCustomDateTime}
                onChange={(e) => setUseCustomDateTime(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-slate-900 flex items-center space-x-1">
                <Calendar className="w-4 h-4" />
                <span>Use custom date and time</span>
              </span>
            </label>
            
            {useCustomDateTime && (
              <div className="mt-3 grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="customDate" className="block text-xs font-medium text-neutral-700 mb-1">
                    Date
                  </label>
                  <input
                    type="date"
                    id="customDate"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-slate-900"
                  />
                </div>
                <div>
                  <label htmlFor="customTime" className="block text-xs font-medium text-neutral-700 mb-1">
                    Time
                  </label>
                  <input
                    type="time"
                    id="customTime"
                    value={customTime}
                    onChange={(e) => setCustomTime(e.target.value)}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-slate-900"
                  />
                </div>
              </div>
            )}
          </div>
          {/* Meal Type */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-3">
              Meal Type
            </label>
            <div className="grid grid-cols-4 gap-3">
              {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setMealType(type)}
                  className={`px-4 py-3 rounded-lg font-medium capitalize transition-colors ${
                    mealType === type
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          {/* Description */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="description" className="block text-sm font-medium text-slate-900">
                Meal Description
              </label>
              {/* Voice Input Button */}
              <div className="flex items-center space-x-2">
                {speechSupported && (
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={loading}
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      isRecording || isListening
                        ? 'bg-error-100 text-error-700 hover:bg-error-200 animate-pulse'
                        : 'bg-primary-50 text-primary-700 hover:bg-primary-100'
                    } disabled:opacity-50 disabled:cursor-not-allowed shadow-sm`}
                    title={
                      isRecording || isListening
                        ? 'Click to stop recording'
                        : 'Click to start voice input (speak your meal description)'
                    }
                  >
                    {isRecording || isListening ? (
                      <>
                        <MicOff className="w-4 h-4" />
                        <span>{isListening ? 'Listening...' : 'Stop'}</span>
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4" />
                        <span>Voice Input</span>
                      </>
                    )}
                  </button>
                )}
                {!speechSupported && (
                  <div className="flex items-center space-x-1 text-xs text-neutral-500" title="Voice input requires Chrome or Edge browser">
                    <Mic className="w-3 h-3 opacity-50" />
                    <span>Voice not available</span>
                  </div>
                )}
              </div>
            </div>
            <textarea
              id="description"
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Sandwich with wheat bread, turkey, lettuce, and tomato. Also had chips and an apple."
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none text-slate-900 placeholder-neutral-400"
              required
            />
            <p className="text-xs text-neutral-500 mt-2">
              Include all ingredients, preparation methods, and brands when possible for accurate analysis.
              {speechSupported && (
                <span className="block mt-1">
                  💡 Tip: Click "Voice Input" to speak your meal description (works best in Chrome or Edge).
                </span>
              )}
            </p>
          </div>
          
          {/* Submit Button */}
          <div className="flex space-x-3">
            {isEditMode && onCancelEdit && (
              <button
                type="button"
                onClick={onCancelEdit}
                className="flex-1 px-6 py-3 bg-neutral-100 text-neutral-700 rounded-lg hover:bg-neutral-200 flex items-center justify-center space-x-2 transition-colors font-medium"
              >
                <X className="w-5 h-5" />
                <span>Cancel</span>
              </button>
            )}
            <button
              type="submit"
              disabled={loading || !description.trim() || isRecording}
              className={`${isEditMode && onCancelEdit ? 'flex-1' : 'w-full'} px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors font-medium shadow-sm`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Analyzing...</span>
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
                      <span>Log Meal</span>
                    </>
                  )}
                </>
              )}
            </button>
          </div>
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
                <p className="font-medium text-success-900">Meal Logged Successfully</p>
                <p className="text-sm text-success-700 mt-1">AI analysis complete</p>
              </div>
            </div>
            
            {/* Analysis Results */}
            <div className="p-6 bg-neutral-50 border border-neutral-200 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Gluten Risk Analysis</h3>
                <div className={`px-4 py-2 rounded-lg border ${getGlutenRiskColor(result.gluten_risk_score).bg} ${getGlutenRiskColor(result.gluten_risk_score).border}`}>
                  <span className={`font-semibold text-xl ${getGlutenRiskColor(result.gluten_risk_score).text}`}>
                    {result.gluten_risk_score}/100
                  </span>
                </div>
              </div>
              
              {result.detected_foods && result.detected_foods.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-neutral-700 mb-2">Detected Foods:</p>
                  <div className="flex flex-wrap gap-2">
                    {result.detected_foods.map((food, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-white border border-neutral-300 rounded-lg text-sm text-slate-900">
                        {typeof food === 'string' ? food : food.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {result.contains_gluten && (
                <div className="p-4 bg-error-50 border border-error-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-error-900 mb-1">Contains Gluten</p>
                      {result.gluten_sources && result.gluten_sources.length > 0 && (
                        <p className="text-sm text-error-700">
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
      
      {/* Tips */}
      <div className="mt-6 p-6 bg-neutral-50 border border-neutral-200 rounded-xl">
        <h3 className="font-semibold text-slate-900 mb-3">Guidelines for Accurate Tracking</h3>
        <ul className="text-sm text-neutral-700 space-y-2">
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">•</span>
            <span>Include all ingredients, even small ones</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">•</span>
            <span>Mention if something is gluten-free (e.g., "gluten-free bread")</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">•</span>
            <span>Note sauces and condiments (they often contain hidden gluten)</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">•</span>
            <span>Log meals as soon as possible for accurate timing correlation</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-primary-600 font-medium">•</span>
            <span>Consider using the Photo Upload feature for faster, more accurate logging</span>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default LogMeal
