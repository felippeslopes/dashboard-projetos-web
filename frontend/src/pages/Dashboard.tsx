import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../services/api";
import type { DashboardResponse, Tarefa } from "../types/api";
import ColdStartLoader from "../components/ColdStartLoader";
import ProjectStatCard from "../components/cards/ProjectStatCard";
import ProjectsTable from "../components/table/ProjectsTable";
import StatusPieChart from "../components/charts/StatusPieChart";
import GroupBarChart from "../components/charts/GroupBarChart";
import TimelineBarChart from "../components/charts/TimelineBarChart";
import KanbanBoard from "../components/kanban/KanbanBoard";
import TaskFilters, {
  DEFAULT_FILTERS,
  applyFilters,
  type TaskFiltersState,
} from "../components/filters/TaskFilters";
import "./Dashboard.css";

type Status = "loading" | "ready" | "no-sheet" | "error";
type View = "tabela" | "kanban";

export default function Dashboard() {
  const [status, setStatus] = useState<Status>("loading");
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFiltersState>(DEFAULT_FILTERS);
  const [view, setView] = useState<View>("tabela");
  const [kanbanError, setKanbanError] = useState<string | null>(null);

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

  async function handleStatusChange(tarefa: Tarefa, novoStatus: string) {
    const previousStatus = tarefa.status;
    setKanbanError(null);
    setData((current) =>
      current
        ? {
            ...current,
            tarefas: current.tarefas.map((t) =>
              t.linha_planilha === tarefa.linha_planilha ? { ...t, status: novoStatus } : t,
            ),
          }
        : current,
    );

    try {
      const response = await api.patch(
        `/dashboard/tarefas/${tarefa.linha_planilha}/status`,
        { status: novoStatus, status_esperado: previousStatus },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Não foi possível salvar a alteração.");
      }
    } catch (err) {
      setData((current) =>
        current
          ? {
              ...current,
              tarefas: current.tarefas.map((t) =>
                t.linha_planilha === tarefa.linha_planilha
                  ? { ...t, status: previousStatus }
                  : t,
              ),
            }
          : current,
      );
      setKanbanError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

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

        <div className="charts-grid">
          <GroupBarChart title="Tarefas por Projeto" data={data.grafico_projeto} />
          <GroupBarChart title="Tarefas por Responsável" data={data.grafico_responsavel} />
        </div>

        <TimelineBarChart data={data.grafico_prazo} />

        <div className="view-switch" role="tablist" aria-label="Modo de visualização">
          <button
            type="button"
            role="tab"
            aria-selected={view === "tabela"}
            className={`view-switch-btn ${view === "tabela" ? "view-switch-btn--active" : ""}`}
            onClick={() => setView("tabela")}
          >
            Tabela
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "kanban"}
            className={`view-switch-btn ${view === "kanban" ? "view-switch-btn--active" : ""}`}
            onClick={() => setView("kanban")}
          >
            Kanban
          </button>
        </div>

        <TaskFilters
          tarefas={data.tarefas}
          value={filters}
          onChange={setFilters}
          showGroupBy={view === "tabela"}
        />

        {view === "kanban" && kanbanError && (
          <p className="alert alert-error" role="alert">
            {kanbanError}
          </p>
        )}

        {view === "tabela" ? (
          <ProjectsTable tarefas={filteredTarefas} groupBy={filters.groupBy} />
        ) : (
          <KanbanBoard tarefas={filteredTarefas} onStatusChange={handleStatusChange} />
        )}
      </div>
    </div>
  );
}
