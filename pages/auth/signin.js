import { getProviders, signIn } from 'next-auth/react'

export default function SignIn({ providers }) {
  return (
    <main style={{maxWidth:720,margin:'40px auto',padding:'0 16px',fontFamily:"system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial"}}>
      <h1>Sign in to RxServicesSolutions</h1>
      <p>Use your GitHub account to sign in to the demo environment.</p>
      <div style={{display:'grid',gap:12,marginTop:20}}>
        {Object.values(providers || {}).map((provider) => (
          <div key={provider.name}>
            <button onClick={() => signIn(provider.id)} style={{padding:'10px 14px',borderRadius:6}}>
              Sign in with {provider.name}
            </button>
          </div>
        ))}
      </div>
    </main>
  )
}

export async function getServerSideProps(context) {
  const providers = await getProviders()
  return {
    props: { providers: providers ?? {} },
  }
}
