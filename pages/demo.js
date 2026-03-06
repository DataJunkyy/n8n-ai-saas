import { getSession } from 'next-auth/react'

export default function Demo({ user }) {
  return (
    <main style={{maxWidth:880,margin:'40px auto',padding:'0 16px',fontFamily:"system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial"}}>
      <h1>Sandbox Demo</h1>
      <p>Welcome, {user?.name || user?.email || 'demo user'} — this demo is protected by application auth.</p>
      <p>This is a protected sandbox demo placeholder. To enable a real sandbox, configure the provider in the project settings.</p>
      <p>
        Demo API endpoints (authenticated):
      </p>
      <ul>
        <li><a href="/api/demo/formulas">/api/demo/formulas</a> — sample formulas (static)</li>
      </ul>
      <p style={{marginTop:24}}>Next steps: connect a GitHub OAuth app or other provider and set `NEXTAUTH_SECRET` in your environment.</p>
    </main>
  )
}

export async function getServerSideProps(context) {
  const session = await getSession(context)
  if (!session) {
    return {
      redirect: {
        destination: '/api/auth/signin',
        permanent: false,
      },
    }
  }
  return {
    props: { user: session.user },
  }
}
