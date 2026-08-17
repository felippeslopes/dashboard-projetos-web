import { useMemo, useState } from "react";
import type { Tarefa } from "../../types/api";
import { statusClass, compareStatus } from "../../lib/status";
import type { GroupBy } from "../filters/TaskFilters";
import "./ProjectsTable.css";

interface ProjectsTableProps {
  tarefas: Tarefa[];
  groupBy?: GroupBy;
}

type SortField = "projeto" | "nome" | "status" | "responsavel" | "prazo";
type SortDirection = "asc" | "desc";

const COLUMNS: { field: SortField; label: string }[] = [
  { field: "projeto", label: "Projeto" },
  { field: "nome", label: "Tarefa" },
  { field: "status", label: "Status" },
  { field: "responsavel", label: "Responsável" },
  { field: "prazo", label: "Prazo" },
];

function formatPrazo(prazo: string | null): string {
  if (!prazo) return "—";
  const [year, month, day] = prazo.split("-");
  return `${day}/${month}/${year}`;
}

function compareTarefas(a: Tarefa, b: Tarefa, field: SortField): number {
  if (field === "status") return compareStatus(a.status, b.status);
  if (field === "prazo") {
    if (a.prazo === b.prazo) return 0;
    if (a.prazo === null) return 1;
    if (b.prazo === null) return -1;
    return a.prazo.localeCompare(b.prazo);
  }
  return a[field].localeCompare(b[field], "pt-BR");
}

function groupKey(tarefa: Tarefa, groupBy: GroupBy): string {
  if (groupBy === "status") return tarefa.status || "Sem status";
  if (groupBy === "responsavel") return tarefa.responsavel || "Sem responsável";
  if (groupBy === "projeto") return tarefa.projeto || "Sem projeto";
  return "";
}

function compareGroupKeys(a: string, b: string, groupBy: GroupBy): number {
  if (groupBy === "status") return compareStatus(a, b);
  return a.localeCompare(b, "pt-BR");
}

interface TableSectionProps {
  title?: string;
  tarefas: Tarefa[];
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

function TableSection({ title, tarefas, sortField, sortDirection, onSort }: TableSectionProps) {
  return (
    <div className="table-scroll">
      {title && (
        <div className="table-group-header">
          {title} <span className="table-group-count">{tarefas.length}</span>
        </div>
      )}
      <table className="projects-table">
        <thead>
          <tr>
            {COLUMNS.map((column) => (
              <th key={column.field}>
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => onSort(column.field)}
                >
                  {column.label}
                  {sortField === column.field && (
                    <span aria-hidden="true">{sortDirection === "asc" ? " ▲" : " ▼"}</span>
                  )}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tarefas.map((tarefa) => (
            <tr key={tarefa.linha_planilha}>
              <td>{tarefa.projeto}</td>
              <td>{tarefa.nome}</td>
              <td>
                <span className={`status-badge ${statusClass(tarefa.status)}`}>
                  {tarefa.status}
                </span>
              </td>
              <td>{tarefa.responsavel}</td>
              <td className="tabular-nums">{formatPrazo(tarefa.prazo)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ProjectsTable({ tarefas, groupBy = "none" }: ProjectsTableProps) {
  const [sortField, setSortField] = useState<SortField>("prazo");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  function handleSort(field: SortField) {
    if (field === sortField) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  }

  const sorted = useMemo(() => {
    const copy = [...tarefas].sort((a, b) => compareTarefas(a, b, sortField));
    return sortDirection === "asc" ? copy : copy.reverse();
  }, [tarefas, sortField, sortDirection]);

  const groups = useMemo(() => {
    if (groupBy === "none") return null;

    const map = new Map<string, Tarefa[]>();
    for (const tarefa of sorted) {
      const key = groupKey(tarefa, groupBy);
      const bucket = map.get(key);
      if (bucket) bucket.push(tarefa);
      else map.set(key, [tarefa]);
    }

    return Array.from(map.entries()).sort((a, b) => compareGroupKeys(a[0], b[0], groupBy));
  }, [sorted, groupBy]);

  if (tarefas.length === 0) {
    return (
      <div className="card table-card">
        <p className="projects-table-empty">Nenhuma tarefa encontrada.</p>
      </div>
    );
  }

  if (groups) {
    return (
      <div className="table-groups">
        {groups.map(([key, groupTarefas]) => (
          <div className="card table-card" key={key}>
            <TableSection
              title={key}
              tarefas={groupTarefas}
              sortField={sortField}
              sortDirection={sortDirection}
              onSort={handleSort}
            />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card table-card">
      <TableSection
        tarefas={sorted}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
      />
    </div>
  );
}
