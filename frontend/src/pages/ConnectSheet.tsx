import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import ColdStartLoader from "../components/ColdStartLoader";
import SheetFormatGuide from "../components/SheetFormatGuide";
import type { ConfigStatusResponse, UserConfigResponse } from "../types/api";
import "./ConnectSheet.css";

type Status = "loading" | "form" | "redirect" | "error";

export default function ConnectSheet() {
  const [searchParams] = useSearchParams();
  const forceReconnect = searchParams.get("trocar") === "1";
  const navigate = useNavigate();
  const { user } = useAuth();
  const loggedInWithMicrosoft = user?.app_metadata.provider === "azure";

  const [status, setStatus] = useState<Status>("loading");
  const [serviceAccountEmail, setServiceAccountEmail] = useState("");
  const [currentConfig, setCurrentConfig] = useState<UserConfigResponse | null>(null);
  const [sheetUrl, setSheetUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await api.get("/config");
        if (!response.ok) {
          throw new Error("Não foi possível carregar as informações de conexão.");
        }
        const data: ConfigStatusResponse = await response.json();
        if (cancelled) return;

        setServiceAccountEmail(data.service_account_email);

        if (data.config && !forceReconnect) {
          setStatus("redirect");
          return;
        }

        setCurrentConfig(data.config);
        setStatus("form");
      } catch (err) {
        if (cancelled) return;
        setLoadError(err instanceof Error ? err.message : "Erro inesperado.");
        setStatus("error");
      }
    }

    loadStatus();
    return () => {
      cancelled = true;
    };
  }, [forceReconnect]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      const response = await api.post("/config", { sheet_url: sheetUrl });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Não foi possível conectar a planilha.");
      }

      navigate("/dashboard", { replace: true });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCopyEmail() {
    await navigator.clipboard.writeText(serviceAccountEmail);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (status === "loading") {
    return <ColdStartLoader />;
  }

  if (status === "redirect") {
    return <Navigate to="/dashboard" replace />;
  }

  if (status === "error") {
    return (
      <div className="alert alert-error" role="alert">
        {loadError}
      </div>
    );
  }

  return (
    <div className="connect-sheet">
      <div className="page-header">
        <div className="connect-header">
          <h1>Conectar Planilha</h1>

          {currentConfig && (
            <Link to="/dashboard" className="btn connect-back-link">
              <span aria-hidden="true">←</span> Voltar ao Dashboard
            </Link>
          )}
        </div>
        <p>Aponte o sistema para a planilha do Google Sheets ou o arquivo do Excel Online com suas tarefas.</p>
      </div>

      {currentConfig && (
        <p className="alert alert-warning" role="status">
          Planilha atualmente conectada: <code>{currentConfig.sheet_id}</code>.
          Conectar uma nova planilha abaixo substitui essa conexão.
        </p>
      )}

      <SheetFormatGuide />

      <div className="connect-steps">
        <div className="card connect-step">
          <span className="connect-step-number">1</span>
          <div className="connect-step-body">
            <p>
              Abra sua planilha do Google Sheets ou o arquivo do Excel Online
              com as tarefas.
            </p>
          </div>
        </div>

        {loggedInWithMicrosoft ? (
          <div className="card connect-step">
            <span className="connect-step-number">2</span>
            <div className="connect-step-body">
              <p>
                Como você entrou com a conta Microsoft, <strong>não precisa
                compartilhar com ninguém</strong> — o acesso já é o da sua
                própria conta. Clique em &quot;Compartilhar&quot; →
                &quot;Copiar link&quot; só pra pegar o endereço do arquivo.
              </p>
            </div>
          </div>
        ) : (
          <div className="card connect-step">
            <span className="connect-step-number">2</span>
            <div className="connect-step-body">
              <p>
                Clique em &quot;Compartilhar&quot; e adicione o e-mail abaixo com
                permissão de <strong>Editor</strong> (necessário para o Kanban
                salvar mudanças de status na planilha):
              </p>
              <div className="connect-email-row">
                <code className="code-chip">{serviceAccountEmail}</code>
                <button type="button" className="btn" onClick={handleCopyEmail}>
                  {copied ? "Copiado!" : "Copiar"}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="card connect-step">
          <span className="connect-step-number">3</span>
          <div className="connect-step-body">
            <p>Cole abaixo o link compartilhado.</p>
          </div>
        </div>
      </div>

      <form className="card connect-form" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="sheet-url">Link da planilha ou do arquivo Excel</label>
          <input
            id="sheet-url"
            className="input"
            type="url"
            placeholder="https://docs.google.com/spreadsheets/d/... ou https://1drv.ms/..."
            value={sheetUrl}
            onChange={(event) => setSheetUrl(event.target.value)}
            required
          />
        </div>

        {formError && (
          <p className="alert alert-error" role="alert">
            {formError}
          </p>
        )}

        <div className="connect-form-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Conectando..." : "Conectar"}
          </button>
        </div>
      </form>
    </div>
  );
}
