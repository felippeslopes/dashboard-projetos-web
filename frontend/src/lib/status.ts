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
