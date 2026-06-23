import React, { useState, useMemo } from 'react';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
export default function DashboardFormExample() {
  const [cyclePhase, setCyclePhase] = useState('');
  const [moodCategory, setMoodCategory] = useState('');
  const [moodDetail, setMoodDetail] = useState('');
  const [energy, setEnergy] = useState('');
  const [sleep, setSleep] = useState('');
  // insight may be a string (raw) or an object (structured)
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);
  const [predictions, setPredictions] = useState(null);

  const token = localStorage.getItem('access_token');

  const MOOD_OPTIONS = useMemo(() => ({
    positive: ["Happy", "Energetic", "Motivated", "Confident", "Relaxed"],
    neutral:  ["Calm", "Okay", "Tired", "Numb", "Meh"],
    negative: ["Anxious", "Stressed", "Sad", "Irritated", "Overwhelmed"],
  }), []);

  const CYCLE_PHASES = ["menstrual", "follicular", "ovulatory", "luteal"];
  const ENERGY_LEVELS = ["low", "medium", "high"];

  // simple inline styles for a cleaner look
  const styles = {
  page: {
    minHeight: '98dvh',
    backgroundColor: '#fff0f5',
    padding: '16px',
    boxSizing: 'border-box',
    fontFamily: 'Inter, system-ui, Arial',
    color: '#3b0a29',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'flex-start',
  },

  container: {
    width: '100%',
    maxWidth: '900px',
  },

  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: '12px',
  },

  subtitle: {
    color: '#666',
    marginTop: '6px',
  },

  card: {
    background: '#fff',
    padding: '24px',
    borderRadius: '20px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
    marginTop: '12px',
    boxSizing: 'border-box',
  },

  formGroup: {
    marginBottom: '16px',
  },

  formLabel: {
    display: 'block',
    marginBottom: '6px',
    fontWeight: 600,
    color: '#3b0a29',
  },

  input: {
    width: '100%',
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    boxSizing: 'border-box',
    background: '#fff',
  },

  actionsRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '16px',
    flexWrap: 'wrap',
  },

  primaryBtn: {
    padding: '12px 16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    backgroundColor: '#e86b8f',
    color: '#fff',
    fontWeight: 600,
  },

  secondaryBtn: {
    padding: '12px 16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    backgroundColor: '#f8d7e3',
    color: '#3b0a29',
    fontWeight: 500,
  },

  predictCard: {
    background: '#fff',
    padding: '20px',
    borderRadius: '16px',
    marginTop: '12px',
    border: '1px solid #f3d6df',
    boxShadow: '0 4px 12px rgba(0,0,0,0.04)',
  },

  twoColumn: {
    display: 'flex',
    gap: '16px',
    marginTop: '16px',
    flexWrap: 'wrap',
  },

  predictColumn: {
    flex: '1 1 340px',
    minWidth: '300px',
  },

  insightColumn: {
    flex: '1 1 340px',
    minWidth: '300px',
  },

  predictionsPanel: {
    marginTop: '16px',
    display: 'grid',
    gap: '12px',
  },

  smallMeta: {
    color: '#666',
    fontSize: '14px',
  },
};

  function parseJwt(token) {
    if (!token) return null;
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64).split('').map(c =>
          '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
        ).join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('parseJwt error', e);
      return null;
    }
  }

  const claims = parseJwt(token);
  const user_id = claims?.sub ?? null;

  function buildPayload() {
    return {
      user_id,
      cycle_phase: cyclePhase,
      mood_category: moodCategory,
      mood_detail: moodDetail,
      energy,
      sleep: sleep === '' ? null : String(sleep),
      mood: moodDetail || moodCategory || null,
    };
  }

  async function handleSubmit(e) {
    if (e && typeof e.preventDefault === 'function') e.preventDefault();
    if (!token || !user_id) { setInsight('Not authenticated'); return; }
    setLoading(true);
    setInsight(null);
    try {
      const res = await fetch('http://localhost:8000/insight', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(buildPayload()),
      });
      if (!res.ok) {
        if (res.status === 401) {
          setInsight('Session expired — logging in again');
          localStorage.removeItem('access_token');
          setTimeout(() => { window.location.href = '/login'; }, 1100);
          return;
        }
        const text = await res.text();
        setInsight(`Server error: ${res.status} ${text}`);
        return;
      }
      const data = await res.json();
      const raw = data.insight ?? data?.insight_text ?? data?.insightString ?? null;
      // try to parse structured JSON insight if present
      if (raw) {
        if (typeof raw === 'object') {
          setInsight(raw);
        } else {
          try {
            const parsed = JSON.parse(raw);
            if (parsed && typeof parsed === 'object') {
              setInsight(parsed);
            } else {
              setInsight(String(raw));
            }
          } catch {
            setInsight(String(raw));
          }
        }
      } else {
        setInsight('No insight returned');
      }
    } catch (err) {
      setInsight(`Unexpected error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  // wrapper so "Get Insight" button in the Insight card can call the same handler
  function handleGetInsightClick() {
    // call handleSubmit with a dummy event that provides preventDefault()
    handleSubmit({ preventDefault: () => {} });
  }

  async function handlePredictFutureBehaviours() {
    if (!token || !user_id) { setInsight('Not authenticated'); return; }

    const payload = buildPayload();

    setLoading(true);
    setInsight(''); // clear insight while retraining/predicting

    // First, try to trigger an explicit training endpoint.
    // If the backend exposes POST /ml/train that calls train_multi.train_and_save,
    // this will retrain the model on the server. If /ml/train is missing, we
    // fall back to calling /ml/predict with a header to indicate retrain.
    let trainSucceeded = false;
    try {
      const trainRes = await fetch('http://localhost:8000/ml/train', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (trainRes.ok) {
        console.log('Training requested: /ml/train responded OK');
        trainSucceeded = true;
      } else {
        console.warn('Training request /ml/train returned non-OK:', trainRes.status);
      }
    } catch (err) {
      console.warn('Training request /ml/train failed (endpoint may not exist):', err);
    }

    // Now request prediction. If /ml/train didn't exist or didn't succeed,
    // include header X-Force-Retrain so servers that honor it will retrain first.
    try {
      const res = await fetch('http://localhost:8000/ml/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Force-Retrain': trainSucceeded ? '0' : '1',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        if (res.status === 401) {
          setInsight('Session expired — logging in again');
          localStorage.removeItem('access_token');
          setTimeout(() => { window.location.href = '/login'; }, 1100);
          return;
        }
        console.warn('ml predict failed', res.status, await res.text());
        setPredictions(null);
        return;
      }
      const json = await res.json();
      console.log('ml predict response:', JSON.stringify(json, null, 2));
      setPredictions(json.predictions || null);
    } catch (err) {
      console.warn('ml predict error', err);
      setPredictions(null);
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Body Literacy AI</h2>
        <p>Please log in to use the dashboard.</p>
        <a href="/login">Go to Login</a>
      </div>
    );
  }

  // reusable pill renderer
  function ProbabilityPills({ probabilities, prediction, highlightColor }) {
    if (!probabilities) return null;
    return (
      <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
        {Object.entries(probabilities).map(([label, pct]) => (
          <span key={label} style={{
            padding: '2px 10px',
            borderRadius: 12,
            background: label === prediction ? highlightColor : '#e9ecef',
            fontSize: 13,
            textTransform: 'capitalize',
          }}>
            {label}: {pct}
          </span>
        ))}
      </div>
    );
  }

  function capitalizeLabel(s) {
    if (!s && s !== 0) return 'N/A';
    try {
      const str = String(s);
      return str.charAt(0).toUpperCase() + str.slice(1);
    } catch {
      return String(s);
    }
  }

  function PredictionCard({ title, data, highlightColor }) {
    if (!data) return null;
    if (data.error) return (
      <div style={{ marginBottom: 14, color: '#a71d2a', fontSize: 14 }}>
        <strong>{title}:</strong> {data.error}
      </div>
    );
    // If warning exists but there is also a fallback prediction, show both.
    if (data.warning && data.fallback) {
      return (
        <div style={{ marginBottom: 14 }}>
          <div style={{ color: '#856404', fontSize: 14 }}>
            <strong>{title}:</strong> {data.warning}
          </div>
          <div style={{ marginTop: 8 }}>
            <strong>{title} (fallback)</strong>
            <div style={{ fontSize: 18, marginTop: 4, textTransform: 'capitalize' }}>
              {capitalizeLabel(data.prediction)}
              <span style={{ fontSize: 13, color: '#6b2750', marginLeft: 8 }}>
                ({data.confidence ?? 'N/A'} confident)
              </span>
            </div>
            {data.fallback_source && (
              <div style={{ marginTop: 6, fontSize: 13, color: '#6b2750' }}>
                Source: {data.fallback_source}
              </div>
            )}
          </div>
        </div>
      );
    }
    if (data.warning) return (
      <div style={{ marginBottom: 14, color: '#c2185b', fontSize: 14 }}>
        <strong>{title}:</strong> {data.warning}
      </div>
    );
    return (
      <div style={{ marginBottom: 14 }}>
        <strong>{title}</strong>
        <div style={{ fontSize: 18, marginTop: 4, textTransform: 'capitalize' }}>
          {capitalizeLabel(data.prediction)}
          <span style={{ fontSize: 13, color: '#6b2750', marginLeft: 8 }}>
            ({data.confidence ?? 'N/A'} confident)
           </span>
        </div>
        <ProbabilityPills
          probabilities={data.probabilities}
          prediction={data.prediction}
          highlightColor={highlightColor}
        />
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={{ margin: 0 }}>Body Literacy AI</h1>
        <div className="small-meta" style={styles.smallMeta}>User: {user_id ?? 'guest'}</div>
      </div>
      <p style={styles.subtitle}>Please select these fields below to get a personalized insight.</p>

      {loading && (
        <div style={{ margin: '12px 0', padding: 12, background: '#fff0f6', color: '#9c0a3a', borderRadius: 6 }}>
          <strong>Getting insight — please wait</strong>
          <div style={{ fontSize: 13, marginTop: 6 }}>We are analyzing your input and recent history.</div>
        </div>
      )}

      <div style={styles.predictCard}>
        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Cycle phase</label>
            <select style={styles.input} value={cyclePhase} onChange={e => setCyclePhase(e.target.value)} required>
              <option value="">-- choose --</option>
              {CYCLE_PHASES.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Mood category</label>
            <select style={styles.input} value={moodCategory} onChange={e => { setMoodCategory(e.target.value); setMoodDetail(''); }} required>
              <option value="">-- choose --</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Mood detail</label>
            <select style={styles.input} value={moodDetail} onChange={e => setMoodDetail(e.target.value)} required disabled={!moodCategory}>
              <option value="">-- choose --</option>
              {moodCategory && MOOD_OPTIONS[moodCategory].map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Energy</label>
            <select style={styles.input} value={energy} onChange={e => setEnergy(e.target.value)} required>
              <option value="">-- choose --</option>
              {ENERGY_LEVELS.map(lvl => <option key={lvl} value={lvl}>{lvl}</option>)}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.formLabel}>Sleep (hours 0–24)</label>
            <input
              style={styles.input}
              type="number" min="0" max="24" step="0.5"
              value={sleep} onChange={e => setSleep(e.target.value)} required
            />
          </div>

        </form>
      </div>

      {/* two-column layout: predict (fixed width) + insight (flex) */}
      <div style={{ marginTop: 12 }}>
        <div
          style={{
            ...styles.predictCard,
            marginTop: 12
          }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong>Insight</strong>
              <div style={styles.smallMeta}>Receive a personalized insight tailored to your history and supported by evidence from multiple research papers, clinical studies, and trusted scientific documents.</div>
            </div>
            <div>
              <button
                type="button"
                onClick={handleGetInsightClick}
                style={styles.primaryBtn}
                disabled={loading}
              >
                {loading ? 'Getting insight…' : 'Get Insight'}
              </button>
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            {insight && typeof insight === "object" ? (
              <div
                style={{
                  background: "#f8f9fa",
                  padding: 12,
                  borderRadius: 6
                }}
              >
                <div
                  style={{
                    lineHeight: 1.6
                  }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {insight.insight || ""}
                  </ReactMarkdown>
                </div>

                {insight.confidence && (
                  <div
                    style={{
                      marginTop: 16,
                      paddingTop: 12,
                      borderTop: "1px solid #ddd"
                    }}
                  >
                    <strong>Confidence:</strong> {insight.confidence}
                  </div>
                )}

                {insight.sources?.length > 0 && (
                  <div
                    style={{
                      marginTop: 16,
                      paddingTop: 12,
                      borderTop: "1px solid #ddd"
                    }}
                  >
                    <strong>Sources</strong>

                    <ul style={{ marginTop: 8 }}>
                      {insight.sources.map((source, idx) => (
                        <li key={idx}>
                          {source.source}
                          {source.page && ` (Page ${source.page})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : 
            insight?(
              <div
                style={{
                  background: "#f8f9fa",
                  padding: 12,
                  borderRadius: 6
                }}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {insight}
                </ReactMarkdown>
              </div>
            ): null}
          </div>
        </div>
      </div>
        <div style={styles.predictCard}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong>Predict future behaviours</strong>
              <div style={styles.smallMeta}>Predict your future mood and energy levels based on your personal history and past patterns.</div>
            </div>
            <div>
              <button
                type="button"
                onClick={handlePredictFutureBehaviours}
                style={styles.primaryBtn}
                disabled={loading}
              >
                {loading ? 'Working…' : 'Predict future behaviours'}
              </button>
            </div>
          </div>
        </div>

        

      {predictions && (
        <div style={styles.card}>
          <h3 style={{ marginBottom: 10 }}>Predictions</h3>
          <div style={styles.predictionsPanel}>
            <PredictionCard
              title="Energy tomorrow"
              data={predictions.energy}
              highlightColor="#ffd1e8"
            />
            <PredictionCard
              title="Mood tomorrow"
              data={predictions.mood}
              highlightColor="#ffb3d9"
            />
          </div>
        </div>
      )}
      </div>
    </div>
  );
}


