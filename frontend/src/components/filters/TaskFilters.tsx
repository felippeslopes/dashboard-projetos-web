import { useMemo } from "react";
import type { Tarefa } from "../../types/api";
import { statusClass, compareStatus } from "../../lib/status";
import "./TaskFilters.css";

export type GroupBy = "none" | "status" | "responsavel" | "projeto";

export interface TaskFiltersState {
  search: string;
  projeto: string;
  responsavel: string;
  statuses: string[];
  groupBy: GroupBy;
}

export const DEFAULT_FILTERS: TaskFiltersState = {
  search: "",
  projeto: "",
  responsavel: "",
  statuses: [],
  groupBy: "none",
};

interface TaskFiltersProps {
  tarefas: Tarefa[];
  value: TaskFiltersState;
  onChange: (next: TaskFiltersState) => void;
}

function uniqueSorted(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) =>
    a.localeCompare(b, "pt-BR"),
  );
}

function orderedStatuses(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort(compareStatus);
}

export function isFiltersActive(filters: TaskFiltersState): boolean {
  return (
    filters.search.trim() !== "" ||
    filters.projeto !== "" ||
    filters.responsavel !== "" ||
    filters.statuses.length > 0
  );
}

export default function TaskFilters({ tarefas, value, onChange }: TaskFiltersProps) {
  const projetos = useMemo(() => uniqueSorted(tarefas.map((t) => t.projeto)), [tarefas]);
  const responsaveis = useMemo(
    () => uniqueSorted(tarefas.map((t) => t.responsavel)),
    [tarefas],
  );
  const statuses = useMemo(
    () => orderedStatuses(tarefas.map((t) => t.status)),
    [tarefas],
  );

  function toggleStatus(status: string) {
    const next = value.statuses.includes(status)
      ? value.statuses.filter((s) => s !== status)
      : [...value.statuses, status];
    onChange({ ...value, statuses: next });
  }

  return (
    <div className="card task-filters">
      <div className="task-filters-row">
        <input
          type="search"
          className="input task-filters-search"
          placeholder="Buscar tarefa..."
          value={value.search}
          onChange={(event) => onChange({ ...value, search: event.target.value })}
        />

        <select
          className="input"
          value={value.projeto}
          onChange={(event) => onChange({ ...value, projeto: event.target.value })}
          aria-label="Filtrar por projeto"
        >
          <option value="">Todos os projetos</option>
          {projetos.map((projeto) => (
            <option key={projeto} value={projeto}>
              {projeto}
            </option>
          ))}
        </select>

        <select
          className="input"
          value={value.responsavel}
          onChange={(event) => onChange({ ...value, responsavel: event.target.value })}
          aria-label="Filtrar por responsável"
        >
          <option value="">Todos os responsáveis</option>
          {responsaveis.map((responsavel) => (
            <option key={responsavel} value={responsavel}>
              {responsavel}
            </option>
          ))}
        </select>

        <select
          className="input"
          value={value.groupBy}
          onChange={(event) =>
            onChange({ ...value, groupBy: event.target.value as GroupBy })
          }
          aria-label="Agrupar por"
        >
          <option value="none">Sem agrupamento</option>
          <option value="status">Agrupar por status</option>
          <option value="responsavel">Agrupar por responsável</option>
          <option value="projeto">Agrupar por projeto</option>
        </select>

        {isFiltersActive(value) && (
          <button
            type="button"
            className="btn task-filters-clear"
            onClick={() => onChange({ ...DEFAULT_FILTERS, groupBy: value.groupBy })}
          >
            Limpar filtros
          </button>
        )}
      </div>

      <div className="task-filters-statuses">
        {statuses.map((status) => (
          <button
            key={status}
            type="button"
            className={`status-chip ${statusClass(status)} ${
              value.statuses.includes(status) ? "status-chip--active" : ""
            }`}
            onClick={() => toggleStatus(status)}
            aria-pressed={value.statuses.includes(status)}
          >
            {status}
          </button>
        ))}
      </div>
    </div>
  );
}

export function applyFilters(tarefas: Tarefa[], filters: TaskFiltersState): Tarefa[] {
  const search = filters.search.trim().toLowerCase();

  return tarefas.filter((tarefa) => {
    if (search && !tarefa.nome.toLowerCase().includes(search)) return false;
    if (filters.projeto && tarefa.projeto !== filters.projeto) return false;
    if (filters.responsavel && tarefa.responsavel !== filters.responsavel) return false;
    if (filters.statuses.length > 0 && !filters.statuses.includes(tarefa.status)) {
      return false;
    }
    return true;
  });
}
