from dataclasses import dataclass
from datetime import date

from supabase import create_client

from app.core.config import get_settings
from app.schemas.project import DashboardCards

TABLE_NAME = "dashboard_snapshots"


@dataclass
class SnapshotRecord:
    snapshot_date: date
    total_tarefas: int
    em_andamento: int
    concluidas: int
    atrasadas: int
    taxa_conclusao: float


def _client(access_token: str):
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client


def upsert_snapshot(
    user_id: str, access_token: str, cards: DashboardCards, today: date | None = None
) -> None:
    today = today or date.today()
    _client(access_token).table(TABLE_NAME).upsert(
        {
            "user_id": user_id,
            "snapshot_date": today.isoformat(),
            "total_tarefas": cards.total_tarefas,
            "em_andamento": cards.em_andamento,
            "concluidas": cards.concluidas,
            "atrasadas": cards.atrasadas,
            "taxa_conclusao": cards.taxa_conclusao,
        },
        on_conflict="user_id,snapshot_date",
    ).execute()


def list_snapshots(user_id: str, access_token: str, dias: int = 30) -> list[SnapshotRecord]:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .select("snapshot_date, total_tarefas, em_andamento, concluidas, atrasadas, taxa_conclusao")
        .eq("user_id", user_id)
        .order("snapshot_date", desc=False)
        .limit(dias)
        .execute()
    )
    return [
        SnapshotRecord(
            snapshot_date=row["snapshot_date"],
            total_tarefas=row["total_tarefas"],
            em_andamento=row["em_andamento"],
            concluidas=row["concluidas"],
            atrasadas=row["atrasadas"],
            taxa_conclusao=row["taxa_conclusao"],
        )
        for row in response.data
    ]
