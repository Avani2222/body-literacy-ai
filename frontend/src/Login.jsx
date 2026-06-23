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
  page: {
    height: '98dvh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff0f5',
    padding: '16px',
    boxSizing: 'border-box',
  },

  card: {
    width: '100%',
    maxWidth: '400px',
    background: '#fff',
    borderRadius: '20px',
    padding: '24px',
    boxSizing: 'border-box',
    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
  },

  title: {
    textAlign: 'center',
    marginBottom: '8px',
  },

  smallMeta: {
    textAlign: 'center',
    color: '#666',
    marginBottom: '24px',
  },

  input: {
    width: '100%',
    padding: '12px',
    marginBottom: '12px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    boxSizing: 'border-box',
  },

  primaryBtn: {
    width: '100%',
    padding: '12px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    backgroundColor: '#e86b8f',
    color: '#fff',
    fontWeight: 600,
  },

  subtleLink: {
    marginLeft: '6px',
    color: '#e86b8f',
    textDecoration: 'none',
  },

  error: {
    marginBottom: '12px',
    color: '#d32f2f',
  },
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