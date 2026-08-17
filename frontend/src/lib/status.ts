export const CANONICAL_STATUS_ORDER = [
  "Planejado",
  "Em andamento",
  "Concluído",
  "Atrasado",
  "Cancelado",
];

const STATUS_CLASSES: Record<string, string> = {
  "planejado": "status-planejado",
  "em andamento": "status-em-andamento",
  "concluído": "status-concluido",
  "concluido": "status-concluido",
  "atrasado": "status-atrasado",
  "cancelado": "status-cancelado",
};

export function statusClass(status: string): string {
  return STATUS_CLASSES[status.trim().toLowerCase()] ?? "status-outros";
}

export function compareStatus(a: string, b: string): number {
  const ia = CANONICAL_STATUS_ORDER.indexOf(a);
  const ib = CANONICAL_STATUS_ORDER.indexOf(b);
  if (ia !== -1 && ib !== -1) return ia - ib;
  if (ia !== -1) return -1;
  if (ib !== -1) return 1;
  return a.localeCompare(b, "pt-BR");
}

// SVG presentation attributes (unlike the `style` attribute) don't resolve
// CSS custom properties, so chart fills need literal colors mirrored from
// global.css per theme instead of var() references.
export const STATUS_CHART_COLORS: Record<"light" | "dark", Record<string, string>> = {
  light: {
    Planejado: "#2a78d6",
    "Em andamento": "#eb6834",
    Concluído: "#1baf7a",
    Atrasado: "#eda100",
    Cancelado: "#e87ba4",
    Outros: "#8b9390",
  },
  dark: {
    Planejado: "#3987e5",
    "Em andamento": "#d95926",
    Concluído: "#199e70",
    Atrasado: "#c98500",
    Cancelado: "#d55181",
    Outros: "#6f7a77",
  },
};

export type ChartMetric = "total" | "atrasadas" | "taxa_conclusao";

// Mirrors --accent (light/dark) from global.css, plus the status colors
// above -- same var()-in-SVG-attribute limitation, resolved to literals.
export const METRIC_COLORS: Record<"light" | "dark", Record<ChartMetric, string>> = {
  light: {
    total: "#4a3aa7",
    atrasadas: STATUS_CHART_COLORS.light.Atrasado,
    taxa_conclusao: STATUS_CHART_COLORS.light.Concluído,
  },
  dark: {
    total: "#9085e9",
    atrasadas: STATUS_CHART_COLORS.dark.Atrasado,
    taxa_conclusao: STATUS_CHART_COLORS.dark.Concluído,
  },
};

export const METRIC_LABELS: Record<ChartMetric, string> = {
  total: "Total",
  atrasadas: "Atrasadas",
  taxa_conclusao: "Taxa de conclusão",
};
