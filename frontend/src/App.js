import { useState } from "react";

// ─── Componente KYC ───────────────────────────────────────────────────────────
function KYCModule() {
  const [file, setFile] = useState(null);
  const [threshold, setThreshold] = useState(0.82);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleMatch() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(
        `http://localhost:8000/match?threshold=${threshold}`,
        { method: "POST", body: form }
      );
      setResult(await res.json());
    } catch {
      setError("Erro ao conectar na API. Verifique se o backend está rodando.");
    }
    setLoading(false);
  }

  return (
    <div>
      <div style={s.card}>
        <h2 style={s.cardTitle}>Upload de Dataset KYC</h2>
        <p style={s.cardDesc}>CSV com colunas: <code>id, name, country, document</code></p>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} />
        {file && <p style={s.fileName}>📄 {file.name}</p>}
        <div style={{ marginTop: 16, marginBottom: 16 }}>
          <label style={s.label}>
            Threshold: <strong>{(threshold * 100).toFixed(0)}%</strong>
            <span style={{ color: "#888", marginLeft: 8, fontSize: 12 }}>
              {threshold >= 0.9 ? "🔴 Restrito" : threshold >= 0.8 ? "🟡 Balanceado" : "🟢 Permissivo"}
            </span>
          </label>
          <input type="range" min="0.5" max="1.0" step="0.01"
            value={threshold} onChange={e => setThreshold(parseFloat(e.target.value))}
            style={{ width: "100%", marginTop: 6 }} />
        </div>
        <button onClick={handleMatch} disabled={!file || loading}
          style={!file || loading ? s.btnDisabled : s.btn}>
          {loading ? "Processando..." : "Analisar Duplicatas"}
        </button>
      </div>

      {error && <div style={s.errorBox}>⚠️ {error}</div>}

      {result && (
        <>
          <div style={s.metricsRow}>
            {[
              { label: "Registros", value: result.summary.total_records.toLocaleString(), color: "#1a1a2e" },
              { label: "Duplicatas", value: result.summary.matches_found.toLocaleString(), color: "#e67e22" },
              ...(result.metrics ? [
                { label: "Precision", value: (result.metrics.precision * 100).toFixed(1) + "%", color: "#27ae60" },
                { label: "Recall", value: (result.metrics.recall * 100).toFixed(1) + "%", color: "#2980b9" },
                { label: "F1 Score", value: (result.metrics.f1_score * 100).toFixed(1) + "%", color: "#8e44ad" },
              ] : [])
            ].map((m, i) => (
              <div key={i} style={s.metricCard}>
                <div style={{ ...s.metricNum, color: m.color }}>{m.value}</div>
                <div style={s.metricLabel}>{m.label}</div>
              </div>
            ))}
          </div>

          <div style={s.card}>
            <h2 style={s.cardTitle}>
              Matches Encontrados
              <span style={s.badge}>{result.matches.length}</span>
            </h2>
            <div style={{ overflowX: "auto" }}>
              <table style={s.table}>
                <thead>
                  <tr style={{ background: "#f8f9fa" }}>
                    {["Nome A", "Nome B", "País", "Score"].map(h => (
                      <th key={h} style={s.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.matches.slice(0, 50).map((m, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                      <td style={s.td}>{m.name_a}</td>
                      <td style={s.td}>{m.name_b}</td>
                      <td style={s.td}>{m.country}</td>
                      <td style={s.td}>
                        <span style={{
                          ...s.scoreBadge,
                          background: m.score === 1 ? "#27ae60" : m.score >= 0.9 ? "#e67e22" : "#c0392b"
                        }}>
                          {(m.score * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Componente CSAT ──────────────────────────────────────────────────────────
function CSATModule() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleAnalyse() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("http://localhost:8000/csat", { method: "POST", body: form });
      setResult(await res.json());
    } catch {
      setError("Erro ao conectar na API.");
    }
    setLoading(false);
  }

  const npsColor = (score) => score >= 50 ? "#27ae60" : score >= 0 ? "#e67e22" : "#c0392b";

  return (
    <div>
      <div style={s.card}>
        <h2 style={s.cardTitle}>Upload de Feedback CSAT/NPS</h2>
        <p style={s.cardDesc}>CSV com colunas: <code>comentario, nps_score, canal, produto</code></p>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} />
        {file && <p style={s.fileName}>📄 {file.name}</p>}
        <button onClick={handleAnalyse} disabled={!file || loading}
          style={!file || loading ? { ...s.btnDisabled, marginTop: 16 } : { ...s.btn, marginTop: 16 }}>
          {loading ? "Analisando..." : "Analisar Feedback"}
        </button>
      </div>

      {error && <div style={s.errorBox}>⚠️ {error}</div>}

      {result && (
        <>
          {/* NPS Score */}
          <div style={s.metricsRow}>
            <div style={{ ...s.metricCard, flex: 2, textAlign: "center" }}>
              <div style={{ fontSize: 48, fontWeight: 700, color: npsColor(result.resumo.nps_score) }}>
                {result.resumo.nps_score}
              </div>
              <div style={s.metricLabel}>NPS Score</div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                {result.resumo.nps_score >= 50 ? "Excelente" :
                  result.resumo.nps_score >= 0 ? "Precisa melhorar" : "Crítico"}
              </div>
            </div>
            {[
              { label: "Promotores", value: `${result.resumo.promotores} (${result.resumo.pct_promotores}%)`, color: "#27ae60" },
              { label: "Neutros", value: result.resumo.neutros, color: "#888" },
              { label: "Detratores", value: `${result.resumo.detratores} (${result.resumo.pct_detratores}%)`, color: "#c0392b" },
            ].map((m, i) => (
              <div key={i} style={s.metricCard}>
                <div style={{ ...s.metricNum, color: m.color }}>{m.value}</div>
                <div style={s.metricLabel}>{m.label}</div>
              </div>
            ))}
          </div>

          {/* Sentimentos */}
          <div style={s.metricsRow}>
            {[
              { label: "😊 Positivo", value: result.sentimentos.positivo, color: "#27ae60" },
              { label: "😐 Neutro", value: result.sentimentos.neutro, color: "#888" },
              { label: "😠 Negativo", value: result.sentimentos.negativo, color: "#c0392b" },
            ].map((m, i) => (
              <div key={i} style={s.metricCard}>
                <div style={{ ...s.metricNum, color: m.color }}>{m.value}</div>
                <div style={s.metricLabel}>{m.label}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            {/* Temas de insatisfação */}
            <div style={s.card}>
              <h2 style={s.cardTitle}>🔴 Temas de Insatisfação</h2>
              {result.temas_insatisfacao.map((t, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: "#333" }}>{t.tema}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                      width: `${Math.min(t.frequencia * 3, 100)}px`,
                      height: 8, borderRadius: 4,
                      background: "#e74c3c", opacity: 0.7
                    }} />
                    <span style={{ fontSize: 12, color: "#888", minWidth: 24 }}>{t.frequencia}x</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Temas de satisfação */}
            <div style={s.card}>
              <h2 style={s.cardTitle}>🟢 Temas de Satisfação</h2>
              {result.temas_satisfacao.map((t, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: "#333" }}>{t.tema}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                      width: `${Math.min(t.frequencia * 3, 100)}px`,
                      height: 8, borderRadius: 4,
                      background: "#27ae60", opacity: 0.7
                    }} />
                    <span style={{ fontSize: 12, color: "#888", minWidth: 24 }}>{t.frequencia}x</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* NPS por canal */}
          <div style={s.card}>
            <h2 style={s.cardTitle}>NPS por Canal</h2>
            {Object.entries(result.por_canal).map(([canal, score], i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                <span style={{ fontSize: 13, color: "#333", minWidth: 140 }}>{canal}</span>
                <div style={{ flex: 1, background: "#f0f0f0", borderRadius: 4, height: 10 }}>
                  <div style={{
                    width: `${(score / 10) * 100}%`,
                    height: 10, borderRadius: 4,
                    background: score >= 8 ? "#27ae60" : score >= 6 ? "#e67e22" : "#c0392b"
                  }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#333", minWidth: 30 }}>{score}</span>
              </div>
            ))}
          </div>

          {/* Amostra detratores */}
          <div style={s.card}>
            <h2 style={s.cardTitle}>⚠️ Amostra de Detratores</h2>
            {result.amostra_detratores.map((d, i) => (
              <div key={i} style={{
                padding: "10px 14px", borderRadius: 8, marginBottom: 8,
                background: "#fdecea", borderLeft: "3px solid #e74c3c"
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#333", marginBottom: 2 }}>
                  {d.cliente} · {d.canal} · NPS {d.nps_score}
                </div>
                <div style={{ fontSize: 13, color: "#555" }}>{d.comentario}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── App principal ────────────────────────────────────────────────────────────
function App() {
  const [aba, setAba] = useState("kyc");

  return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.title}>SmartMatch</h1>
        <p style={s.subtitle}>Plataforma de compliance financeiro — KYC & CSAT Analytics</p>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        <button onClick={() => setAba("kyc")}
          style={aba === "kyc" ? s.tabActive : s.tab}>
          🔍 KYC — Deduplicação
        </button>
        <button onClick={() => setAba("csat")}
          style={aba === "csat" ? s.tabActive : s.tab}>
          📊 CSAT — NPS Analytics
        </button>
      </div>

      {aba === "kyc" ? <KYCModule /> : <CSATModule />}
    </div>
  );
}

// ─── Estilos ──────────────────────────────────────────────────────────────────
const s = {
  container: { maxWidth: 960, margin: "0 auto", padding: "24px 20px", fontFamily: "'Segoe UI', sans-serif", background: "#f5f6fa", minHeight: "100vh" },
  header: { marginBottom: 20 },
  title: { fontSize: 28, fontWeight: 700, color: "#1a1a2e", margin: 0 },
  subtitle: { color: "#666", fontSize: 14, marginTop: 4 },
  tabs: { display: "flex", gap: 8, marginBottom: 20 },
  tab: { padding: "10px 20px", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: "pointer", fontSize: 14, color: "#555" },
  tabActive: { padding: "10px 20px", borderRadius: 8, border: "none", background: "#1a1a2e", cursor: "pointer", fontSize: 14, color: "#fff", fontWeight: 600 },
  card: { background: "#fff", borderRadius: 12, padding: "24px", marginBottom: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  cardTitle: { fontSize: 16, fontWeight: 600, color: "#1a1a2e", marginTop: 0, marginBottom: 8, display: "flex", alignItems: "center", gap: 10 },
  cardDesc: { color: "#888", fontSize: 13, marginBottom: 12 },
  fileName: { fontSize: 13, color: "#27ae60", margin: "8px 0 0" },
  label: { fontSize: 14, color: "#444", display: "block" },
  btn: { background: "#1a1a2e", color: "#fff", border: "none", borderRadius: 8, padding: "11px 24px", fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnDisabled: { background: "#ccc", color: "#fff", border: "none", borderRadius: 8, padding: "11px 24px", fontSize: 14, fontWeight: 600, cursor: "default" },
  errorBox: { background: "#fdecea", border: "1px solid #e74c3c", borderRadius: 8, padding: "12px 16px", color: "#c0392b", fontSize: 14, marginBottom: 16 },
  metricsRow: { display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" },
  metricCard: { flex: 1, minWidth: 100, background: "#fff", borderRadius: 12, padding: "16px", textAlign: "center", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  metricNum: { fontSize: 24, fontWeight: 700, color: "#1a1a2e" },
  metricLabel: { fontSize: 12, color: "#888", marginTop: 4 },
  badge: { background: "#f0f0f0", borderRadius: 20, padding: "2px 10px", fontSize: 12, fontWeight: 500, color: "#555" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: { padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#444", borderBottom: "2px solid #eee" },
  td: { padding: "9px 14px", color: "#333", borderBottom: "1px solid #f0f0f0" },
  scoreBadge: { display: "inline-block", padding: "2px 10px", borderRadius: 20, color: "#fff", fontSize: 12, fontWeight: 600 },
};

export default App;