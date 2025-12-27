import React, { useState, useEffect } from 'react'
import { Clock, Utensils, Activity, Loader2, AlertCircle, Calendar } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { format } from 'date-fns'

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
  
  const getGlutenRiskColor = (score) => {
    if (score >= 70) return 'bg-error-50 text-error-700 border-error-200'
    if (score >= 30) return 'bg-warning-50 text-warning-700 border-warning-200'
    return 'bg-success-50 text-success-700 border-success-200'
  }
  
  const getSeverityColor = (sev) => {
    if (sev >= 7) return 'bg-error-50 text-error-700 border-error-200'
    if (sev >= 4) return 'bg-warning-50 text-warning-700 border-warning-200'
    return 'bg-success-50 text-success-700 border-success-200'
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Timeline</h1>
          <p className="text-neutral-600 mt-2">Complete meal and symptom history</p>
        </div>
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-neutral-500" />
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white text-slate-900"
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
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
            <p className="text-neutral-600">Loading timeline data...</p>
          </div>
        </div>
      )}
      
      {/* Error */}
      {error && (
        <div className="bg-error-50 border border-error-200 rounded-xl p-6 flex items-start space-x-3">
          <AlertCircle className="w-6 h-6 text-error-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-error-900">Error Loading Timeline</p>
            <p className="text-sm text-error-700 mt-1">{error}</p>
          </div>
        </div>
      )}
      
      {/* Timeline */}
      {!loading && !error && (
        <>
          {timeline.length === 0 ? (
            <div className="bg-white border border-neutral-200 rounded-xl p-12 text-center">
              <Clock className="w-16 h-16 text-neutral-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No Entries Yet</h3>
              <p className="text-neutral-600 mb-6">Start logging meals and symptoms to build your timeline</p>
              <div className="flex justify-center space-x-3">
                <Link 
                  to="/upload-photo" 
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  Upload Photo
                </Link>
                <Link 
                  to="/log-meal" 
                  className="px-4 py-2 bg-white text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-medium"
                >
                  Log Meal
                </Link>
              </div>
            </div>
          ) : (
            <div className="relative">
              {/* Vertical Line */}
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-neutral-200"></div>
              
              {/* Timeline Entries */}
              <div className="space-y-6">
                {timeline.map((entry, idx) => (
                  <div key={idx} className="relative pl-20">
                    {/* Icon Circle */}
                    <div className={`absolute left-4 w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-sm ${
                      entry.entry_type === 'meal' 
                        ? 'bg-primary-100 text-primary-600' 
                        : 'bg-error-100 text-error-600'
                    }`}>
                      {entry.entry_type === 'meal' ? (
                        <Utensils className="w-4 h-4" />
                      ) : (
                        <Activity className="w-4 h-4" />
                      )}
                    </div>
                    
                    {/* Content Card */}
                    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="text-xs text-neutral-500 font-medium uppercase tracking-wide mb-1">
                            {entry.entry_type}
                          </p>
                          <p className="text-sm text-neutral-600">
                            {format(new Date(entry.timestamp), 'MMM d, yyyy • h:mm a')}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          {entry.gluten_risk !== null && (
                            <span className={`px-3 py-1 rounded-lg font-semibold text-xs border ${getGlutenRiskColor(entry.gluten_risk)}`}>
                              Gluten: {entry.gluten_risk.toFixed(0)}/100
                            </span>
                          )}
                          {entry.severity !== null && (
                            <span className={`px-3 py-1 rounded-lg font-semibold text-xs border ${getSeverityColor(entry.severity)}`}>
                              Severity: {entry.severity.toFixed(1)}/10
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-slate-900 font-medium mb-2">{entry.description}</p>
                      {entry.detailed_description && (
                        <div className="mt-3 p-4 bg-primary-50 border-l-4 border-primary-500 rounded-lg">
                          <div className="flex items-start space-x-2">
                            <div className="flex-shrink-0 mt-0.5">
                              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </div>
                            <div className="flex-1">
                              <p className="text-xs font-semibold text-primary-800 uppercase tracking-wide mb-1">Nutritional Analysis</p>
                              <p className="text-sm text-primary-900 leading-relaxed whitespace-pre-line">
                                {entry.detailed_description}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Summary Stats */}
          {timeline.length > 0 && (
            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-semibold text-primary-600">
                  {timeline.filter(e => e.entry_type === 'meal').length}
                </p>
                <p className="text-sm text-neutral-600 mt-1">Meals</p>
              </div>
              <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-semibold text-error-600">
                  {timeline.filter(e => e.entry_type === 'symptom').length}
                </p>
                <p className="text-sm text-neutral-600 mt-1">Symptoms</p>
              </div>
              <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-semibold text-warning-600">
                  {timeline.filter(e => e.entry_type === 'meal' && e.gluten_risk >= 70).length}
                </p>
                <p className="text-sm text-neutral-600 mt-1">High Gluten</p>
              </div>
              <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-semibold text-error-600">
                  {timeline.filter(e => e.entry_type === 'symptom' && e.severity >= 7).length}
                </p>
                <p className="text-sm text-neutral-600 mt-1">Severe Symptoms</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Timeline
