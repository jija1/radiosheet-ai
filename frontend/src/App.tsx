import { Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import LoginPage from './features/auth/LoginPage'
import RegisterPage from './features/auth/RegisterPage'
import InputFormPage from './features/input-form'
import TimelinePage from './features/timeline'

function HistoryPage() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0] flex items-center justify-center">
      <div className="text-[#8891a8] text-lg">History</div>
    </div>
  )
}

function ExportPage() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0] flex items-center justify-center">
      <div className="text-[#8891a8] text-lg">Export</div>
    </div>
  )
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute><InputFormPage /></ProtectedRoute>
      } />
      <Route path="/timeline" element={
        <ProtectedRoute><TimelinePage /></ProtectedRoute>
      } />
      <Route path="/history" element={
        <ProtectedRoute><HistoryPage /></ProtectedRoute>
      } />
      <Route path="/export" element={
        <ProtectedRoute><ExportPage /></ProtectedRoute>
      } />
    </Routes>
  )
}

export default App
