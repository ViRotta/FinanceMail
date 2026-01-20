import { useEffect, useMemo, useState } from "react";
import { apiClassificar, apiFeedback } from "./api";

const STORAGE_KEY = "financemail_history_v1";

function nivelConfianca(valor) {
  const v = Number(valor || 0);
  if (v >= 0.8) return "alta";
  if (v >= 0.6) return "media";
  return "baixa";
}

function clampPct(valor) {
  const v = Number(valor || 0);
  const pct = Math.round(v * 100);
  return Math.max(0, Math.min(100, pct));
}

function nowIso() {
  return new Date().toISOString();
}

function makeId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return String(Date.now()) + "_" + Math.random().toString(16).slice(2);
}

export default function App() {
  const [texto, setTexto] = useState("");

  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [resultado, setResultado] = useState(null);

  // feedback UI
  const [feedbackMsg, setFeedbackMsg] = useState("");
  const [mostrarEscolhaCorreto, setMostrarEscolhaCorreto] = useState(false);
  const [categoriaCorreta, setCategoriaCorreta] = useState("produtivo");

  // historico
  const [historico, setHistorico] = useState([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const arr = raw ? JSON.parse(raw) : [];
      if (Array.isArray(arr)) setHistorico(arr);
    } catch {
      setHistorico([]);
    }
  }, []);

  const historico10 = useMemo(() => historico.slice(0, 10), [historico]);

  function salvarHistorico(item) {
    const novo = [item, ...historico].slice(0, 10);
    setHistorico(novo);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(novo));
  }

  function limparHistorico() {
    setHistorico([]);
    localStorage.removeItem(STORAGE_KEY);
  }

  async function onClassificar() {
    setErro("");
    setFeedbackMsg("");
    setMostrarEscolhaCorreto(false);
    setResultado(null);

    const t = (texto || "").trim();
    if (!t) {
      setErro("Cole um e-mail antes de classificar.");
      return;
    }

    setCarregando(true);
    try {
      const data = await apiClassificar(t);
      setResultado(data);

      salvarHistorico({
        id: makeId(),
        createdAt: nowIso(),
        texto: t,
        categoria: data?.categoria,
        confianca: data?.confianca,
        fonte: data?.fonte,
        resposta: data?.resposta,
      });

      setCategoriaCorreta(data?.categoria === "produtivo" ? "improdutivo" : "produtivo");
    } catch (e) {
      setErro(e?.message || "Erro ao classificar.");
    } finally {
      setCarregando(false);
    }
  }

  async function copiarResposta() {
    if (!resultado?.resposta) return;
    try {
      await navigator.clipboard.writeText(resultado.resposta);
      setFeedbackMsg("Resposta copiada ✅");
      setTimeout(() => setFeedbackMsg(""), 1500);
    } catch {
      setFeedbackMsg("Nao consegui copiar (permissao do navegador).");
      setTimeout(() => setFeedbackMsg(""), 2000);
    }
  }

  async function enviarFeedback(correto) {
    if (!resultado?.categoria) return;

    setErro("");
    setFeedbackMsg("");

    const payload = {
      texto: (texto || "").trim(),
      previsto: resultado.categoria,
      correto,
    };

    try {
      await apiFeedback(payload);
      setFeedbackMsg("Feedback salvo ✅");
      setTimeout(() => setFeedbackMsg(""), 2000);
      setMostrarEscolhaCorreto(false);
    } catch (e) {
      setErro(e?.message || "Erro ao salvar feedback.");
    }
  }

  const confiancaNum = Number(resultado?.confianca ?? 0);
  const pct = clampPct(confiancaNum);
  const nivel = nivelConfianca(confiancaNum);

  return (
    <div className="page">
      <div className="container">
        <header className="top">
          <div>
            <h1>FinanceMail</h1>
            <p className="subtitle">Cole um e-mail e veja se e produtivo ou improdutivo.</p>
          </div>

          <button className="btn ghost" onClick={limparHistorico} type="button">
            Limpar historico
          </button>
        </header>

        <section className="card">
          <label className="label">Texto do e-mail</label>
          <textarea
            className="textarea"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            rows={8}
            placeholder="Cole aqui o conteudo do e-mail..."
          />

          <div className="row">
            <button className="btn primary" onClick={onClassificar} disabled={carregando} type="button">
              {carregando ? "Classificando..." : "Classificar"}
            </button>
          </div>

          {erro ? <div className="alert">{erro}</div> : null}
        </section>

        {resultado ? (
          <section className="card">
            <div className="chips">
              <span className={`chip ${resultado.categoria === "produtivo" ? "chip-green" : "chip-gray"}`}>
                {resultado.categoria}
              </span>
              <span className="chip">fonte: {resultado.fonte || "modelo"}</span>
              <span className="chip">
                confianca: {pct}% ({nivel})
              </span>
            </div>

            <div className="progress">
              <div className="bar" style={{ width: `${pct}%` }} />
            </div>

            <div className="block">
              <div className="blockTitle">Resposta sugerida</div>
              <textarea className="textarea small" value={resultado.resposta || ""} readOnly rows={7} />
              <div className="row">
                <button className="btn ghost" onClick={copiarResposta} type="button">
                  Copiar resposta
                </button>
                {feedbackMsg ? <span className="hint ok">{feedbackMsg}</span> : null}
              </div>
            </div>

            <div className="block">
              <div className="blockTitle">Essa classificacao esta correta?</div>

              <div className="row">
                <button className="btn primary" type="button" onClick={() => enviarFeedback(resultado.categoria)}>
                  👍 Sim
                </button>

                <button className="btn danger" type="button" onClick={() => setMostrarEscolhaCorreto(true)}>
                  👎 Nao
                </button>

                {feedbackMsg ? <span className="hint ok">{feedbackMsg}</span> : null}
              </div>

              {mostrarEscolhaCorreto ? (
                <div className="row wrap">
                  <select className="select" value={categoriaCorreta} onChange={(e) => setCategoriaCorreta(e.target.value)}>
                    <option value="produtivo">produtivo</option>
                    <option value="improdutivo">improdutivo</option>
                  </select>

                  <button className="btn ghost" type="button" onClick={() => enviarFeedback(categoriaCorreta)}>
                    Enviar feedback
                  </button>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        <section className="card">
          <div className="blockTitle">Historico (ultimos 10)</div>

          {historico10.length === 0 ? (
            <div className="hint">Nenhum historico ainda.</div>
          ) : (
            <div className="history">
              {historico10.map((h) => (
                <div key={h.id} className="historyItem">
                  <div className="historyTop">
                    <span className={`chip ${h.categoria === "produtivo" ? "chip-green" : "chip-gray"}`}>
                      {h.categoria}
                    </span>
                    <span className="hint">
                      {Math.round(Number(h.confianca || 0) * 100)}% • {h.fonte || "modelo"}
                    </span>
                  </div>
                  <div className="historyText">{h.texto}</div>
                </div>
              ))}
            </div>
          )}
        </section>

        <footer className="footer">
          <span className="hint">Dev: proxy do Vite (/api → 127.0.0.1:8000)</span>
        </footer>
      </div>
    </div>
  );
}
