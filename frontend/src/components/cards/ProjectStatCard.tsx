interface ProjectStatCardProps {
  label: string;
  value: string | number;
}

export default function ProjectStatCard({ label, value }: ProjectStatCardProps) {
  return (
    <div>
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}
