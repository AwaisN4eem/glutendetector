import React, { useState, useEffect } from 'react'
import { Loader2, AlertCircle, Clock, Utensils, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { format } from 'date-fns'
import ExplainButton from '../components/ExplainButton'

const Timeline = () => {
  const [loading, setLoading] = useState(true)
  const [timeline, setTimeline] = useState([])
  const [days, setDays] = useState(7)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    loadTimeline()
  }, [days])
  
  const loadTimeline = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getTimeline(days)
      setTimeline(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load timeline')
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
    <div className="max-w-4xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Timeline</h1>
          </div>
          <div className="flex items-center space-x-2">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-4 py-2 bg-[#1a1f2e] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white shadow-sm"
          >
              <option value={3}>Last 3 days</option>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>
        
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mx-auto mb-4 stroke-2" />
              <p className="text-sm text-gray-400">Loading timeline data...</p>
            </div>
          </div>
        )}
        
        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
            <div>
              <p className="font-medium text-white">Error Loading Timeline</p>
              <p className="text-sm text-gray-400 mt-1">{error}</p>
            </div>
          </div>
        )}
        
        {/* Timeline */}
        {!loading && !error && (
          <>
            {timeline.length === 0 ? (
              <div className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl p-12 text-center shadow-xl">
                <div className="w-16 h-16 bg-emerald-500/20 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Clock className="w-8 h-8 text-emerald-400" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">No entries yet</h3>
                <p className="text-sm text-gray-400 mb-8">Start logging meals and symptoms to build your timeline</p>
                <div className="flex justify-center space-x-3">
                  <Link 
                    to="/upload-photo" 
                    className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 font-medium shadow-xl hover:scale-105 transform"
                  >
                    Upload Photo
                  </Link>
                  <Link 
                    to="/log-meal" 
                    className="px-6 py-3 bg-transparent text-emerald-400 border-2 border-emerald-500/30 rounded-xl hover:bg-emerald-500/10 transition-all duration-300 font-medium"
                  >
                    Log Meal
                  </Link>
                </div>
              </div>
            ) : (
              <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl shadow-xl">
                <div className="divide-y divide-emerald-500/20">
                  {timeline.map((entry, idx) => (
                    <div key={idx} className="p-5 hover:bg-emerald-500/5 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            {entry.entry_type === 'meal' ? (
                              <div className="w-8 h-8 bg-emerald-500/20 border border-emerald-500/30 rounded-lg flex items-center justify-center">
                                <Utensils className="w-4 h-4 text-emerald-400 stroke-2" />
                              </div>
                            ) : (
                              <div className="w-8 h-8 bg-rose-500/20 border border-rose-500/30 rounded-lg flex items-center justify-center">
                                <Activity className="w-4 h-4 text-rose-400 stroke-2" />
                              </div>
                            )}
                            <p className="text-xs text-gray-400">
                              {format(new Date(entry.timestamp), 'MMM d, yyyy h:mm a')}
                            </p>
                          </div>
                          <p className="text-sm font-medium text-white mb-2">
                            {entry.description}
                          </p>
                          {entry.id && (
                            <ExplainButton
                              type="data-point"
                              entryType={entry.entry_type}
                              entryId={entry.id}
                              className="mt-2 text-xs"
                            />
                          )}
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          {entry.gluten_risk !== null && (
                            <span className={`px-3 py-1.5 rounded-xl text-xs font-medium border shadow-sm ${getGlutenRiskBadge(entry.gluten_risk).bg} ${getGlutenRiskBadge(entry.gluten_risk).text} ${getGlutenRiskBadge(entry.gluten_risk).border}`}>
                              {entry.gluten_risk.toFixed(0)}/100
                            </span>
                          )}
                          {entry.severity !== null && (
                            <span className="px-3 py-1.5 rounded-xl text-xs font-medium border bg-[#0a0e1a] text-gray-300 border-emerald-500/20 shadow-sm">
                              {entry.severity.toFixed(1)}/10
                            </span>
                          )}
                        </div>
                      </div>
                      {entry.detailed_description && (
                        <div className="mt-4 p-4 bg-emerald-500/10 border-l-4 border-emerald-500/50 rounded-xl">
                          <p className="text-xs text-gray-400 mb-2 font-medium">Detailed Description</p>
                          <p className="text-sm text-gray-300 whitespace-pre-line">
                            {entry.detailed_description}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Timeline
