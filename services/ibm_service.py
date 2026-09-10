"""
IBM watsonx.ai Service — integration with IBM Granite models.
All credentials read from environment variables.
"""
import logging
from config import Config

logger = logging.getLogger(__name__)

_ibm_client = None


def _get_ibm_client():
    global _ibm_client
    if _ibm_client is not None:
        return _ibm_client
    if not Config.ibm_configured():
        logger.warning("IBM watsonx.ai credentials not configured.")
        return None
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        creds = Credentials(url=Config.IBM_WATSONX_URL, api_key=Config.IBM_WATSONX_API_KEY)
        _ibm_client = APIClient(credentials=creds, project_id=Config.IBM_PROJECT_ID)
        logger.info("IBM watsonx.ai client initialized.")
    except Exception as exc:
        logger.error(f"IBM watsonx.ai initialization error: {exc}")
        _ibm_client = None
    return _ibm_client


def generate_with_ibm(prompt: str, max_tokens: int = 1024,
                       temperature: float = 0.7) -> str | None:
    """
    Generate text using IBM Granite model.
    Returns generated text or None if IBM is unavailable.
    """
    client = _get_ibm_client()
    if client is None:
        return None
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params

        params = {
            Params.MAX_NEW_TOKENS: max_tokens,
            Params.TEMPERATURE: temperature,
            Params.REPETITION_PENALTY: 1.1,
        }
        model = ModelInference(
            model_id=Config.IBM_MODEL_ID,
            api_client=client,
            project_id=Config.IBM_PROJECT_ID,
            params=params,
        )
        response = model.generate_text(prompt=prompt)
        return response.strip() if response else None
    except Exception as exc:
        logger.error(f"IBM generation error: {exc}")
        return None


def ibm_status() -> dict:
    """Return the IBM configuration status for health checks."""
    configured = Config.ibm_configured()
    return {
        "configured": configured,
        "url": Config.IBM_WATSONX_URL if configured else None,
        "model_id": Config.IBM_MODEL_ID if configured else None,
        "orchestrate_configured": Config.ibm_orchestrate_configured(),
    }
