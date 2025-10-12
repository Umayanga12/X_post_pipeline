#!/usr/bin/env python3
"""
Monitoring and health check script for Crypto News Pipe
Provides HTTP endpoints for health checks and basic metrics
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Dict, Any
import psutil
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health monitoring and metrics collection"""

    def __init__(self):
        self.start_time = time.time()
        self.posted_file = os.getenv("POSTED_FILE", "posted.json")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def check_ollama_health(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "models": [m.get("name", "unknown") for m in models],
                    "model_count": len(models),
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            metrics = {
                "uptime_seconds": time.time() - self.start_time,
                "posted_articles_count": 0,
                "last_post_time": None,
            }

            # Check posted articles
            if os.path.exists(self.posted_file):
                try:
                    with open(self.posted_file, "r") as f:
                        posted_data = json.load(f)

                    if isinstance(posted_data, list):
                        metrics["posted_articles_count"] = len(posted_data)
                        if posted_data:
                            # Assuming the data has timestamps
                            metrics["last_post_time"] = posted_data[-1].get(
                                "timestamp", "unknown"
                            )
                    elif isinstance(posted_data, dict):
                        metrics["posted_articles_count"] = len(posted_data)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {self.posted_file}")
                except Exception as e:
                    logger.error(f"Error reading {self.posted_file}: {e}")

            return metrics

        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {"error": str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        ollama_health = self.check_ollama_health()
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()

        # Determine overall health
        is_healthy = (
            ollama_health.get("status") == "healthy"
            and system_metrics.get("memory", {}).get("percent", 100) < 90
            and system_metrics.get("disk", {}).get("percent", 100) < 90
        )

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "ollama": ollama_health,
                "application": {"status": "running", "metrics": app_metrics},
            },
            "system": system_metrics,
        }


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks"""

    def __init__(self, *args, monitor=None, **kwargs):
        self.monitor = monitor or HealthMonitor()
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/ready":
            self._handle_ready()
        elif self.path == "/":
            self._handle_root()
        else:
            self._send_response(404, {"error": "Not found"})

    def _handle_health(self):
        """Handle health check endpoint"""
        try:
            health_data = self.monitor.get_health_status()
            status_code = 200 if health_data["status"] == "healthy" else 503
            self._send_response(status_code, health_data)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self._send_response(500, {"error": "Internal server error"})

    def _handle_metrics(self):
        """Handle metrics endpoint"""
        try:
            metrics = {
                "system": self.monitor.get_system_metrics(),
                "application": self.monitor.get_application_metrics(),
                "ollama": self.monitor.check_ollama_health(),
            }
            self._send_response(200, metrics)
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            self._send_response(500, {"error": "Internal server error"})

    def _handle_ready(self):
        """Handle readiness check endpoint"""
        try:
            ollama_health = self.monitor.check_ollama_health()
            is_ready = ollama_health.get("status") == "healthy"

            response = {
                "ready": is_ready,
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {"ollama": ollama_health},
            }

            status_code = 200 if is_ready else 503
            self._send_response(status_code, response)
        except Exception as e:
            logger.error(f"Readiness check error: {e}")
            self._send_response(500, {"error": "Internal server error"})

    def _handle_root(self):
        """Handle root endpoint with basic info"""
        info = {
            "service": "Crypto News Pipe Monitor",
            "version": "1.0.0",
            "endpoints": {
                "/health": "Health check with detailed status",
                "/metrics": "System and application metrics",
                "/ready": "Readiness check for dependencies",
                "/": "This information page",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._send_response(200, info)

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        response_data = json.dumps(data, indent=2, default=str)
        self.wfile.write(response_data.encode("utf-8"))


def create_handler(monitor):
    """Create handler class with monitor instance"""

    def handler(*args, **kwargs):
        return HealthHandler(*args, monitor=monitor, **kwargs)

    return handler


def start_monitor_server(host="0.0.0.0", port=8000):
    """Start the monitoring HTTP server"""
    monitor = HealthMonitor()
    handler_class = create_handler(monitor)

    try:
        server = HTTPServer((host, port), handler_class)
        logger.info(f"Starting health monitor server on {host}:{port}")
        logger.info("Available endpoints:")
        logger.info(f"  http://{host}:{port}/health - Health check")
        logger.info(f"  http://{host}:{port}/metrics - Metrics")
        logger.info(f"  http://{host}:{port}/ready - Readiness check")

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Shutting down monitor server...")
        server.shutdown()
    except Exception as e:
        logger.error(f"Monitor server error: {e}")
        raise


def run_health_check():
    """Run a one-time health check and exit"""
    monitor = HealthMonitor()
    health_data = monitor.get_health_status()

    print(json.dumps(health_data, indent=2, default=str))

    # Exit with appropriate code
    exit_code = 0 if health_data["status"] == "healthy" else 1
    exit(exit_code)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        run_health_check()
    else:
        # Start monitoring server in background thread if imported
        # or run directly if executed as script
        port = int(os.getenv("MONITOR_PORT", 8000))
        host = os.getenv("MONITOR_HOST", "0.0.0.0")
        start_monitor_server(host, port)
