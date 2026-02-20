from fastapi import APIRouter, Depends, HTTPException
from app.monitoring.metrics import metrics, get_health_status
from app.middleware.auth import require_api_key
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/metrics", dependencies=[Depends(require_api_key)])
async def get_metrics():
    """
    Get application metrics.
    Requires API key authentication.
    """
    try:
        return metrics.get_metrics()
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.get("/health")
async def get_health():
    """
    Get application health status.
    Public endpoint - no authentication required.
    """
    try:
        return get_health_status()
    except Exception as e:
        logger.error("Failed to get health status", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/status", dependencies=[Depends(require_api_key)])
async def get_detailed_status():
    """
    Get detailed application status.
    Requires API key authentication.
    """
    try:
        health_data = get_health_status()
        metrics_data = metrics.get_metrics()
        
        return {
            "status": health_data["status"],
            "health_checks": health_data["checks"],
            "summary": {
                "uptime": health_data["metrics"]["uptime_formatted"],
                "total_requests": health_data["metrics"]["requests"]["total"],
                "error_rate": f"{health_data['metrics']['requests']['error_rate_percent']}%",
                "avg_processing_time": f"{health_data['metrics']['processing']['avg_time_ms']}ms",
                "last_request": health_data["metrics"]["system"]["last_request"]
            }
        }
    except Exception as e:
        logger.error("Failed to get detailed status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve status")
