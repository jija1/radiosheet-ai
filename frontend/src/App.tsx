import { Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { ToastContainer } from './components/ui/Toast'
import LoginPage from './features/auth/LoginPage'
import RegisterPage from './features/auth/RegisterPage'
import DashboardPage from './features/dashboard'
import ExportPage from './features/export'
import InputFormPage from './features/input-form'
import PrivacyPage from './features/privacy'
import ProfilePage from './features/profile'
import SettingsPage from './features/settings'
import StatisticsPage from './features/statistics'
import TimelinePage from './features/timeline'
import ValidatePage from './features/validate'

function HistoryPage() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0] flex items-center justify-center">
      <div className="text-[#8891a8] text-lg">History</div>
    </div>
  )
}

function App() {
  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/" element={
          <ProtectedRoute><InputFormPage /></ProtectedRoute>
        } />
        <Route path="/timeline" element={
          <ProtectedRoute><TimelinePage /></ProtectedRoute>
        } />
        <Route path="/history" element={
          <ProtectedRoute><HistoryPage /></ProtectedRoute>
        } />
        <Route path="/validate" element={
          <ProtectedRoute><ValidatePage /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><ProfilePage /></ProtectedRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute><SettingsPage /></ProtectedRoute>
        } />
        <Route path="/statistics" element={
          <ProtectedRoute><StatisticsPage /></ProtectedRoute>
        } />
        <Route path="/privacy" element={
          <ProtectedRoute><PrivacyPage /></ProtectedRoute>
        } />
        <Route path="/export" element={
          <ProtectedRoute><ExportPage /></ProtectedRoute>
        } />
      </Routes>
      <ToastContainer />
    </>
  )
}

export default App
