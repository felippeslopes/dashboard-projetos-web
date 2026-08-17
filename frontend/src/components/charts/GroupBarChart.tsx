import { useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { GroupBreakdown } from "../../types/api";
import { METRIC_COLORS, METRIC_LABELS, type ChartMetric } from "../../lib/status";
import { useTheme } from "../../contexts/ThemeContext";
import "./GroupBarChart.css";

interface GroupBarChartProps {
  title: string;
  data: GroupBreakdown[];
}

const AXIS_COLORS: Record<"light" | "dark", string> = {
  light: "#5b6360",
  dark: "#a9b3b0",
};

const METRICS: ChartMetric[] = ["total", "atrasadas", "taxa_conclusao"];

export default function GroupBarChart({ title, data }: GroupBarChartProps) {
  const { theme } = useTheme();
  const [metric, setMetric] = useState<ChartMetric>("total");
  const color = METRIC_COLORS[theme][metric];
  const axisColor = AXIS_COLORS[theme];
  const height = Math.max(120, data.length * 42 + 24);

  return (
    <div className="card chart-card">
      <div className="chart-card-header">
        <h2>{title}</h2>
        <div className="metric-switch">
          {METRICS.map((option) => (
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

      {data.length === 0 ? (
        <p className="chart-empty">Sem dados suficientes para este gráfico.</p>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 28, bottom: 4, left: 4 }}>
            <XAxis
              type="number"
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              unit={metric === "taxa_conclusao" ? "%" : ""}
            />
            <YAxis
              type="category"
              dataKey="chave"
              width={110}
              tick={{ fill: axisColor, fontSize: 12 }}
              tickLine={false}
              axisLine={false}
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
              cursor={{ fill: "var(--paper)" }}
            />
            <Bar dataKey={metric} radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry) => (
                <Cell key={entry.chave} fill={color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
