import React, { useState, useRef, useEffect, useContext } from 'react'
import { MessageCircle, X, Send, Mic, Loader2, Database } from 'lucide-react'
import { api } from '../api/client'
import { AICoachContext } from './Layout'

const AICoach = () => {
  const aiCoachContext = useContext(AICoachContext)
  const [internalOpen, setInternalOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your AI Health Coach. I can help you understand your gluten tracking data. Ask me anything about your meals, symptoms, or patterns!",
      retrieval_stats: null
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [recognition, setRecognition] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    // Initialize Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognitionInstance = new SpeechRecognition()
      recognitionInstance.continuous = false
      recognitionInstance.interimResults = false
      recognitionInstance.lang = 'en-US'
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setInput(transcript)
        setIsListening(false)
      }
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }
      
      recognitionInstance.onend = () => {
        setIsListening(false)
      }
      
      setRecognition(recognitionInstance)
    }
  }, [])

  // Use context state if available, otherwise use internal state
  const isOpen = aiCoachContext?.isOpen !== undefined ? aiCoachContext.isOpen : internalOpen
  
  const handleToggle = (open) => {
    if (aiCoachContext?.setIsOpen) {
      aiCoachContext.setIsOpen(open)
    } else {
      setInternalOpen(open)
    }
  }
  
  // Sync internal state when context changes
  useEffect(() => {
    if (aiCoachContext?.isOpen !== undefined) {
      // Context is controlling, no need to sync
    }
  }, [aiCoachContext?.isOpen])
  
  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await api.aiCoachChat(userMessage)
      const retrieval_stats = response.data.retrieval_stats || {}
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.answer,
        retrieval_stats: retrieval_stats
      }])
      
      // Speak response (optional)
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.answer)
        utterance.rate = 0.9
        utterance.pitch = 1
        window.speechSynthesis.speak(utterance)
      }
    } catch (error) {
      console.error('AI Coach error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.',
        retrieval_stats: null
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleVoiceInput = () => {
    if (!recognition) {
      alert('Voice input is not supported in your browser. Please use Chrome or Edge.')
      return
    }

    if (isListening) {
      recognition.stop()
      setIsListening(false)
    } else {
      recognition.start()
      setIsListening(true)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating Chat Button - Only show if not using sidebar button */}
      {!isOpen && !aiCoachContext && (
        <button
          onClick={() => handleToggle(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-200 flex items-center justify-center z-50"
          aria-label="Open AI Coach"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl shadow-2xl flex flex-col z-50">
          {/* Header */}
          <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white p-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MessageCircle className="w-5 h-5" />
              <h3 className="font-semibold">AI Health Coach</h3>
            </div>
            <button
              onClick={() => handleToggle(false)}
              className="hover:bg-white/20 rounded p-1 transition-colors"
              aria-label="Close chat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0a0e1a]">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white'
                      : 'bg-[#1a1f2e] text-gray-300 border border-emerald-500/20'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
                {/* RAG Retrieval Stats Badge */}
                {msg.role === 'assistant' && msg.retrieval_stats && msg.retrieval_stats.total_items_retrieved > 0 && (
                  <div className="mt-1 px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 flex items-center space-x-1.5">
                    <Database className="w-3 h-3 text-emerald-400" />
                    <span className="text-[10px] text-emerald-300 font-medium">
                      Retrieved {msg.retrieval_stats.total_items_retrieved} items from knowledge base
                    </span>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-lg p-3">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-emerald-500/20 bg-[#1a1f2e]">
            <div className="flex items-end space-x-2">
              <button
                onClick={handleVoiceInput}
                className={`p-2 rounded-lg transition-colors ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-[#0a0e1a] text-gray-400 hover:bg-emerald-500/10 hover:text-emerald-400 border border-emerald-500/20'
                }`}
                aria-label="Voice input"
              >
                <Mic className="w-5 h-5" />
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your health data..."
                className="flex-1 min-h-[60px] max-h-[120px] p-3 border border-emerald-500/20 rounded-lg focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none resize-none bg-[#0a0e1a] text-white placeholder-gray-500"
                rows={2}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="p-2 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-lg hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default AICoach

