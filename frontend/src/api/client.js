import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Default user ID for MVP (no auth)
const USER_ID = 1

export const api = {
  // Meals
  getMeals: (params = {}) => 
    apiClient.get('/api/meals', { params: { user_id: USER_ID, ...params } }),
  
  createMeal: (data) => 
    apiClient.post('/api/meals', data, { params: { user_id: USER_ID } }),
  
  updateMeal: (mealId, data) =>
    apiClient.put(`/api/meals/${mealId}`, data),
  
  // Symptoms
  getSymptoms: (params = {}) => 
    apiClient.get('/api/symptoms', { params: { user_id: USER_ID, ...params } }),
  
  createSymptom: (data) => 
    apiClient.post('/api/symptoms', data, { params: { user_id: USER_ID } }),
  
  // Photos
  uploadPhoto: (file, createMeal = true) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post('/api/photos/upload', formData, {
      params: { user_id: USER_ID, create_meal: createMeal },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  
  getPhotos: (params = {}) => 
    apiClient.get('/api/photos', { params: { user_id: USER_ID, ...params } }),
  
  // Analysis
  getDashboard: (days = 14) => 
    apiClient.get('/api/analysis/dashboard', { params: { user_id: USER_ID, days } }),
  
  getCorrelation: (startDate, endDate) => 
    apiClient.get('/api/analysis/correlation', { 
      params: { user_id: USER_ID, start_date: startDate, end_date: endDate } 
    }),
  
  getTimeline: (days = 7) => 
    apiClient.get('/api/analysis/timeline', { params: { user_id: USER_ID, days } }),
  
  generateReport: (weeks = 6) => 
    apiClient.post('/api/analysis/generate-report', null, { 
      params: { user_id: USER_ID, weeks } 
    }),
  
  getReports: () => 
    apiClient.get('/api/analysis/reports', { params: { user_id: USER_ID } }),
}

export default apiClient

