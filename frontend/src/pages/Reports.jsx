import React, { useState, useEffect } from 'react'
import { FileText, Loader2, AlertCircle, Download, TrendingUp, Calendar, CheckCircle, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { format } from 'date-fns'

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
  
  const getCorrelationLabel = (score) => {
    if (score >= 70) return { label: 'Strong', color: 'text-error-700 bg-error-50 border-error-200' }
    if (score >= 40) return { label: 'Moderate', color: 'text-warning-700 bg-warning-50 border-warning-200' }
    return { label: 'Weak', color: 'text-success-700 bg-success-50 border-success-200' }
  }
  
  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Analysis Reports</h1>
        <p className="text-neutral-600 mt-2">Comprehensive gluten-symptom correlation analysis</p>
      </div>
      
      {/* Generate New Report */}
      <div className="bg-white border border-primary-200 rounded-xl p-6 mb-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Generate New Report</h3>
            <p className="text-sm text-neutral-600 mb-4">
              Requires at least 10 meals and 10 symptoms for statistical analysis
            </p>
            <div className="flex items-center space-x-3">
              <label className="text-sm font-medium text-neutral-700">Analysis Period:</label>
              <select
                value={weeks}
                onChange={(e) => setWeeks(parseInt(e.target.value))}
                className="px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white text-slate-900"
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
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors font-medium shadow-sm"
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
          <div className="mt-4 p-3 bg-error-50 border border-error-200 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-error-700">{error}</p>
          </div>
        )}
      </div>
      
      {/* Current Correlation Analysis */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
            <p className="text-neutral-600">Calculating correlation...</p>
          </div>
        </div>
      )}
      
      {!loading && correlation && (
        <div className="bg-white rounded-xl border border-neutral-200 p-8 mb-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900 mb-6">Current Correlation Analysis</h2>
          
          {/* Main Score */}
          <div className="text-center py-8 bg-neutral-50 rounded-xl mb-6 border border-neutral-200">
            <p className="text-sm text-neutral-600 mb-2 uppercase tracking-wide font-medium">Gluten-Symptom Correlation</p>
            <div className="text-6xl font-semibold text-primary-600 mb-3">
              {correlation.correlation_score.toFixed(1)}%
            </div>
            <span className={`inline-block px-4 py-2 rounded-lg font-semibold border ${getCorrelationLabel(correlation.correlation_score).color}`}>
              {getCorrelationLabel(correlation.correlation_score).label} Correlation
            </span>
          </div>
          
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center p-4 bg-neutral-50 rounded-lg border border-neutral-200">
              <p className="text-sm text-neutral-600 mb-1 font-medium">Statistical Confidence</p>
              <p className="text-2xl font-semibold text-slate-900">{(correlation.confidence_level * 100).toFixed(1)}%</p>
            </div>
            
            <div className="text-center p-4 bg-neutral-50 rounded-lg border border-neutral-200">
              <p className="text-sm text-neutral-600 mb-1 font-medium">Statistical Significance</p>
              <div className="flex items-center justify-center mt-2">
                {correlation.significant ? (
                  <>
                    <CheckCircle className="w-6 h-6 text-success-600 mr-2" />
                    <span className="text-lg font-semibold text-success-600">Yes (p&lt;0.05)</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-6 h-6 text-neutral-400 mr-2" />
                    <span className="text-lg font-semibold text-neutral-600">Not Yet</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="text-center p-4 bg-neutral-50 rounded-lg border border-neutral-200">
              <p className="text-sm text-neutral-600 mb-1 font-medium">Time Lag</p>
              <p className="text-2xl font-semibold text-slate-900">
                {correlation.time_lag_hours ? `${correlation.time_lag_hours}h` : 'Same day'}
              </p>
            </div>
          </div>
          
          {/* Findings */}
          <div className="space-y-4">
            {/* Dose Response */}
            {correlation.dose_response !== null && (
              <div className={`p-4 rounded-lg border ${
                correlation.dose_response ? 'bg-warning-50 border-warning-200' : 'bg-neutral-50 border-neutral-200'
              }`}>
                <div className="flex items-start space-x-3">
                  <TrendingUp className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                    correlation.dose_response ? 'text-warning-600' : 'text-neutral-400'
                  }`} />
                  <div>
                    <p className="font-semibold text-slate-900">Dose-Response Relationship</p>
                    <p className="text-sm text-neutral-700 mt-1">
                      {correlation.dose_response 
                        ? 'Detected: Higher gluten intake correlates with worse symptoms'
                        : 'Not detected: No clear dose-response pattern yet'
                      }
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Time Lag Info */}
            {correlation.time_lag_hours > 0 && (
              <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Calendar className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-slate-900">Delayed Reaction Pattern</p>
                    <p className="text-sm text-neutral-700 mt-1">
                      Symptoms tend to appear approximately {correlation.time_lag_hours} hours after gluten exposure
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Interpretation */}
            <div className={`p-4 rounded-lg border ${
              correlation.correlation_score >= 60 
                ? 'bg-error-50 border-error-200' 
                : correlation.correlation_score >= 40 
                  ? 'bg-warning-50 border-warning-200'
                  : 'bg-success-50 border-success-200'
            }`}>
              <p className="font-semibold text-slate-900 mb-2">Clinical Interpretation</p>
              <p className="text-sm text-neutral-800 leading-relaxed">
                {correlation.correlation_score >= 60 && correlation.significant && (
                  <>
                    <strong>Strong evidence of gluten intolerance.</strong> Your symptoms show a statistically significant correlation with gluten intake. 
                    We recommend consulting with a healthcare provider about gluten elimination and further diagnostic testing.
                  </>
                )}
                {correlation.correlation_score >= 40 && correlation.correlation_score < 60 && (
                  <>
                    <strong>Moderate correlation detected.</strong> There appears to be a relationship between gluten and your symptoms. 
                    Continue tracking for 2-4 more weeks to gather more data for a definitive conclusion.
                  </>
                )}
                {correlation.correlation_score < 40 && (
                  <>
                    <strong>Low correlation.</strong> Gluten may not be the primary trigger for your symptoms. 
                    Consider tracking other potential triggers (dairy, sugar, stress, etc.) or continue tracking to gather more data.
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Previous Reports */}
      {reports.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200 p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900 mb-6">Previous Reports</h2>
          <div className="space-y-4">
            {reports.map((report) => (
              <div key={report.id} className="p-5 border border-neutral-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-sm font-medium text-neutral-600">
                        {format(new Date(report.start_date), 'MMM d')} - {format(new Date(report.end_date), 'MMM d, yyyy')}
                      </span>
                      <span className={`px-3 py-1 rounded-lg text-xs font-semibold border ${
                        report.gluten_intolerance_detected 
                          ? 'bg-error-50 text-error-700 border-error-200' 
                          : 'bg-success-50 text-success-700 border-success-200'
                      }`}>
                        {report.gluten_intolerance_detected ? 'Positive' : 'Negative'}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-600">
                      Correlation: <strong className="text-slate-900">{report.correlation_score?.toFixed(1)}%</strong> • 
                      Meals: {report.total_meals_logged} • 
                      Symptoms: {report.total_symptoms_logged}
                    </p>
                    {report.recommendations && (
                      <p className="text-sm text-neutral-700 mt-2 line-clamp-2">{report.recommendations}</p>
                    )}
                  </div>
                  <button
                    className="ml-4 p-2 text-neutral-400 hover:text-primary-600 transition-colors"
                    title="Download report"
                  >
                    <Download className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Empty State */}
      {!loading && reports.length === 0 && !correlation && (
        <div className="bg-white border border-neutral-200 rounded-xl p-12 text-center">
          <FileText className="w-16 h-16 text-neutral-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Reports Yet</h3>
          <p className="text-neutral-600 mb-6">
            You need at least 10 meals and 10 symptoms logged to generate your first report.<br/>
            Keep tracking your meals and symptoms for accurate analysis.
          </p>
          <div className="flex justify-center space-x-3">
            <Link 
              to="/upload-photo" 
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Upload Photo
            </Link>
            <Link 
              to="/timeline" 
              className="px-4 py-2 bg-white text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-medium"
            >
              View Timeline
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default Reports
