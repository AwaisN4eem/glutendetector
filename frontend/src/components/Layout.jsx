import React, { useState, createContext, useContext } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Camera, 
  List, 
  Heart, 
  Clock, 
  FileText,
  Menu,
  X,
  LogOut,
  Info,
  Settings,
  Power,
  MessageCircle
} from 'lucide-react'
import Logo from '../images/Logo.png'
import AICoach from './AICoach'

// Context for AI Coach control
export const AICoachContext = createContext(null)

const Layout = ({ children }) => {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [aiCoachOpen, setAiCoachOpen] = useState(false)
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Upload Photo', href: '/upload-photo', icon: Camera },
    { name: 'Log Meal', href: '/log-meal', icon: List },
    { name: 'Log Symptom', href: '/log-symptom', icon: Heart },
    { name: 'Timeline', href: '/timeline', icon: Clock },
    { name: 'Reports', href: '/reports', icon: FileText },
  ]
  
  return (
    <div className="min-h-screen bg-[#0a0e1a] relative">
      {/* Network Pattern Background */}
      <div className="network-pattern"></div>
      
      <div className="flex h-screen overflow-hidden relative z-10">
        {/* Top Bar / Header with Logo */}
        <header className="fixed top-0 left-0 right-0 h-28 bg-[#1a1f2e]/95 backdrop-blur-xl border-b border-emerald-500/30 z-50 flex items-center justify-between px-8 shadow-2xl">
          {/* Logo - Professional and Prominent - Perfectly Aligned with Text */}
          <Link to="/" className="flex items-center space-x-5 hover:opacity-90 transition-opacity group flex-shrink-0">
            <div className="w-20 h-20 flex items-center justify-center relative flex-shrink-0">
              <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="absolute inset-0 border-2 border-emerald-500/40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <img
                src={Logo}
                alt="GlutenGuard AI"
                className="w-20 h-20 object-contain drop-shadow-[0_14px_36px_rgba(16,185,129,0.5)] transition-all duration-300 group-hover:scale-105 group-hover:drop-shadow-[0_18px_45px_rgba(16,185,129,0.65)] relative z-10"
              />
            </div>
            <div className="flex flex-col justify-center leading-none">
              <h1 className="text-3xl lg:text-4xl font-extrabold text-white transition-colors group-hover:text-emerald-50 tracking-tight leading-none">
                GlutenGuard <span className="text-emerald-400">AI</span>
              </h1>
              <p className="text-xs lg:text-sm text-gray-400 font-medium mt-1.5 leading-tight">Intelligent Gluten Detection Platform</p>
            </div>
          </Link>
          
          {/* Top Right Icons */}
          <div className="flex items-center space-x-4">
            <button className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-all duration-200">
              <Info className="w-5 h-5" />
            </button>
            <button className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-all duration-200">
              <Settings className="w-5 h-5" />
            </button>
            <button className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200">
              <Power className="w-5 h-5" />
            </button>
          </div>
        </header>
        
        {/* Sidebar Navigation */}
        <aside className={`
          fixed lg:static top-28 left-0 bottom-0 z-30
          w-20 lg:w-64
          bg-[#1a1f2e]/95 backdrop-blur-lg
          border-r border-emerald-500/20
          transform transition-transform duration-300 ease-in-out
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex flex-col
          overflow-hidden
        `}>
          
          {/* Navigation Items - Properly Aligned with Clear Spacing from Header */}
          <nav className="flex-1 px-2 lg:px-4 pt-4 pb-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`
                    group flex items-center justify-center lg:justify-start
                    lg:space-x-4 space-x-0
                    px-3 lg:px-4 py-3 lg:py-3 rounded-xl
                    transition-all duration-300
                    relative overflow-hidden
                    min-h-[44px] lg:min-h-[48px]
                    ${isActive 
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-lg' 
                      : 'text-gray-400 hover:bg-emerald-500/10 hover:text-emerald-400'
                    }
                  `}
                >
                  {/* Background animation on hover */}
                  {!isActive && (
                    <div className="absolute inset-0 bg-emerald-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                  )}
                  
                  {/* Icon with proper z-index - Centered on mobile, left-aligned on desktop */}
                  <div className="relative z-10 flex-shrink-0 flex items-center justify-center">
                    <item.icon className={`w-6 h-6 lg:w-5 lg:h-5 stroke-2 transition-all duration-300 ${
                      isActive 
                        ? 'text-white scale-110' 
                        : 'text-gray-400 group-hover:text-emerald-400 group-hover:scale-110 group-hover:rotate-6'
                    }`} />
                  </div>
                  
                  {/* Text with proper z-index - Hidden on mobile, shown on desktop */}
                  <span className={`hidden lg:block font-medium text-sm relative z-10 transition-colors duration-300 ml-2 ${
                    isActive ? 'text-white' : 'text-gray-400 group-hover:text-emerald-400'
                  }`}>{item.name}</span>
                  
                  {/* Active indicator with smooth animation */}
                  {isActive && (
                    <div className="hidden lg:block absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-emerald-300 rounded-r-full shadow-lg animate-pulse"></div>
                  )}
                  
                  {/* Hover indicator */}
                  {!isActive && (
                    <div className="hidden lg:block absolute left-0 top-1/2 -translate-y-1/2 w-1 h-0 bg-emerald-500 rounded-r-full group-hover:h-8 transition-all duration-300 opacity-0 group-hover:opacity-100"></div>
                  )}
                </Link>
              )
            })}
          </nav>
          
          {/* AI Coach Button (Bottom) */}
          <div className="px-3 lg:px-4 pb-6 mt-auto">
            <button 
              onClick={() => setAiCoachOpen(true)}
              className={`group flex items-center ${aiCoachOpen ? 'justify-center lg:justify-start' : 'justify-center'} w-full h-12 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-600 transition-all duration-300 shadow-lg hover:scale-105`}
            >
              <div className="w-6 h-6 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <MessageCircle className="w-4 h-4" />
              </div>
              <span className="hidden lg:block font-medium text-sm ml-3">AI Coach</span>
            </button>
          </div>
        </aside>
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden mt-28">
          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto px-6 py-8">
              {children}
            </div>
          </main>
        </div>
      </div>
      
      {/* AI Coach Chat */}
      <AICoachContext.Provider value={{ isOpen: aiCoachOpen, setIsOpen: setAiCoachOpen }}>
        <AICoach />
      </AICoachContext.Provider>
      
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="lg:hidden fixed top-7 left-7 z-50 p-2 bg-[#1a1f2e] border border-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/10 transition-all duration-200"
        aria-label="Toggle menu"
      >
        {mobileMenuOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <Menu className="w-6 h-6" />
        )}
      </button>
      
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/70 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        ></div>
      )}
    </div>
  )
}

export default Layout

