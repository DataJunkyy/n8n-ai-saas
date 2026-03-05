export default function Home() {
  return (
    <main className="container">
      <header className="hero">
        <h1>RxServicesSolutions</h1>
        <p className="subtitle">AI-powered formulation and project tools for cosmetics and CPG teams.</p>
        <div className="cta-row">
          <a className="btn primary" href="/demo">Try Sandbox — 14d Free</a>
          <a className="btn" href="#contact">Request a Demo</a>
        </div>
      </header>

      <section className="features">
        <h2>Core Services</h2>
        <ul>
          <li><strong>Cosmetic Formulator</strong> — Create, version, and export lab-ready formulas.</li>
          <li><strong>Project Assistant</strong> — Tasks, milestones, and contextual summaries.</li>
          <li><strong>Integrations</strong> — API, CSV import/export, and partner connectors.</li>
        </ul>
      </section>

      <footer id="contact" className="footer">
        <p>Get started — or schedule a demo.</p>
      </footer>

      <style jsx>{`
        .container { max-width: 880px; margin: 40px auto; padding: 0 16px; font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
        .hero { text-align: center; padding: 48px 0; }
        h1 { font-size: 36px; margin: 0 0 8px; }
        .subtitle { color: #555; margin-bottom: 20px; }
        .cta-row { display:flex; gap:12px; justify-content:center; }
        .btn { padding: 10px 16px; border-radius:6px; text-decoration:none; color:#111; background:#eee; }
        .btn.primary { background:#0ea5a4; color: white; }
        .features { margin-top:36px; }
        .features ul { list-style: none; padding:0; }
        .features li { background: #fafafa; padding:12px; margin-bottom:8px; border-radius:6px; }
        .footer { text-align:center; margin:48px 0; color:#666; }
      `}</style>

      {/* GA4 placeholder; set NEXT_PUBLIC_GA_ID in env for live tracking */}
      <script dangerouslySetInnerHTML={{__html: `
        (function(){
          const id = process.env.NEXT_PUBLIC_GA_ID || '';
          if(!id) return;
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          const s = document.createElement('script');
          s.async = true;
          s.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
          document.head.appendChild(s);
          gtag('js', new Date());
          gtag('config', id);
        })();
      `}} />
    </main>
  )
}
