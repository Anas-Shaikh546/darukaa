from fastapi import APIRouter

from app.schemas.environment import EnvironmentInput
from app.schemas.recommendation import RecommendationOutput
from app.services.reasoning import reason

router = APIRouter(prefix="/api/v1/recommendation", tags=["recommendation"])


@router.post("/generate", response_model=RecommendationOutput)
def generate_recommendation(env: EnvironmentInput) -> RecommendationOutput:
    """
    Generate an evidence-grounded, multi-variable biodiversity recommendation
    based on the provided environmental state.
    """
    return reason(env)
