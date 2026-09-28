import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ProfilePage } from './ProfilePage'

const storedUser = {
  user_id: 'candidate-1',
  email: 'candidate@example.com',
  full_name: 'Candidate One',
  role: 'CANDIDATE' as const,
  has_profile_photo: false,
}

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual<typeof import('../../api/client')>('../../api/client')
  return {
    ...actual,
    getStoredUser: vi.fn(() => storedUser),
    setAuth: vi.fn(),
  }
})

vi.mock('../../api/optional', () => ({
  listMyCvs: vi.fn(),
  updateProfile: vi.fn(),
  uploadMyCv: vi.fn(),
  deleteMyCv: vi.fn(),
  uploadMyPhoto: vi.fn(),
  deleteMyPhoto: vi.fn(),
  getUserPhotoBlob: vi.fn(),
}))

import { listMyCvs, uploadMyPhoto, getUserPhotoBlob } from '../../api/optional'

const mockedListMyCvs = vi.mocked(listMyCvs)
const mockedUploadMyPhoto = vi.mocked(uploadMyPhoto)
const mockedGetUserPhotoBlob = vi.mocked(getUserPhotoBlob)

describe('ProfilePage profile picture', () => {
  beforeEach(() => {
    mockedListMyCvs.mockReset()
    mockedUploadMyPhoto.mockReset()
    mockedGetUserPhotoBlob.mockReset()
    mockedListMyCvs.mockResolvedValue([])
    mockedGetUserPhotoBlob.mockRejectedValue(new Error('no photo'))
    if (!URL.createObjectURL) {
      URL.createObjectURL = vi.fn(() => 'blob:mock')
      URL.revokeObjectURL = vi.fn()
    }
  })

  it('uploads a profile picture and shows an updated status', async () => {
    const user = userEvent.setup()
    mockedUploadMyPhoto.mockResolvedValue({
      ...storedUser,
      token: 'token',
      has_profile_photo: true,
    } as never)

    render(<ProfilePage />)

    await screen.findByText('Profile picture')
    const fileInput = document.querySelector('input[type="file"][accept="image/*"]') as HTMLInputElement
    expect(fileInput).toBeTruthy()
    const file = new File(['fake-image'], 'me.png', { type: 'image/png' })
    await user.upload(fileInput, file)

    const uploadButton = screen.getByRole('button', { name: 'Upload photo' })
    await user.click(uploadButton)

    expect(mockedUploadMyPhoto).toHaveBeenCalledWith(file)
    expect(await screen.findByText('Profile picture updated.')).toBeInTheDocument()
  })
})
