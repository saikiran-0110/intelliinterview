/** Browser Web Speech API helpers for live AI interviews. */

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window
}

export function isSpeechRecognitionSupported(): boolean {
  if (typeof window === 'undefined') return false
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}

export function stopSpeaking(): void {
  if (!isSpeechSynthesisSupported()) return
  window.speechSynthesis.cancel()
}

/**
 * Speak text aloud. Returns a cancel function.
 * Playback is asynchronous and does not block the interview UI.
 */
export function speakText(
  text: string,
  options?: {
    rate?: number
    pitch?: number
    lang?: string
    onEnd?: () => void
    onError?: (message: string) => void
  },
): () => void {
  if (!isSpeechSynthesisSupported()) {
    options?.onError?.('Text-to-speech is not supported in this browser.')
    return () => undefined
  }

  const cleaned = text.trim()
  if (!cleaned) {
    return () => undefined
  }

  stopSpeaking()

  const utterance = new SpeechSynthesisUtterance(cleaned)
  utterance.rate = options?.rate ?? 1
  utterance.pitch = options?.pitch ?? 1
  utterance.lang = options?.lang ?? 'en-GB'
  utterance.onend = () => options?.onEnd?.()
  utterance.onerror = () => options?.onError?.('Text-to-speech playback failed.')

  window.speechSynthesis.speak(utterance)
  return () => {
    window.speechSynthesis.cancel()
  }
}

export type SpeechRecognitionHandlers = {
  onResult: (transcript: string, isFinal: boolean) => void
  onError?: (message: string) => void
  onEnd?: () => void
  continuous?: boolean
  interimResults?: boolean
  lang?: string
}

export type SpeechRecognitionController = {
  supported: boolean
  start: () => void
  stop: () => void
}

/**
 * Create a speech-to-text controller. Candidates can review/edit the transcript before submit.
 */
export function createSpeechRecognition(handlers: SpeechRecognitionHandlers): SpeechRecognitionController {
  const Recognition = typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : undefined

  if (!Recognition) {
    return {
      supported: false,
      start: () => handlers.onError?.('Speech-to-text is not supported in this browser.'),
      stop: () => undefined,
    }
  }

  const recognition = new Recognition()
  recognition.continuous = handlers.continuous ?? true
  recognition.interimResults = handlers.interimResults ?? true
  recognition.lang = handlers.lang ?? 'en-US'

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let interim = ''
    let finalText = ''
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i]
      const chunk = result[0]?.transcript ?? ''
      if (result.isFinal) {
        finalText += chunk
      } else {
        interim += chunk
      }
    }
    if (finalText) {
      handlers.onResult(finalText.trim(), true)
    } else if (interim) {
      handlers.onResult(interim.trim(), false)
    }
  }

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    if (event.error === 'aborted' || event.error === 'no-speech') {
      handlers.onEnd?.()
      return
    }
    handlers.onError?.(event.error || 'Speech recognition failed.')
    handlers.onEnd?.()
  }

  recognition.onend = () => {
    handlers.onEnd?.()
  }

  return {
    supported: true,
    start: () => {
      try {
        recognition.start()
      } catch {
        handlers.onError?.('Could not start speech recognition. Check microphone permission.')
      }
    },
    stop: () => {
      try {
        recognition.stop()
      } catch {
        // already stopped
      }
    },
  }
}
