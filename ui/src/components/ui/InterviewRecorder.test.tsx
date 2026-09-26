import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { InterviewRecorder } from './InterviewRecorder'

vi.mock('../../api/sessions', () => ({
  uploadRecording: vi.fn(),
  deleteRecording: vi.fn(),
}))

describe('InterviewRecorder', () => {
  it('degrades gracefully and lets the interview proceed when MediaRecorder is undefined', () => {
    expect('MediaRecorder' in window).toBe(false)

    render(<InterviewRecorder sessionId="session-1" active={false} completed={false} />)

    expect(
      screen.getByText(/Recording is not supported in this browser/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/The interview will proceed normally without it/i),
    ).toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  it('shows the opt-in toggle, off by default, when recording is supported', () => {
    // Minimal MediaRecorder stub so the component reports support.
    class FakeMediaRecorder {
      state = 'inactive'
      ondataavailable: (() => void) | null = null
      onstop: (() => void) | null = null
      start() {}
      stop() {}
      static isTypeSupported() {
        return false
      }
    }
    vi.stubGlobal('MediaRecorder', FakeMediaRecorder)
    vi.stubGlobal('navigator', {
      ...navigator,
      mediaDevices: { getUserMedia: vi.fn() },
    })

    render(<InterviewRecorder sessionId="session-1" active={false} completed={false} />)

    const checkbox = screen.getByRole('checkbox', { name: /record this interview/i })
    expect(checkbox).not.toBeChecked()

    vi.unstubAllGlobals()
  })
})
