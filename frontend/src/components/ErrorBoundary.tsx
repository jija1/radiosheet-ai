import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message || 'Unexpected error' }
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    // Error already captured in state; could log to a service here
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0f1117] flex items-center justify-center px-4">
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-8 max-w-md w-full text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-[#ef444422] border border-[#ef444455] flex items-center justify-center mx-auto">
              <span className="text-[#ef4444] text-xl">!</span>
            </div>
            <h1 className="text-[#e8eaf0] text-lg font-semibold">Something went wrong</h1>
            <p className="text-[#8891a8] text-sm">
              An unexpected error occurred. Reload the page to continue.
            </p>
            {this.state.message && (
              <p className="text-[#4a5166] text-xs font-mono bg-[#0f1117] rounded px-3 py-2 text-left">
                {this.state.message}
              </p>
            )}
            <button
              onClick={this.handleReload}
              className="bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
            >
              Reload
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
