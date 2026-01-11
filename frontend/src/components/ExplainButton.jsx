import React, { useState } from 'react'
import { Info, X, Loader2 } from 'lucide-react'
import { api } from '../api/client'

const ExplainButton = ({ 
  type, // 'gluten-risk', 'correlation', 'data-point'
  foodName = null,
  glutenRisk = null,
  mealDescription = null,
  correlationScore = null,
  pValue = null,
  totalMeals = 0,
  totalSymptoms = 0,
  entryType = null,
  entryId = null,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [explanation, setExplanation] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleExplain = async () => {
    if (isOpen) {
      setIsOpen(false)
      return
    }

    setLoading(true)
    setError(null)
    setIsOpen(true)

    try {
      let response
      
      if (type === 'gluten-risk') {
        response = await api.explainGlutenRisk(foodName, glutenRisk, mealDescription)
      } else if (type === 'correlation') {
        response = await api.explainCorrelation(correlationScore, pValue, totalMeals, totalSymptoms)
      } else if (type === 'data-point') {
        response = await api.explainDataPoint(entryType, entryId)
      } else {
        throw new Error('Invalid explain type')
      }

      setExplanation(response.data.explanation)
    } catch (err) {
      console.error('Explain error:', err)
      setError('Failed to generate explanation. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={handleExplain}
        className={`inline-flex items-center space-x-2 px-3 py-1.5 bg-[#1a1f2e] border border-emerald-500/30 rounded-lg text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all duration-200 shadow-sm glow-green hover:shadow-md ${className}`}
        aria-label="Explain this result"
      >
        <Info className="w-4 h-4 stroke-2" />
        <span className="text-xs font-semibold">Explain</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setIsOpen(false)}>
          <div 
            className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl shadow-2xl glow-green max-w-2xl w-full p-8 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-emerald-500/20 border border-emerald-500/30 rounded-lg flex items-center justify-center shadow-sm glow-green">
                  <Info className="w-5 h-5 text-emerald-400 stroke-2" />
                </div>
                <h3 className="text-xl font-bold text-white">Explanation</h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-10 h-10 text-emerald-400 animate-spin stroke-2 glow-green" />
              </div>
            ) : error ? (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                <p className="text-sm text-red-400 font-medium">{error}</p>
              </div>
            ) : (
              <div className="prose prose-sm max-w-none">
                <p className="text-[15px] leading-relaxed text-gray-300 whitespace-pre-wrap font-medium">{explanation}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExplainButton

