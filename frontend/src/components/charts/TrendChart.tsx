import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistoricoPonto } from "../../types/api";
import { useTheme } from "../../contexts/ThemeContext";

type TrendMetric = "total_tarefas" | "concluidas" | "atrasadas" | "taxa_conclusao";

const METRIC_LABELS: Record<TrendMetric, string> = {
  total_tarefas: "Total",
  concluidas: "Concluídas",
  atrasadas: "Atrasadas",
  taxa_conclusao: "Taxa de conclusão",
};

const METRIC_ORDER: TrendMetric[] = ["total_tarefas", "concluidas", "atrasadas", "taxa_conclusao"];

const COLORS: Record<"light" | "dark", Record<TrendMetric, string>> = {
  light: {
    total_tarefas: "#4a3aa7",
    concluidas: "#1baf7a",
    atrasadas: "#eda100",
    taxa_conclusao: "#1baf7a",
  },
  dark: {
    total_tarefas: "#9085e9",
    concluidas: "#199e70",
    atrasadas: "#c98500",
    taxa_conclusao: "#199e70",
  },
};

const AXIS_COLORS = { light: "#5b6360", dark: "#a9b3b0" };
const GRID_COLORS = { light: "#dde3e0", dark: "#2c3436" };

interface TrendChartProps {
  historico: HistoricoPonto[];
}

function formatData(iso: string): string {
  const [, mes, dia] = iso.split("-");
  return `${dia}/${mes}`;
}

export default function TrendChart({ historico }: TrendChartProps) {
  const { theme } = useTheme();
  const [metric, setMetric] = useState<TrendMetric>("total_tarefas");
  const color = COLORS[theme][metric];
  const axisColor = AXIS_COLORS[theme];
  const gridColor = GRID_COLORS[theme];

  const data = historico.map((ponto) => ({ ...ponto, dataLabel: formatData(ponto.data) }));

  return (
    <div className="card chart-card">
      <div className="chart-card-header">
        <h2>Tendência</h2>
        <div className="metric-switch">
          {METRIC_ORDER.map((option) => (
            <button
              key={option}
              type="button"
              className={`metric-switch-btn ${metric === option ? "metric-switch-btn--active" : ""}`}
              onClick={() => setMetric(option)}
            >
              {METRIC_LABELS[option]}
            </button>
          ))}
        </div>
      </div>

      {historico.length < 3 && (
        <p className="alert alert-warning">
          Ainda estamos formando o histórico — esse gráfico fica mais útil
          depois de alguns dias de uso.
          {historico.length > 0 &&
            ` (${historico.length} ${historico.length === 1 ? "dia registrado" : "dias registrados"} até agora)`}
        </p>
      )}

      {historico.length === 0 ? null : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid vertical={false} stroke={gridColor} />
            <XAxis
              dataKey="dataLabel"
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={32}
              unit={metric === "taxa_conclusao" ? "%" : ""}
            />
            <Tooltip
              formatter={(value) => [
                metric === "taxa_conclusao" ? `${value}%` : String(value),
                METRIC_LABELS[metric],
              ]}
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--rule)",
                borderRadius: "8px",
                fontSize: "0.85rem",
                color: "var(--ink)",
              }}
              itemStyle={{ color: "var(--ink)" }}
            />
            <Line
              type="monotone"
              dataKey={metric}
              stroke={color}
              strokeWidth={2}
              dot={{ r: 3, fill: color }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
