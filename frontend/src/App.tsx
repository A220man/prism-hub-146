import { useState, useEffect } from 'react'

function App() {
  const [health, setHealth] = useState<{status: string, service: string} | null>(null)
  const [version, setVersion] = useState<{version: string, name: string} | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('/health')
        if (response.ok) {
          setHealth(await response.json())
        } else {
          setError(`Health check failed: ${response.status}`)
        }
      } catch (e) {
        setError(`Health check error: ${e}`)
      }
    }

    const fetchVersion = async () => {
      try {
        const response = await fetch('/api/version')
        if (response.ok) {
          setVersion(await response.json())
        }
      } catch (e) {
        console.error('Version fetch failed:', e)
      }
    }

    fetchHealth()
    fetchVersion()
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Prism Hub</h1>
      <p>AI/ML Developer Tools Platform</p>
      
      <section style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h2>Backend Connection</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {health && (
          <div style={{ color: 'green' }}>
            <p><strong>Status:</strong> {health.status}</p>
            <p><strong>Service:</strong> {health.service}</p>
          </div>
        )}
        {!health && !error && <p>Checking...</p>}
      </section>

      <section style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h2>Version Info</h2>
        {version && (
          <div>
            <p><strong>Name:</strong> {version.name}</p>
            <p><strong>Version:</strong> {version.version}</p>
          </div>
        )}
        {!version && <p>Loading...</p>}
      </section>
    </div>
  )
}

export default App
