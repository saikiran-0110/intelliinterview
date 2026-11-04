import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { checkProctoringFrame, uploadRecording } from '../../api/sessions'
import { InterviewRecorder } from './InterviewRecorder'

vi.mock('../../api/sessions', () => ({
  uploadRecording: vi.fn(),
  checkProctoringFrame: vi.fn(),
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

  describe('proctoring frame checks', () => {
    beforeEach(() => {
      vi.useFakeTimers()
      // jsdom has no real canvas/video rendering pipeline: stub just enough of it that
      // captureAndCheckFrame's readiness guard passes and toBlob delivers a frame.
      vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
        { drawImage: vi.fn() } as unknown as CanvasRenderingContext2D,
      )
      vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation(function (
        this: HTMLCanvasElement,
        callback: BlobCallback,
      ) {
        callback(new Blob(['frame']))
      })
      vi.spyOn(HTMLMediaElement.prototype, 'readyState', 'get').mockReturnValue(4)
      vi.spyOn(HTMLVideoElement.prototype, 'videoWidth', 'get').mockReturnValue(320)
      vi.spyOn(HTMLVideoElement.prototype, 'videoHeight', 'get').mockReturnValue(240)
    })

    afterEach(() => {
      vi.useRealTimers()
      vi.restoreAllMocks()
      vi.unstubAllGlobals()
    })

    function stubMediaForCapture() {
      const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [] })
      class FakeMediaRecorder {
        state = 'inactive'
        mimeType = 'video/webm'
        ondataavailable: (() => void) | null = null
        onstop: (() => void) | null = null
        start() {}
        stop() {
          this.state = 'inactive'
          this.onstop?.()
        }
        static isTypeSupported() {
          return false
        }
      }
      vi.stubGlobal('MediaRecorder', FakeMediaRecorder)
      vi.stubGlobal('navigator', { ...navigator, mediaDevices: { getUserMedia } })
    }

    it('checks a proctoring frame on an interval and reports the result upward', async () => {
      stubMediaForCapture()
      vi.mocked(checkProctoringFrame).mockResolvedValue({
        violation: true,
        kind: 'PROHIBITED_OBJECT',
        detail: 'A phone is visible.',
        warning_count: 1,
        warning_limit: 3,
        disqualified: false,
        session_status: 'IN_PROGRESS',
      })
      const onProctoringEvent = vi.fn()

      const { rerender } = render(
        <InterviewRecorder sessionId="session-1" active={false} completed={false} />,
      )
      rerender(
        <InterviewRecorder
          sessionId="session-1"
          active={true}
          completed={false}
          onProctoringEvent={onProctoringEvent}
        />,
      )
      await vi.waitFor(() => expect(screen.getByText('Recording')).toBeInTheDocument())

      await vi.advanceTimersByTimeAsync(10_000)

      expect(checkProctoringFrame).toHaveBeenCalledWith('session-1', expect.any(Blob))
      await vi.waitFor(() => expect(onProctoringEvent).toHaveBeenCalledWith(
        expect.objectContaining({ violation: true, warning_count: 1 }),
      ))
    })

    it('stops checking frames once the interview is completed', async () => {
      stubMediaForCapture()
      vi.mocked(checkProctoringFrame).mockResolvedValue({
        violation: false,
        kind: null,
        detail: '',
        warning_count: 0,
        warning_limit: 3,
        disqualified: false,
        session_status: 'IN_PROGRESS',
      })
      vi.mocked(uploadRecording).mockResolvedValue(undefined as never)

      const { rerender } = render(
        <InterviewRecorder sessionId="session-1" active={true} completed={false} />,
      )
      await vi.waitFor(() => expect(screen.getByText('Recording')).toBeInTheDocument())

      rerender(<InterviewRecorder sessionId="session-1" active={true} completed={true} />)

      vi.mocked(checkProctoringFrame).mockClear()
      await vi.advanceTimersByTimeAsync(30_000)

      expect(checkProctoringFrame).not.toHaveBeenCalled()
    })
  })
})
