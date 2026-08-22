"""GET /api/v1/connections?from=lewis_hamilton&to=fangio — six degrees of
teammates (public)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.connections import service
from app.features.connections.schemas import ConnectionOut, GraphStatsOut, HopOut, ViaOut


router = APIRouter(prefix="/api/v1/connections", tags=["Connections"])


@router.get("", response_model=ConnectionOut, responses={404: {"description": "Unknown driver or no chain"}})
def connection(
    from_id: str = Query(alias="from", min_length=1, max_length=80),
    to_id: str = Query(alias="to", min_length=1, max_length=80),
    db: Session = Depends(get_db),
) -> ConnectionOut:
    """Shortest chain of shared-team links between two drivers."""
    try:
        result = service.connect(db, from_id, to_id)
    except service.ConnectionError_ as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ConnectionOut(
        from_id=from_id,
        to_id=to_id,
        degrees=result.degrees,
        path=[
            HopOut(
                driver_id=h.driver_id,
                name=h.name,
                via=ViaOut(**h.via._asdict()) if h.via else None,
            )
            for h in result.path
        ],
    )


@router.get("/stats", response_model=GraphStatsOut)
def stats(db: Session = Depends(get_db)) -> GraphStatsOut:
    return GraphStatsOut(**service.graph_stats(db))
