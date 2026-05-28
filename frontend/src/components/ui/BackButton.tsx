import { useNavigate } from 'react-router-dom'

export function BackButton() {
  const navigate = useNavigate()
  return (
    <button
      onClick={() => navigate(-1)}
      className="flex items-center gap-1.5 text-[#8891a8] hover:text-[#e8eaf0] text-sm transition-colors mb-6"
    >
      ← Back
    </button>
  )
}
