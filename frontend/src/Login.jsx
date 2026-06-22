import React, { useState, useEffect } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!document.getElementById('bl-fonts')) {
      const l = document.createElement('link');
      l.id = 'bl-fonts';
      l.rel = 'stylesheet';
      l.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Poppins:wght@300;400;600&display=swap';
      document.head.appendChild(l);
    }
    const prev = document.body.style.fontFamily;
    document.body.style.fontFamily = "Poppins, Inter, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif";
    document.body.style.webkitFontSmoothing = 'antialiased';
    return () => { document.body.style.fontFamily = prev; };
  }, []);

  const styles = {
    page: { maxWidth: 520, margin: '48px auto', fontFamily: "Poppins, Inter, system-ui, -apple-system, 'Segoe UI', Roboto, Arial", color: '#3b0a29', padding: 12 },
    card: { background: '#fff5f8', padding: 20, borderRadius: 10, boxShadow: '0 8px 30px rgba(59,10,41,0.06)', overflow: 'hidden' },
    title: { margin: '0 0 8px 0', color: '#501038' },
    input: { width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #ffd6ec', marginBottom: 12, boxSizing: 'border-box', background: '#fff' },
    primaryBtn: { width: '100%', background: '#e91e63', color: '#fff', border: 'none', padding: '10px 14px', borderRadius: 8, cursor: 'pointer', boxSizing: 'border-box' },
    smallMeta: { fontSize: 13, color: '#6b2750', marginTop: 8 },
    error: { color: '#9c0a3a', marginBottom: 8 },
    subtleLink: { color: '#e91e63', textDecoration: 'none', marginLeft: 6 }
  };

  async function handleLogin(e) {
    e.preventDefault();
    setMsg('');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password })
      });
      if (!res.ok) {
        console.log("not ok", res.status);
        if (res.status === 401) {
          setMsg('Invalid credentials — please try again.');
          return;
        }
        if (res.status === 404) {
          setMsg('Authentication service unavailable (404). Please try again later.');
          return;
        }
        if (res.status === 422) {
          // Validation error from backend (pydantic). Try to extract messages.
          try {
            const body = await res.json();
            // common patterns: { detail: [...] } or { detail: "..." } or { errors: {...} }
            if (body.detail) {
              if (Array.isArray(body.detail)) {
                setMsg(body.detail.map(d => (d.msg || JSON.stringify(d))).join('; '));
              } else {
                setMsg(String(body.detail));
              }
            } else if (body.errors) {
              setMsg(JSON.stringify(body.errors));
            } else {
              setMsg('Validation error — please check your input.');
            }
          } catch (parseErr) {
            const txt = await res.text();
            setMsg(`Validation failed: ${txt}`);
          }
          return;
        }
        const txt = await res.text();
        setMsg(`Login failed: ${res.status} ${txt}`);
        return;
      }
      const data = await res.json();
      console.log('Login response data:', data);
      if (data.access_token) {
        console.log('Login succeeded, token received:', data.access_token);
        localStorage.setItem('access_token', data.access_token);
        window.location.href = '/Dashboard';
      } else {
        setMsg('Login succeeded but no token returned.');
      }
    } catch (err) {
      setMsg('Network error — please try again.');
      console.warn('login error', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h2 style={styles.title}>Welcome back</h2>
        <p style={styles.smallMeta}>Log in to access your Body Literacy dashboard.</p>
        {msg && <div style={styles.error}>{msg}</div>}
        <form onSubmit={handleLogin}>
          <input style={styles.input} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input style={styles.input} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
          <button style={styles.primaryBtn} type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <div style={{ marginTop: 12 }}>
          <span style={styles.smallMeta}>New here?</span>
          <a href="/signup" style={styles.subtleLink}>Create an account</a>
        </div>
      </div>
    </div>
  );
}