import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../services/api";
import type { DashboardResponse } from "../types/api";
import ColdStartLoader from "../components/ColdStartLoader";
import ProjectStatCard from "../components/cards/ProjectStatCard";
import ProjectsTable from "../components/table/ProjectsTable";
import StatusPieChart from "../components/charts/StatusPieChart";
import TaskFilters, {
  DEFAULT_FILTERS,
  applyFilters,
  type TaskFiltersState,
} from "../components/filters/TaskFilters";
import "./Dashboard.css";

type Status = "loading" | "ready" | "no-sheet" | "error";

export default function Dashboard() {
  const [status, setStatus] = useState<Status>("loading");
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFiltersState>(DEFAULT_FILTERS);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const response = await api.get("/dashboard");

        if (response.status === 404) {
          if (!cancelled) setStatus("no-sheet");
          return;
        }

        const body = await response.json();

        if (!response.ok) {
          throw new Error(body.detail ?? "Não foi possível carregar o dashboard.");
        }

        if (cancelled) return;
        setData(body as DashboardResponse);
        setStatus("ready");
      } catch (err) {
        if (cancelled) return;
        setErrorMessage(err instanceof Error ? err.message : "Erro inesperado.");
        setStatus("error");
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return <ColdStartLoader label="Carregando dashboard..." />;
  }

  if (status === "no-sheet") {
    return <Navigate to="/connect-sheet" replace />;
  }

  if (status === "error") {
    return (
      <div className="alert alert-error dashboard-error" role="alert">
        {errorMessage}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const filteredTarefas = applyFilters(data.tarefas, filters);

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Visão geral das tarefas conectadas à sua planilha.</p>
      </div>

      {(data.planilha_truncada || data.avisos.length > 0) && (
        <div className="dashboard-notices">
          {data.planilha_truncada && (
            <p className="alert alert-warning" role="alert">
              A planilha tem mais linhas do que o limite processado — só as
              primeiras 2000 linhas de dados foram consideradas.
            </p>
          )}

          {data.avisos.length > 0 && (
            <div className="alert alert-warning" role="alert">
              <ul>
                {data.avisos.map((aviso) => (
                  <li key={aviso}>{aviso}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="stat-grid">
        <ProjectStatCard label="Total de Tarefas" value={data.cards.total_tarefas} accent />
        <ProjectStatCard label="Em Andamento" value={data.cards.em_andamento} />
        <ProjectStatCard label="Concluídas" value={data.cards.concluidas} />
        <ProjectStatCard label="Atrasadas" value={data.cards.atrasadas} />
        <ProjectStatCard
          label="Taxa de Conclusão"
          value={`${data.cards.taxa_conclusao}%`}
        />
      </div>

      <div className="dashboard-main">
        <StatusPieChart data={data.grafico_status} />
        <TaskFilters tarefas={data.tarefas} value={filters} onChange={setFilters} />
        <ProjectsTable tarefas={filteredTarefas} groupBy={filters.groupBy} />
      </div>
    </div>
  );
}
