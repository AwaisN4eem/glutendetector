import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Camera, 
  Utensils, 
  Activity, 
  Clock, 
  FileText,
  Menu,
  X
} from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Track', href: '/upload-photo', icon: Camera, group: 'Input' },
    { name: 'Log Meal', href: '/log-meal', icon: Utensils, group: 'Input' },
    { name: 'Log Symptom', href: '/log-symptom', icon: Activity, group: 'Input' },
    { name: 'Timeline', href: '/timeline', icon: Clock, group: 'Analysis' },
    { name: 'Reports', href: '/reports', icon: FileText, group: 'Analysis' },
  ]
  
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-semibold text-lg">G</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-900">GlutenGuard AI</h1>
                <p className="text-xs text-neutral-500">Gluten Intolerance Detection System</p>
              </div>
            </Link>
            
            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center space-x-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                      ${isActive 
                        ? 'bg-primary-50 text-primary-700' 
                        : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                      }
                    `}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>
            
            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-lg"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
        
        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="lg:hidden border-t border-neutral-200 bg-white">
            <div className="px-4 py-3 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors
                      ${isActive 
                        ? 'bg-primary-50 text-primary-700' 
                        : 'text-neutral-600 hover:bg-neutral-100'
                      }
                    `}
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </nav>
        )}
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-neutral-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-2 md:space-y-0">
            <p className="text-sm text-neutral-500">
              GlutenGuard AI - Clinical Data Analysis Platform
            </p>
            <p className="text-xs text-neutral-400">
              For Educational Use • Not Medical Advice • Consult Healthcare Provider
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout

