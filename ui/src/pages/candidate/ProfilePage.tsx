import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function ProfilePage() {
  return (
    <div>
      <PageHeader
        title="My Profile"
        description="Manage your account, upload your CV, and update contact details for interview scheduling."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Account details"
          items={[
            { label: 'Full name', hint: 'Profile field' },
            { label: 'Email address', hint: 'Login identifier' },
            { label: 'Password change', hint: 'Security settings' },
          ]}
        />
        <PlaceholderPanel
          title="CV management"
          items={[
            { label: 'Upload CV', hint: 'PDF/DOCX ,  Apache Tika parsing' },
            { label: 'Current CV preview', hint: 'Extracted text summary' },
            { label: 'Registration', hint: 'Create candidate account' },
          ]}
        />
      </div>
    </div>
  )
}
