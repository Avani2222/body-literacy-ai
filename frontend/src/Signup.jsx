import React, { useState, useEffect } from 'react';

export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [fieldErrors, setFieldErrors] = useState({}); // { name: '', email: '', password: '' }

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
    // ensure box-sizing so width includes padding (prevents overflow)
    input: { width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #ffd6ec', marginBottom: 12, boxSizing: 'border-box', background: '#fff' },
    primaryBtn: { width: '100%', background: '#e91e63', color: '#fff', border: 'none', padding: '10px 14px', borderRadius: 8, cursor: 'pointer', boxSizing: 'border-box' },
    smallMeta: { fontSize: 13, color: '#6b2750', marginTop: 8 },
    error: { color: '#9c0a3a', marginBottom: 8 },
    subtleLink: { color: '#e91e63', textDecoration: 'none', marginLeft: 6 }
  };

  // basic client-side validation
  function validateForm() {
    const errs = {};
    if (!name.trim()) errs.name = 'Name is required.';
    if (!email.trim()) errs.email = 'Email is required.';
    else {
      // simple email sanity check
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!re.test(email.trim())) errs.email = 'Enter a valid email.';
    }
    if (!password) errs.password = 'Password is required.';
    return errs;
  }

  async function handleSignup(e) {
    e.preventDefault();
    setMsg('');
    // client-side validation first
    const errs = validateForm();
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      setMsg(Object.values(errs).join(' '));
      return;
    }
    setFieldErrors({});
    setLoading(true);

    const payload = { name: name.trim(), email: email.trim(), password };
    const primaryUrl = 'http://localhost:8000/auth/signup';

    // helper to parse and show validation-like details
    const showValidation = async (res) => {
      try {
        const body = await res.json();
        if (body.detail) {
          if (Array.isArray(body.detail)) {
            return body.detail.map(d => (d.msg || JSON.stringify(d))).join('; ');
          } else {
            return String(body.detail);
          }
        } else if (body.errors) {
          return JSON.stringify(body.errors);
        } else if (typeof body === 'string') {
          return body;
        } else {
          return JSON.stringify(body);
        }
      } catch {
        const txt = await res.text();
        return txt || `Status ${res.status}`;
      }
    };

    try {
      // try primary endpoint first
      let res = await fetch(primaryUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      // if primary is 404, attempt common alternative endpoints
      if (res.status === 404) {
        console.warn('Primary signup endpoint 404, attempting fallbacks...');
        const fallbacks = ['/auth/register', '/users', '/users/signup'];
        let succeeded = false;
        for (const p of fallbacks) {
          const url = `http://localhost:8000${p}`;
          try {
            const r = await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });
            console.log('Fallback attempt', url, r.status);
            if (r.ok) { res = r; succeeded = true; break; }
            // if validation error, surface it immediately
            if (r.status === 422) {
              const detail = await showValidation(r);
              setMsg(detail || `Validation failed on ${p}`);
              return;
            }
          } catch (err) {
            console.warn('Fallback fetch failed', url, err);
          }
        }
        if (!succeeded && res.status === 404) {
          setMsg('Signup service not found (404). Confirm backend routes or try later.');
          console.error('Signup 404 on primary and fallbacks.');
          return;
        }
      }

      // handle validation / other errors
      if (!res.ok) {
        if (res.status === 422) {
          const detail = await showValidation(res);
          setMsg(detail || 'Validation error — check input.');
          console.error('Signup validation error:', detail);
          return;
        }
        // generic handling: attempt to get body text or json for debugging
        try {
          const bodyText = await res.text();
          console.error('Signup failed', res.status, bodyText);
          setMsg(`Signup failed: ${res.status} ${bodyText}`);
        } catch (err) {
          console.error('Signup failed and response body unreadable', err);
          setMsg(`Signup failed: ${res.status}`);
        }
        return;
      }

      // success path
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        window.location.href = '/Login';
      } else {
        setMsg('Account created. Please sign in.');
      }
    } catch (err) {
      console.warn('Network or unexpected error during signup', err);
      setMsg('Network error — please check backend is running and CORS is configured.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h2 style={styles.title}>Create an account</h2>
        <p style={styles.smallMeta}>Start your Body Literacy journey — it only takes a minute.</p>
        {msg && <div style={styles.error}>{msg}</div>}
        <form onSubmit={handleSignup}>
          <input
            style={styles.input}
            type="text"
            placeholder="Full name"
            value={name}
            onChange={e => { setName(e.target.value); setFieldErrors(prev => ({ ...prev, name: '' })); }}
          />
          {fieldErrors.name && <div style={{ color: '#9c0a3a', marginBottom: 8 }}>{fieldErrors.name}</div>}

          <input
            style={styles.input}
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => { setEmail(e.target.value); setFieldErrors(prev => ({ ...prev, email: '' })); }}
          />
          {fieldErrors.email && <div style={{ color: '#9c0a3a', marginBottom: 8 }}>{fieldErrors.email}</div>}

          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => { setPassword(e.target.value); setFieldErrors(prev => ({ ...prev, password: '' })); }}
          />
          {fieldErrors.password && <div style={{ color: '#9c0a3a', marginBottom: 8 }}>{fieldErrors.password}</div>}

          <button style={styles.primaryBtn} type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create account'}</button>
        </form>
        <div style={{ marginTop: 12 }}>
          <span style={styles.smallMeta}>Already have an account?</span>
          <a href="/login" style={styles.subtleLink}>Sign in</a>
        </div>
      </div>
    </div>
  );
}
