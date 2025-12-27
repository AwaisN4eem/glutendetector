import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import LogMeal from './pages/LogMeal'
import LogSymptom from './pages/LogSymptom'
import UploadPhoto from './pages/UploadPhoto'
import Reports from './pages/Reports'
import Timeline from './pages/Timeline'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log-meal" element={<LogMeal />} />
          <Route path="/log-symptom" element={<LogSymptom />} />
          <Route path="/upload-photo" element={<UploadPhoto />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

