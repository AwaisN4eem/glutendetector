import React, { useState, useEffect } from 'react'
import { Loader2, AlertCircle, Clock, List, Heart, AlertTriangle, TrendingUp, BarChart3, Info, Link as LinkIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { format } from 'date-fns'
import ExplainButton from '../components/ExplainButton'

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState(null)
  const [insights, setInsights] = useState([])
  const [insightsLoading, setInsightsLoading] = useState(false)
  
  useEffect(() => {
    loadDashboard()
    loadInsights()
  }, [])
  
  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.getDashboard(14)
      setDashboardData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }
  
  const loadInsights = async () => {
    try {
      setInsightsLoading(true)
      const response = await api.getSmartInsights(7)
      setInsights(response.data.insights || [])
    } catch (err) {
      console.error('Failed to load insights:', err)
      // Don't show error, just don't display insights
    } finally {
      setInsightsLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mx-auto mb-4 stroke-2" />
          <p className="text-gray-400">Loading dashboard data...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="bg-[#1a1f2e] border border-red-500/30 rounded-xl p-6 flex items-start space-x-3 shadow-xl">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 stroke-2" />
        <div>
          <p className="font-medium text-white">Error Loading Dashboard</p>
          <p className="text-gray-400 mt-1">{error}</p>
        </div>
      </div>
    )
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
  
  const stats = [
    {
      label: 'Total Meals',
      value: dashboardData?.total_meals || 0,
      icon: List,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20',
      borderColor: 'border-emerald-500/30',
      hoverGradient: 'from-emerald-500/20 to-emerald-500/30',
      accentGradient: 'from-emerald-500 via-emerald-400 to-emerald-300',
    },
    {
      label: 'Total Symptoms',
      value: dashboardData?.total_symptoms || 0,
      icon: Heart,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/20',
      borderColor: 'border-rose-500/30',
      hoverGradient: 'from-rose-500/20 to-rose-500/30',
      accentGradient: 'from-rose-500 via-rose-400 to-rose-300',
    },
    {
      label: 'Avg Gluten Risk',
      value: `${dashboardData?.avg_gluten_risk?.toFixed(0) || 0}/100`,
      icon: AlertTriangle,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/20',
      borderColor: 'border-amber-500/30',
      hoverGradient: 'from-amber-500/20 to-amber-500/30',
      accentGradient: 'from-amber-500 via-amber-400 to-amber-300',
    },
    {
      label: 'Correlation',
      value: dashboardData?.correlation_preview !== null && dashboardData?.correlation_preview !== undefined
        ? `${dashboardData.correlation_preview.toFixed(0)}%`
        : 'N/A',
      icon: LinkIcon,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20',
      borderColor: 'border-emerald-500/30',
      hoverGradient: 'from-emerald-500/20 to-emerald-500/30',
      accentGradient: 'from-emerald-500 via-emerald-400 to-emerald-300',
    },
  ]
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center space-x-3 mb-2 group/header">
            <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500/30 rounded-xl flex items-center justify-center shadow-md group-hover/header:scale-110 group-hover/header:rotate-6 transition-all duration-500">
              <Heart className="w-6 h-6 text-emerald-400 stroke-2 group-hover/header:scale-110 transition-transform duration-300" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white group-hover/header:text-emerald-400 transition-all duration-500">Health Overview</h1>
              <p className="text-sm text-gray-400 mt-1">
                {dashboardData ? format(new Date(), 'MMMM d, yyyy') : 'N/A'}
              </p>
            </div>
          </div>
        </div>
        {dashboardData?.correlation_preview !== null && dashboardData?.correlation_preview !== undefined && (
          <div className="flex items-center space-x-3 px-5 py-3 bg-[#1a1f2e] border border-emerald-500/30 rounded-xl shadow-md hover:shadow-lg transition-all duration-300 group/corr">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-md group-hover/corr:scale-110 group-hover/corr:rotate-6 transition-all duration-500">
              <BarChart3 className="w-5 h-5 text-white stroke-2" />
            </div>
            <div>
              <p className="text-xs text-emerald-400 font-medium">Correlation Score</p>
              <p className="text-lg font-bold text-emerald-400">
                {dashboardData.correlation_preview.toFixed(1)}%
              </p>
            </div>
            <ExplainButton
              type="correlation"
              correlationScore={dashboardData.correlation_preview}
              pValue={null}
              totalMeals={dashboardData.total_meals || 0}
              totalSymptoms={dashboardData.total_symptoms || 0}
              className="ml-2"
            />
          </div>
        )}
      </div>
      
      {/* Overview Statistics - Dark Theme Cards with Green Accents */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => (
          <div 
            key={idx}
            className="group relative bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-500 hover:-translate-y-2 overflow-hidden"
          >
            {/* Animated background gradient on hover */}
            <div className={`absolute inset-0 bg-gradient-to-br ${stat.hoverGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl`}></div>
            
            {/* Content wrapper with z-index */}
            <div className="relative z-10">
              {/* Icon with animated background */}
              <div className={`mb-5 w-14 h-14 rounded-xl flex items-center justify-center ${stat.bgColor} border ${stat.borderColor} shadow-sm transition-all duration-500 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-lg`}>
                <stat.icon className={`w-7 h-7 ${stat.color} stroke-2 transition-all duration-300 group-hover:scale-110`} />
              </div>
              
              {/* Value and Label */}
              <div className="transition-transform duration-300 group-hover:translate-x-1">
                <p className="text-3xl font-bold text-white mb-1 transition-colors duration-300 group-hover:text-emerald-400">{stat.value}</p>
                <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">{stat.label}</p>
              </div>
            </div>
            
            {/* Decorative gradient bar with animation */}
            <div className={`absolute bottom-0 left-0 right-0 h-1.5 bg-gradient-to-r ${stat.accentGradient} rounded-b-2xl transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left`}></div>
          </div>
        ))}
      </div>
      
      {/* Smart Insights Panel - Dark Theme with Green Accents */}
      {insights.length > 0 && (
        <div className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl p-8 shadow-xl relative overflow-hidden group">
          {/* Animated decorative background pattern */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-1000"></div>
          
          <div className="relative z-10">
            <div className="flex items-center space-x-4 mb-6">
              <div className="w-16 h-16 bg-emerald-500/20 border border-emerald-500/30 rounded-xl flex items-center justify-center shadow-md group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                <Info className="w-8 h-8 text-emerald-400 stroke-2" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-1">Smart Insights</h3>
                <p className="text-sm text-gray-400 font-medium">Personalized insights based on your data</p>
              </div>
            </div>
            {insightsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin stroke-2" />
              </div>
            ) : (
              <div className="space-y-4">
                {insights.map((insight, idx) => {
                  const colors = [
                    { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', number: 'bg-gradient-to-br from-emerald-500 to-emerald-600', text: 'text-emerald-300' },
                    { bg: 'bg-emerald-600/10', border: 'border-emerald-600/30', number: 'bg-gradient-to-br from-emerald-600 to-emerald-700', text: 'text-emerald-200' },
                    { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', number: 'bg-gradient-to-br from-emerald-500 to-emerald-600', text: 'text-emerald-300' },
                  ]
                  const colorScheme = colors[idx % colors.length]
                  return (
                    <div 
                      key={idx}
                      className={`${colorScheme.bg} backdrop-blur-sm border ${colorScheme.border} rounded-xl p-5 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 group/item`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`w-8 h-8 ${colorScheme.number} rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md group-hover/item:scale-110 group-hover/item:rotate-12 transition-all duration-300`}>
                          <span className="text-white font-bold text-sm">{idx + 1}</span>
                        </div>
                        <p className={`text-[15px] leading-relaxed ${colorScheme.text} font-medium flex-1`}>{insight}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Correlation Analysis - Dark Theme Card */}
      {dashboardData?.correlation_preview !== null && dashboardData?.correlation_preview !== undefined && (
        <div className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl p-8 shadow-xl">
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-xl font-bold text-white">Correlation Analysis</h3>
                <ExplainButton
                  type="correlation"
                  correlationScore={dashboardData.correlation_preview}
                  pValue={null}
                  totalMeals={dashboardData.total_meals || 0}
                  totalSymptoms={dashboardData.total_symptoms || 0}
                  className="text-xs"
                />
              </div>
              <p className="text-sm text-gray-400 font-medium">Gluten-symptom relationship strength</p>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold text-emerald-400">
                {dashboardData.correlation_preview.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-400 font-medium mt-1">Score</p>
            </div>
          </div>
          <div className="relative w-full h-4 bg-[#0a0e1a] rounded-full overflow-hidden shadow-inner">
            <div 
              className="h-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-300 rounded-full transition-all duration-700 shadow-lg"
              style={{ width: `${dashboardData.correlation_preview}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
            </div>
          </div>
          {dashboardData.correlation_preview >= 60 && (
            <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl shadow-sm">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5 stroke-2" />
                <p className="text-sm text-amber-300 font-medium">
                  Strong correlation detected. Consider generating a full report for detailed analysis.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Recent Activity - Dark Theme Timeline */}
      {dashboardData?.recent_timeline && dashboardData.recent_timeline.length > 0 && (
        <div className="bg-[#1a1f2e] border border-emerald-500/20 rounded-2xl p-8 shadow-xl relative overflow-hidden group/section">
          {/* Animated background gradient */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl opacity-0 group-hover/section:opacity-100 transition-opacity duration-1000"></div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Recent Activity</h2>
                <p className="text-sm text-gray-400">Your latest meals and symptoms</p>
              </div>
              <Link 
                to="/timeline" 
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 font-medium flex items-center space-x-2 transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105 transform"
              >
                <span>View All</span>
                <Clock className="w-4 h-4 stroke-2" />
              </Link>
            </div>
            <div className="space-y-4">
              {dashboardData.recent_timeline.slice(0, 5).map((entry, idx) => (
                <div 
                  key={idx} 
                  className="bg-[#0a0e1a] border border-emerald-500/20 rounded-xl p-5 hover:shadow-lg hover:border-emerald-500/40 transition-all duration-300 hover:-translate-x-1 group/entry relative overflow-hidden"
                >
                  {/* Hover gradient effect */}
                  <div className="absolute inset-0 bg-emerald-500/10 opacity-0 group-hover/entry:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                  <div className="relative z-10 flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shadow-sm transition-all duration-300 group-hover/entry:scale-110 group-hover/entry:rotate-6 ${
                          entry.entry_type === 'meal' 
                            ? 'bg-emerald-500/20 border border-emerald-500/30' 
                            : 'bg-rose-500/20 border border-rose-500/30'
                        }`}>
                          {entry.entry_type === 'meal' ? (
                            <List className="w-5 h-5 text-emerald-400 stroke-2" />
                          ) : (
                            <Heart className="w-5 h-5 text-rose-400 stroke-2" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white group-hover/entry:text-emerald-400 transition-colors duration-300">{entry.description}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {format(new Date(entry.timestamp), 'MMM d, yyyy h:mm a')}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      {entry.gluten_risk !== null && (
                        <span className={`px-4 py-2 rounded-lg text-xs font-bold border shadow-sm transition-all duration-300 group-hover/entry:scale-105 ${getGlutenRiskBadge(entry.gluten_risk).bg} ${getGlutenRiskBadge(entry.gluten_risk).text} ${getGlutenRiskBadge(entry.gluten_risk).border}`}>
                          {entry.gluten_risk.toFixed(0)}/100
                        </span>
                      )}
                      {entry.severity !== null && (
                        <span className="px-4 py-2 rounded-lg text-xs font-bold border bg-[#1a1f2e] text-gray-300 border-gray-600 shadow-sm transition-all duration-300 group-hover/entry:scale-105">
                          {entry.severity.toFixed(1)}/10
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Generate Report Button */}
      {dashboardData?.total_meals >= 10 && dashboardData?.total_symptoms >= 10 && (
        <div className="flex justify-center">
          <Link
            to="/reports"
            className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 font-semibold shadow-xl hover:shadow-2xl flex items-center space-x-3 transform hover:-translate-y-1 hover:scale-105 group/btn"
          >
            <BarChart3 className="w-5 h-5 stroke-2 group-hover/btn:rotate-12 transition-transform duration-300" />
            <span>Generate Full Report</span>
          </Link>
        </div>
      )}
      
      {/* Empty State */}
      {(!dashboardData || dashboardData.total_meals === 0) && (
        <div className="bg-[#1a1f2e] border border-emerald-500/30 rounded-2xl p-16 shadow-xl relative overflow-hidden">
          {/* Animated background */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl opacity-50"></div>
          
          <div className="relative z-10 max-w-md mx-auto text-center">
            <div className="w-24 h-24 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg animate-bounce-slow">
              <List className="w-12 h-12 text-emerald-400 stroke-2" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">No meals logged yet</h3>
            <p className="text-base text-gray-400 mb-8 leading-relaxed">
              Start tracking your meals and symptoms to detect gluten intolerance patterns through statistical analysis.
            </p>
            <div className="flex justify-center items-center space-x-4">
              <Link 
                to="/upload-photo" 
                className="px-8 py-3.5 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:scale-105 transform"
              >
                Upload Photo
              </Link>
              <Link 
                to="/log-meal" 
                className="px-8 py-3.5 bg-[#0a0e1a] text-emerald-400 border-2 border-emerald-500/30 rounded-xl hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all duration-300 font-semibold shadow-md hover:scale-105 transform"
              >
                Log Meal
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
