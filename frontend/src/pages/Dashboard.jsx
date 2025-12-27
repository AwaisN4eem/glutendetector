import React, { useState, useEffect } from 'react'
import { 
  Activity, 
  Utensils, 
  TrendingUp, 
  Calendar,
  AlertCircle,
  CheckCircle,
  Loader2,
  Clock,
  BarChart3,
  Camera
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement)

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    loadDashboard()
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
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-neutral-600">Loading dashboard data...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="bg-error-50 border border-error-200 rounded-xl p-6 flex items-start space-x-3">
        <AlertCircle className="w-6 h-6 text-error-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-error-900">Error Loading Dashboard</p>
          <p className="text-sm text-error-700 mt-1">{error}</p>
        </div>
      </div>
    )
  }
  
  const stats = [
    {
      name: 'Total Meals',
      value: dashboardData?.total_meals || 0,
      icon: Utensils,
      color: 'text-primary-600',
      bgColor: 'bg-primary-50',
    },
    {
      name: 'Symptoms Logged',
      value: dashboardData?.total_symptoms || 0,
      icon: Activity,
      color: 'text-error-600',
      bgColor: 'bg-error-50',
    },
    {
      name: 'Gluten Exposure Days',
      value: dashboardData?.gluten_exposure_days || 0,
      icon: AlertCircle,
      color: 'text-warning-600',
      bgColor: 'bg-warning-50',
    },
    {
      name: 'Symptom Days',
      value: dashboardData?.symptom_days || 0,
      icon: Calendar,
      color: 'text-neutral-600',
      bgColor: 'bg-neutral-50',
    },
  ]
  
  // Chart data for timeline
  const timelineData = dashboardData?.recent_timeline || []
  const chartData = {
    labels: timelineData.slice(0, 10).reverse().map((entry, idx) => `Day ${idx + 1}`),
    datasets: [
      {
        label: 'Gluten Risk',
        data: timelineData.slice(0, 10).reverse().map(e => e.entry_type === 'meal' ? e.gluten_risk : null),
        borderColor: '#FFA000',
        backgroundColor: 'rgba(255, 160, 0, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Symptom Severity',
        data: timelineData.slice(0, 10).reverse().map(e => e.entry_type === 'symptom' ? e.severity * 10 : null),
        borderColor: '#E53935',
        backgroundColor: 'rgba(229, 57, 53, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  }
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 16,
          font: {
            size: 12,
            family: 'Inter',
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(38, 50, 56, 0.95)',
        padding: 12,
        titleFont: {
          size: 13,
          weight: '600',
        },
        bodyFont: {
          size: 12,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
    },
  }
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-neutral-600 mt-2">Overview of your tracking data (last 14 days)</p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-neutral-600 mb-2">{stat.name}</p>
                <p className="text-3xl font-semibold text-slate-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Correlation Preview */}
      {dashboardData?.correlation_preview !== null && dashboardData?.correlation_preview !== undefined && (
        <div className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-1">Correlation Analysis</h3>
              <p className="text-sm text-neutral-600">Preliminary gluten-symptom correlation</p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-semibold text-primary-600">{dashboardData.correlation_preview.toFixed(1)}%</div>
              <p className="text-xs text-neutral-500 mt-1">Correlation Score</p>
            </div>
          </div>
          
          {dashboardData.correlation_preview >= 60 && (
            <div className="mt-4 p-4 bg-warning-50 border border-warning-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-warning-900">Strong Correlation Detected</p>
                  <p className="text-sm text-warning-700 mt-1">
                    Consider generating a full report for detailed statistical analysis.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Average Gluten Risk</h3>
          <div className="flex items-end space-x-3 mb-4">
            <span className="text-4xl font-semibold text-primary-600">{dashboardData?.avg_gluten_risk?.toFixed(1) || 0}</span>
            <span className="text-lg text-neutral-500 mb-1">/100</span>
          </div>
          <div className="w-full bg-neutral-100 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${dashboardData?.avg_gluten_risk || 0}%` }}
            ></div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Average Symptom Severity</h3>
          <div className="flex items-end space-x-3 mb-4">
            <span className="text-4xl font-semibold text-error-600">{dashboardData?.avg_symptom_severity?.toFixed(1) || 0}</span>
            <span className="text-lg text-neutral-500 mb-1">/10</span>
          </div>
          <div className="w-full bg-neutral-100 rounded-full h-2">
            <div 
              className="bg-error-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(dashboardData?.avg_symptom_severity || 0) * 10}%` }}
            ></div>
          </div>
        </div>
      </div>
      
      {/* Chart */}
      {timelineData.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Activity Timeline</h3>
              <p className="text-sm text-neutral-600 mt-1">Last 10 days of meals and symptoms</p>
            </div>
            <Link 
              to="/timeline" 
              className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center space-x-1"
            >
              <span>View Full Timeline</span>
              <Clock className="w-4 h-4" />
            </Link>
          </div>
          <div className="h-64">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>
      )}
      
      {/* Quick Actions */}
      {dashboardData?.total_meals === 0 && (
        <div className="bg-white rounded-xl border border-primary-200 p-8">
          <div className="text-center max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Welcome to GlutenGuard AI</h3>
            <p className="text-neutral-600 mb-6">
              Start tracking your meals and symptoms to detect gluten intolerance patterns through statistical analysis.
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <Link 
                to="/upload-photo" 
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium flex items-center space-x-2"
              >
                <Camera className="w-5 h-5" />
                <span>Upload Photo</span>
              </Link>
              <Link 
                to="/log-meal" 
                className="px-6 py-3 bg-white text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-medium flex items-center space-x-2"
              >
                <Utensils className="w-5 h-5" />
                <span>Log Meal</span>
              </Link>
              <Link 
                to="/log-symptom" 
                className="px-6 py-3 bg-white text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-medium flex items-center space-x-2"
              >
                <Activity className="w-5 h-5" />
                <span>Log Symptom</span>
              </Link>
            </div>
          </div>
        </div>
      )}
      
      {/* Recent Activity */}
      {timelineData.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Activity</h3>
            <Link 
              to="/timeline" 
              className="text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {timelineData.slice(0, 5).map((entry, idx) => (
              <div key={idx} className="flex items-start space-x-3 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
                <div className={`p-2 rounded-lg ${entry.entry_type === 'meal' ? 'bg-primary-50 text-primary-600' : 'bg-error-50 text-error-600'}`}>
                  {entry.entry_type === 'meal' ? <Utensils className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{entry.description}</p>
                  <p className="text-xs text-neutral-500 mt-1">{new Date(entry.timestamp).toLocaleString()}</p>
                </div>
                {entry.gluten_risk && (
                  <span className="px-3 py-1 bg-warning-50 text-warning-700 text-xs font-semibold rounded-lg whitespace-nowrap">
                    {entry.gluten_risk.toFixed(0)}/100
                  </span>
                )}
                {entry.severity && (
                  <span className="px-3 py-1 bg-error-50 text-error-700 text-xs font-semibold rounded-lg whitespace-nowrap">
                    {entry.severity.toFixed(1)}/10
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
