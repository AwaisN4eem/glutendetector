import React, { useState, useEffect } from 'react'
import { FileText, Loader2, AlertCircle, CheckCircle, XCircle, BarChart3 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { format } from 'date-fns'
import ExplainButton from '../components/ExplainButton'

const Reports = () => {
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [reports, setReports] = useState([])
  const [correlation, setCorrelation] = useState(null)
  const [error, setError] = useState(null)
  const [weeks, setWeeks] = useState(6)
  
  useEffect(() => {
    loadReports()
    loadCorrelation()
  }, [])
  
  const loadReports = async () => {
    try {
      const response = await api.getReports()
      setReports(response.data)
    } catch (err) {
      console.error('Failed to load reports:', err)
    }
  }
  
  const loadCorrelation = async () => {
    try {
      setLoading(true)
      const response = await api.getCorrelation()
      setCorrelation(response.data)
    } catch (err) {
      if (err.response?.status !== 400) {
        setError(err.response?.data?.detail || 'Failed to calculate correlation')
      }
    } finally {
      setLoading(false)
    }
  }
  
  const handleGenerateReport = async () => {
    try {
      setGenerating(true)
      setError(null)
      await api.generateReport(weeks)
      await loadReports()
      await loadCorrelation()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate report. You may need more data (minimum 10 meals and 10 symptoms).')
    } finally {
      setGenerating(false)
    }
  }
  
  return (
    <div className="max-w-5xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white">Correlation Analysis Report</h1>
          {correlation && (
            <p className="text-sm text-gray-400 mt-2">
              Generated: {format(new Date(), 'MMM d, yyyy h:mm a')}
            </p>
          )}
        </div>
        
        {/* Generate New Report */}
        <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-10 h-10 bg-emerald-500/20 border border-emerald-500/30 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-lg font-bold text-white">Generate Full Report</h3>
              </div>
              <p className="text-sm text-gray-400 mb-4">
                Requires at least 10 meals and 10 symptoms for statistical analysis
              </p>
              <div className="flex items-center space-x-3">
                <label className="text-sm font-medium text-gray-400">Analysis Period:</label>
                <select
                  value={weeks}
                  onChange={(e) => setWeeks(parseInt(e.target.value))}
                  className="px-4 py-2 bg-[#0a0e1a] border border-emerald-500/20 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none text-sm text-white shadow-sm"
                >
                  <option value={2}>2 weeks</option>
                  <option value={4}>4 weeks</option>
                  <option value={6}>6 weeks</option>
                  <option value={8}>8 weeks</option>
                  <option value={12}>12 weeks</option>
                </select>
              </div>
            </div>
            <button
              onClick={handleGenerateReport}
              disabled={generating}
              className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-all duration-300 font-medium shadow-xl hover:scale-105 transform"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5" />
                  <span>Generate Report</span>
                </>
              )}
            </button>
          </div>
          
          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start space-x-3 shadow-sm">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
              <p className="text-sm text-gray-400">{error}</p>
            </div>
          )}
        </div>
        
        {/* Current Correlation Analysis */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mx-auto mb-4 stroke-2" />
              <p className="text-sm text-gray-400">Calculating correlation...</p>
            </div>
          </div>
        )}
        
        {!loading && correlation && (
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-8 space-y-6 shadow-xl">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500/30 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white">Summary</h2>
            </div>
            
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-5 shadow-sm">
                <p className="text-xs text-gray-400 mb-2 font-medium">Data Period</p>
                <p className="text-sm text-white font-medium">
                  {correlation.start_date && correlation.end_date
                    ? `${format(new Date(correlation.start_date), 'MMM d, yyyy')} - ${format(new Date(correlation.end_date), 'MMM d, yyyy')}`
                    : 'N/A'}
                </p>
              </div>
                <div className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-5 shadow-sm">
                <p className="text-xs text-gray-400 mb-2 font-medium">Total Meals</p>
                <p className="text-2xl font-semibold text-white">{correlation.total_meals || 0}</p>
              </div>
                <div className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-5 shadow-sm">
                <p className="text-xs text-gray-400 mb-2 font-medium">Total Symptoms</p>
                <p className="text-2xl font-semibold text-white">{correlation.total_symptoms || 0}</p>
              </div>
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-gray-400 font-medium">Correlation</p>
                  {correlation.correlation_score !== null && correlation.correlation_score !== undefined && (
                    <ExplainButton
                      type="correlation"
                      correlationScore={correlation.correlation_score}
                      pValue={correlation.p_value}
                      totalMeals={correlation.total_meals || 0}
                      totalSymptoms={correlation.total_symptoms || 0}
                      className="text-xs"
                    />
                  )}
                </div>
                <p className="text-2xl font-semibold text-emerald-400">
                  {correlation.correlation_score?.toFixed(1) || 'N/A'}%
                </p>
                {correlation.p_value !== null && correlation.p_value !== undefined && (
                  <p className="text-xs text-gray-400 mt-1">
                    p&lt;{correlation.p_value < 0.001 ? '0.001' : correlation.p_value.toFixed(3)}
                  </p>
                )}
              </div>
            </div>
            
            {/* Statistical Analysis */}
            <div className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-white mb-5">Statistical Analysis</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Pearson Correlation:</span>
                  <span className="text-sm font-medium text-white">
                    {correlation.correlation_score ? (correlation.correlation_score / 100).toFixed(2) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">P-value:</span>
                  <span className="text-sm font-medium text-white">
                    {correlation.p_value !== null && correlation.p_value !== undefined
                      ? (correlation.p_value < 0.001 ? '<0.001' : correlation.p_value.toFixed(3))
                      : 'N/A'}
                    {correlation.p_value !== null && correlation.p_value < 0.05 && (
                      <span className="ml-2 text-xs text-gray-400">(Highly significant)</span>
                    )}
                  </span>
                </div>
                {correlation.confidence_interval && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-400">Confidence Interval:</span>
                    <span className="text-sm font-medium text-white">
                      {correlation.confidence_interval[0]?.toFixed(2) || 'N/A'} - {correlation.confidence_interval[1]?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Time-Lag Analysis */}
            {correlation.time_lag_hours && correlation.time_lag_hours > 0 && (
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-white mb-4">Time-Lag Analysis</h3>
                <div className="space-y-2">
                  <p className="text-sm text-white">
                    Optimal lag: {correlation.time_lag_hours} hours
                  </p>
                  <p className="text-sm text-gray-400">
                    Symptoms typically appear {correlation.time_lag_hours} hours after high-gluten meals
                  </p>
                </div>
              </div>
            )}
            
            {/* Recommendations */}
            <div className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-white mb-4">Recommendations</h3>
              <div className="space-y-2">
                <p className="text-sm text-white">
                  Based on the data, consider:
                </p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-400 ml-4">
                  <li>Elimination diet trial (2 weeks)</li>
                  <li>Consult healthcare provider</li>
                  <li>Continue tracking for 2 more weeks</li>
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* Previous Reports */}
        {reports.length > 0 && (
          <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-white mb-6">Previous Reports</h2>
            <div className="space-y-3">
              {reports.map((report) => (
                <div key={report.id} className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-5 hover:shadow-xl transition-all shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-sm text-gray-400">
                          {format(new Date(report.start_date), 'MMM d')} - {format(new Date(report.end_date), 'MMM d, yyyy')}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${
                          report.gluten_intolerance_detected 
                            ? 'bg-red-500/20 text-red-400 border-red-500/30' 
                            : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                        }`}>
                          {report.gluten_intolerance_detected ? 'Positive' : 'Negative'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400">
                        Correlation: <strong className="text-white">{report.correlation_score?.toFixed(1)}%</strong> • 
                        Meals: {report.total_meals_logged} • 
                        Symptoms: {report.total_symptoms_logged}
                      </p>
                      {report.recommendations && (
                        <p className="text-sm text-gray-400 mt-2">{report.recommendations}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Empty State */}
        {!loading && reports.length === 0 && !correlation && (
          <div className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl p-12 text-center shadow-xl">
            <div className="w-16 h-16 bg-emerald-500/20 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-emerald-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No reports yet</h3>
            <p className="text-sm text-gray-400 mb-8">
              You need at least 10 meals and 10 symptoms logged to generate your first report.
            </p>
            <div className="flex justify-center space-x-3">
              <Link 
                to="/upload-photo" 
                className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 font-medium shadow-xl hover:scale-105 transform"
              >
                Upload Photo
              </Link>
              <Link 
                to="/timeline" 
                className="px-6 py-3 bg-transparent text-emerald-400 border-2 border-emerald-500/30 rounded-xl hover:bg-emerald-500/10 transition-all duration-300 font-medium"
              >
                View Timeline
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Reports
