export function formatPrazo(prazo: string | null): string {
  if (!prazo) return "—";
  const [year, month, day] = prazo.split("-");
  return `${day}/${month}/${year}`;
}
