"""PriorityAI router — Multi-Agent 优先级排序系统集成"""

from fastapi import APIRouter, HTTPException

from .agents.orchestrator import AgentOrchestrator
from .schemas import PrioritizeRequest

router = APIRouter(prefix="/api/priority", tags=["priority"])
orchestrator = AgentOrchestrator()


@router.get("/health")
def priority_health():
    return {
        'status': 'healthy',
        'service': 'PriorityAI',
        'version': '1.0.0',
        'agents': ['StatusAgent', 'TaskAgent', 'RankingAgent'],
    }


@router.post("/prioritize")
def prioritize(payload: PrioritizeRequest):
    try:
        user_state = payload.user_state.model_dump()
        tasks = [t.model_dump() for t in payload.tasks]
        return orchestrator.run(user_state, tasks)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agents/status")
def agents_status():
    return orchestrator.get_status()
