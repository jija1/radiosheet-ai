function App() {
  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <nav className="bg-[#13151f] border-b border-[#1e2133] px-10 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
            <span className="text-[#3b82f6] font-bold text-sm">R</span>
          </div>
          <span className="text-[#e8eaf0] font-medium">
            Radio<span className="text-[#3b82f6]">Sheet</span> AI
          </span>
        </div>
        <div className="flex gap-7 items-center">
          <span className="text-[#8891a8] text-sm cursor-pointer hover:text-[#e8eaf0]">Features</span>
          <span className="text-[#8891a8] text-sm cursor-pointer hover:text-[#e8eaf0]">About</span>
          <button className="bg-[#2563eb] text-white px-4 py-2 rounded-lg text-sm">
            Get started
          </button>
        </div>
      </nav>
      <main className="flex flex-col items-center justify-center px-10 py-20 text-center">
        <div className="inline-block bg-[#1a2340] border border-[#2563eb44] text-[#60a5fa] text-xs px-3 py-1 rounded-full mb-6 uppercase tracking-widest">
          Final Year Project · GIMPA BSc IT
        </div>
        <h1 className="text-5xl font-medium text-[#f0f2f8] mb-4 leading-tight">
          Intelligent run-sheets<br />
          for <span className="text-[#3b82f6]">radio producers</span>
        </h1>
        <p className="text-[#8891a8] text-base max-w-lg mb-10 leading-relaxed">
          Generate conflict-free broadcast schedules in seconds. AI detects overlaps,
          enforces advert limits, and recommends optimisations.
        </p>
        <div className="flex gap-3">
          <button className="bg-[#2563eb] text-white px-6 py-3 rounded-lg text-sm flex items-center gap-2">
            Generate a run-sheet
          </button>
          <button className="bg-transparent text-[#8891a8] border border-[#1e2133] px-5 py-3 rounded-lg text-sm">
            View demo
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
