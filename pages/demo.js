export default function Demo() {
  return (
    <main style={{maxWidth:880,margin:'40px auto',padding:'0 16px',fontFamily:"system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial"}}>
      <h1>Sandbox Demo</h1>
      <p>This is a protected sandbox demo placeholder. To enable a real sandbox, integrate Auth (Auth0, Clerk, or NextAuth) and connect a demo tenant.</p>
      <p>
        For now you can test the demo API endpoints below:
      </p>
      <ul>
        <li><a href="/api/auth">/api/auth</a> — auth placeholder response</li>
        <li><a href="/api/demo/formulas">/api/demo/formulas</a> — sample formulas (static)</li>
      </ul>
      <p style={{marginTop:24}}>Next steps: integrate Auth and replace these demo endpoints with a sandbox orchestration service.</p>
    </main>
  )
}
