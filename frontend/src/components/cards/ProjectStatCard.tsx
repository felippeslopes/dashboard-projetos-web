import "./ProjectStatCard.css";

interface ProjectStatCardProps {
  label: string;
  value: string | number;
  accent?: boolean;
}

export default function ProjectStatCard({ label, value, accent }: ProjectStatCardProps) {
  return (
    <div className={`card stat-card ${accent ? "stat-card--accent" : ""}`}>
      <p>{label}</p>
      <strong className="tabular-nums">{value}</strong>
    </div>
  );
}
