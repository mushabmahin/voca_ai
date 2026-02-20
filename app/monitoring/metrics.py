import structlog
from typing import Dict, List, Optional
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = structlog.get_logger()

class MetricsCollector:
    """
    Simple metrics collector for monitoring application performance.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Request metrics
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        
        # Processing metrics
        self.processing_times = deque(maxlen=1000)  # Keep last 1000 requests
        self.language_counts = defaultdict(int)
        self.sentiment_counts = defaultdict(int)
        self.risk_scores = deque(maxlen=1000)
        
        # System metrics
        self.start_time = time.time()
        self.last_request_time = None
        
        # Rate limiting
        self.rate_limit_hits = defaultdict(int)
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """
        Record request metrics.
        """
        with self._lock:
            key = f"{method} {endpoint}"
            self.request_count[key] += 1
            self.request_duration[key].append(duration)
            
            if status_code >= 400:
                self.error_count[key] += 1
            
            self.last_request_time = time.time()
            
            # Keep only recent duration data (last 1000 requests per endpoint)
            if len(self.request_duration[key]) > 1000:
                self.request_duration[key] = self.request_duration[key][-1000:]
    
    def record_processing_time(self, duration: float, language: str = None, sentiment: str = None, risk_score: int = None):
        """
        Record processing metrics.
        """
        with self._lock:
            self.processing_times.append(duration)
            
            if language:
                self.language_counts[language] += 1
            
            if sentiment:
                self.sentiment_counts[sentiment] += 1
            
            if risk_score is not None:
                self.risk_scores.append(risk_score)
    
    def record_rate_limit_hit(self, api_key: str):
        """
        Record rate limit violations.
        """
        with self._lock:
            self.rate_limit_hits[api_key] += 1
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics.
        """
        with self._lock:
            uptime = time.time() - self.start_time
            
            # Calculate request statistics
            total_requests = sum(self.request_count.values())
            total_errors = sum(self.error_count.values())
            
            # Calculate average processing time
            avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
            
            # Calculate percentile processing times
            sorted_times = sorted(self.processing_times)
            p50_time = sorted_times[len(sorted_times) // 2] if sorted_times else 0
            p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
            
            # Calculate average risk score
            avg_risk_score = sum(self.risk_scores) / len(self.risk_scores) if self.risk_scores else 0
            
            # Calculate error rate
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "uptime_formatted": str(timedelta(seconds=int(uptime))),
                "requests": {
                    "total": total_requests,
                    "errors": total_errors,
                    "error_rate_percent": round(error_rate, 2),
                    "by_endpoint": dict(self.request_count),
                    "errors_by_endpoint": dict(self.error_count)
                },
                "processing": {
                    "avg_time_ms": round(avg_processing_time * 1000, 2),
                    "p50_time_ms": round(p50_time * 1000, 2),
                    "p95_time_ms": round(p95_time * 1000, 2),
                    "p99_time_ms": round(p99_time * 1000, 2),
                    "total_processed": len(self.processing_times)
                },
                "analysis": {
                    "languages": dict(self.language_counts),
                    "sentiments": dict(self.sentiment_counts),
                    "avg_risk_score": round(avg_risk_score, 1),
                    "risk_analyses": len(self.risk_scores)
                },
                "rate_limiting": {
                    "hits": dict(self.rate_limit_hits),
                    "total_hits": sum(self.rate_limit_hits.values())
                },
                "system": {
                    "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                    "last_request": datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None
                }
            }
    
    def get_health_status(self) -> Dict:
        """
        Get health status based on metrics.
        """
        metrics = self.get_metrics()
        
        health_checks = {
            "error_rate": metrics["requests"]["error_rate_percent"] < 10,  # Error rate < 10%
            "avg_processing_time": metrics["processing"]["avg_time_ms"] < 5000,  # < 5 seconds
            "p95_processing_time": metrics["processing"]["p95_time_ms"] < 10000,  # < 10 seconds
            "recent_requests": metrics["system"]["last_request"] is not None
        }
        
        overall_status = "healthy" if all(health_checks.values()) else "degraded"
        
        return {
            "status": overall_status,
            "checks": health_checks,
            "metrics": metrics
        }

# Global metrics collector instance
metrics = MetricsCollector()

class PerformanceTimer:
    """
    Context manager for timing operations.
    """
    
    def __init__(self, operation_name: str, record_metrics: bool = True):
        self.operation_name = operation_name
        self.record_metrics = record_metrics
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        
        if self.record_metrics:
            logger.info(
                "Operation completed",
                operation=self.operation_name,
                duration_ms=self.duration * 1000
            )
    
    def get_duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000 if self.duration else 0

def record_request_metrics(endpoint: str, method: str, status_code: int, duration: float):
    """
    Helper function to record request metrics.
    """
    metrics.record_request(endpoint, method, status_code, duration)

def record_analysis_metrics(duration: float, language: str = None, sentiment: str = None, risk_score: int = None):
    """
    Helper function to record analysis metrics.
    """
    metrics.record_processing_time(duration, language, sentiment, risk_score)
