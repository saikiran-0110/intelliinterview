import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  speakText,
  stopSpeaking,
} from './speech'

class FakeUtterance {
  text: string
  rate = 1
  pitch = 1
  lang = ''
  onend: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(text: string) {
    this.text = text
  }
}

describe('speech helpers', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('reports missing browser support', () => {
    expect(isSpeechSynthesisSupported()).toBe(false)
    expect(isSpeechRecognitionSupported()).toBe(false)
  })

  it('speaks trimmed text and returns a cancel function', () => {
    const speak = vi.fn()
    const cancel = vi.fn()
    vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance)
    vi.stubGlobal('speechSynthesis', { speak, cancel })

    const onEnd = vi.fn()
    const stop = speakText('  Hello candidate  ', { rate: 1.1, onEnd })
    expect(speak).toHaveBeenCalledTimes(1)
    const utterance = speak.mock.calls[0][0] as FakeUtterance
    expect(utterance.text).toBe('Hello candidate')
    expect(utterance.rate).toBe(1.1)
    utterance.onend?.()
    expect(onEnd).toHaveBeenCalled()
    stop()
    expect(cancel).toHaveBeenCalled()
  })

  it('applies the requested language to the utterance, defaulting to en-GB', () => {
    const speak = vi.fn()
    vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance)
    vi.stubGlobal('speechSynthesis', { speak, cancel: vi.fn() })

    speakText('Bonjour', { lang: 'fr-FR' })
    expect((speak.mock.calls[0][0] as FakeUtterance).lang).toBe('fr-FR')

    speakText('Hello', {})
    expect((speak.mock.calls[1][0] as FakeUtterance).lang).toBe('en-GB')
  })

  it('calls onError when synthesis is unavailable', () => {
    const onError = vi.fn()
    speakText('hello', { onError })
    expect(onError).toHaveBeenCalledWith('Text-to-speech is not supported in this browser.')
  })

  it('does not speak blank text', () => {
    const speak = vi.fn()
    vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance)
    vi.stubGlobal('speechSynthesis', { speak, cancel: vi.fn() })
    speakText('   ')
    expect(speak).not.toHaveBeenCalled()
  })

  it('creates an unsupported recognition controller when APIs are missing', () => {
    const onError = vi.fn()
    const controller = createSpeechRecognition({ onResult: vi.fn(), onError })
    expect(controller.supported).toBe(false)
    controller.start()
    expect(onError).toHaveBeenCalled()
    controller.stop()
  })

  it('starts recognition and reports final transcripts', () => {
    const instances: FakeRecognition[] = []
    class FakeRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onresult: ((event: { resultIndex: number; results: Array<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null =
        null
      onerror: ((event: { error: string }) => void) | null = null
      onend: (() => void) | null = null
      start = vi.fn()
      stop = vi.fn()
      constructor() {
        instances.push(this)
      }
    }
    vi.stubGlobal('SpeechRecognition', FakeRecognition)
    const onResult = vi.fn()
    const controller = createSpeechRecognition({ onResult })
    expect(controller.supported).toBe(true)
    controller.start()
    expect(instances[0].start).toHaveBeenCalled()
    instances[0].onresult?.({
      resultIndex: 0,
      results: [{ 0: { transcript: '  Hello team ' }, isFinal: true }],
    })
    expect(onResult).toHaveBeenCalledWith('Hello team', true)
  })

  it('applies the requested language to speech recognition', () => {
    const instances: FakeRecognition[] = []
    class FakeRecognition {
      continuous = false
      interimResults = false
      lang = ''
      onresult: (() => void) | null = null
      onerror: (() => void) | null = null
      onend: (() => void) | null = null
      start = vi.fn()
      stop = vi.fn()
      constructor() {
        instances.push(this)
      }
    }
    vi.stubGlobal('SpeechRecognition', FakeRecognition)
    const controller = createSpeechRecognition({ onResult: vi.fn(), lang: 'es-ES' })
    expect(controller.supported).toBe(true)
    expect(instances[0].lang).toBe('es-ES')
  })
})

describe('stopSpeaking', () => {
  it('is a no-op without synthesis support', () => {
    expect(() => stopSpeaking()).not.toThrow()
  })
})
