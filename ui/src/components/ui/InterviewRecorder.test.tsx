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

    expect(screen.getByText(/requires recording/i)).toBeInTheDocument()
    expect(screen.getByText(/the interview will still proceed/i)).toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  it('has no opt-out control when recording is supported - it is compulsory', () => {
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

    expect(screen.getByText('This interview is recorded.')).toBeInTheDocument()
    expect(screen.getByText(/cannot be turned off/i)).toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()

    vi.unstubAllGlobals()
  })

  it('starts capture automatically once the interview becomes active, without any toggle', async () => {
    const getUserMedia = vi.fn().mockResolvedValue({
      getTracks: () => [],
    })
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
    vi.stubGlobal('navigator', { ...navigator, mediaDevices: { getUserMedia } })

    const { rerender } = render(
      <InterviewRecorder sessionId="session-1" active={false} completed={false} />,
    )
    expect(getUserMedia).not.toHaveBeenCalled()

    rerender(<InterviewRecorder sessionId="session-1" active={true} completed={false} />)
    await vi.waitFor(() => expect(getUserMedia).toHaveBeenCalledWith({ video: true, audio: true }))

    vi.unstubAllGlobals()
  })
})
