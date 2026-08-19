import { CANONICAL_STATUS_ORDER, statusClass } from "../lib/status";
import "./SheetFormatGuide.css";

const COLUNAS = [
  {
    nome: "Projeto",
    descricao: "Texto livre. Agrupa as tarefas — não precisa existir uma lista fixa de projetos.",
  },
  {
    nome: "Tarefa",
    descricao: "Nome da tarefa. É o único campo obrigatório — linha sem isso é ignorada.",
  },
  {
    nome: "Status",
    descricao: "Um dos valores reconhecidos abaixo (veja a lista). Qualquer outro texto ainda funciona, só aparece agrupado como \"Outros\" nos gráficos.",
  },
  {
    nome: "Responsável",
    descricao: "Texto livre, só aparece na tabela e nos gráficos por responsável.",
  },
  {
    nome: "Prazo",
    descricao: "Data no formato DD/MM/AAAA ou AAAA-MM-DD. Pode ficar em branco sem quebrar a linha.",
  },
];

export default function SheetFormatGuide() {
  return (
    <details className="card sheet-format-guide">
      <summary>Ver formato esperado da planilha</summary>

      <div className="sheet-format-body">
        <p className="sheet-format-hint">
          Vale para os dois provedores — Google Sheets e Excel Online.
        </p>

        <section>
          <h3>Colunas</h3>
          <p className="sheet-format-hint">
            O cabeçalho precisa estar na primeira linha. A ordem das colunas
            não importa, e maiúsculas/acentos são tolerados (ex: "responsavel"
            ou "Responsável" funcionam igual).
          </p>
          <dl className="sheet-format-columns">
            {COLUNAS.map((coluna) => (
              <div key={coluna.nome} className="sheet-format-column">
                <dt>{coluna.nome}</dt>
                <dd>{coluna.descricao}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section>
          <h3>Status reconhecidos</h3>
          <ul className="sheet-format-statuses">
            {CANONICAL_STATUS_ORDER.map((status) => (
              <li key={status}>
                <span className={`status-badge ${statusClass(status)}`}>{status}</span>
              </li>
            ))}
          </ul>
          <p className="sheet-format-hint">
            Esses são os que ganham cor própria nos gráficos e alimentam o
            card "Taxa de Conclusão". Qualquer outro texto na coluna Status
            não trava nada — só entra no grupo "Outros".
          </p>
        </section>

        <section>
          <h3>Colunas e abas extras não atrapalham</h3>
          <ul className="sheet-format-notes">
            <li>
              <strong>Colunas a mais</strong> na mesma aba (além das 5 acima)
              são simplesmente ignoradas — pode manter anotações, fórmulas ou
              qualquer outra coluna que já use.
            </li>
            <li>
              <strong>Abas a mais</strong> também não atrapalham, mas com uma
              ressalva: o sistema sempre lê a <strong>primeira aba</strong>{" "}
              (a mais à esquerda). Garanta que suas tarefas estejam nela —
              abas adicionais depois da primeira são ignoradas.
            </li>
            <li>
              Limite de <strong>2.000 linhas</strong> processadas por
              planilha; se passar disso, um aviso aparece no dashboard.
            </li>
          </ul>
        </section>
      </div>
    </details>
  );
}
