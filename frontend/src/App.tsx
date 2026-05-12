import { Route, Routes } from 'react-router-dom'

function InputFormPage() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0] flex items-center justify-center">
      <div className="text-[#8891a8] text-lg">Input Form</div>
    </div>
  )
}

function TimelinePage() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0] flex items-center justify-center">
      <div className="text-[#8891a8] text-lg">Timeline</div>
    </div>
  )
}

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
      <Route path="/" element={<InputFormPage />} />
      <Route path="/timeline" element={<TimelinePage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/export" element={<ExportPage />} />
    </Routes>
  )
}

export default App
