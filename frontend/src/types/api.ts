export interface Tarefa {
  projeto: string;
  nome: string;
  status: string;
  responsavel: string;
  prazo: string | null;
  linha_planilha: number;
}

export interface DashboardCards {
  total_tarefas: number;
  em_andamento: number;
  concluidas: number;
  atrasadas: number;
  taxa_conclusao: number;
}

export interface StatusBreakdown {
  status: string;
  quantidade: number;
}

export interface GroupBreakdown {
  chave: string;
  total: number;
  concluidas: number;
  atrasadas: number;
  taxa_conclusao: number;
}

export interface PeriodoBreakdown {
  periodo: string;
  total: number;
}

export interface HistoricoPonto {
  data: string;
  total_tarefas: number;
  concluidas: number;
  atrasadas: number;
  taxa_conclusao: number;
}

export interface DashboardResponse {
  cards: DashboardCards;
  tarefas: Tarefa[];
  grafico_status: StatusBreakdown[];
  grafico_projeto: GroupBreakdown[];
  grafico_responsavel: GroupBreakdown[];
  grafico_prazo: PeriodoBreakdown[];
  historico: HistoricoPonto[];
  avisos: string[];
  planilha_truncada: boolean;
}

export interface UserConfigResponse {
  sheet_id: string;
  connected_at: string;
}

export interface ConfigStatusResponse {
  service_account_email: string;
  config: UserConfigResponse | null;
}
