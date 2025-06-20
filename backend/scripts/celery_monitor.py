#!/usr/bin/env python3
"""
Celery monitoring and management script.

This script provides commands to monitor and manage Celery workers and tasks.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.celery import get_queue_health, get_worker_health
from app.core.worker_config import create_worker_manager


def show_queue_status():
    """Show current queue status."""
    print("=== Queue Status ===")
    try:
        health = get_queue_health()
        print(f"Overall Status: {health['status']}")
        print(f"Total Pending Tasks: {health['total_pending']}")
        print()
        
        if health['queues']:
            print("Queue Details:")
            for queue_name, queue_info in health['queues'].items():
                status_indicator = "✓" if queue_info['status'] == 'healthy' else "⚠"
                print(f"  {status_indicator} {queue_name}: {queue_info['length']} pending ({queue_info['status']})")
        else:
            print("No queue information available")
            
    except Exception as e:
        print(f"Error getting queue status: {e}")
    
    print()


def show_worker_status():
    """Show current worker status."""
    print("=== Worker Status ===")
    try:
        health = get_worker_health()
        print(f"Overall Status: {health['status']}")
        print(f"Active Workers: {health['active_workers']}")
        print()
        
        if health['available_queues']:
            print("Available Queues:")
            for queue in health['available_queues']:
                print(f"  - {queue}")
        else:
            print("No workers or queues available")
            
    except Exception as e:
        print(f"Error getting worker status: {e}")
    
    print()


def show_worker_config():
    """Show worker configuration."""
    print("=== Worker Configuration ===")
    try:
        worker_manager = create_worker_manager()
        config = worker_manager.get_monitoring_info()
        
        print(f"Environment: {config['environment']}")
        print(f"Total Workers: {config['total_workers']}")
        print()
        
        for worker_name, worker_info in config['workers'].items():
            print(f"Worker: {worker_name}")
            print(f"  Queues: {', '.join(worker_info['queues'])}")
            print(f"  Concurrency: {worker_info['concurrency']}")
            print(f"  Pool Type: {worker_info['pool_type']}")
            if worker_info['autoscale']:
                print(f"  Autoscale: {worker_info['autoscale'][1]}-{worker_info['autoscale'][0]}")
            print(f"  Time Limits: Hard {worker_info['time_limits']['hard']}s, Soft {worker_info['time_limits']['soft']}s")
            print()
            
    except Exception as e:
        print(f"Error getting worker configuration: {e}")


def show_system_status():
    """Show complete system status."""
    print("TaxPoynt eInvoice - Celery System Status")
    print("=" * 50)
    show_queue_status()
    show_worker_status()
    show_worker_config()


def purge_queue(queue_name: str):
    """Purge all messages from a queue."""
    print(f"Purging queue: {queue_name}")
    try:
        # Use Celery command to purge queue
        cmd = [
            "celery", "purge",
            "--app=app.core.celery:celery_app",
            "--force",
            "--queues", queue_name
        ]
        
        result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully purged queue: {queue_name}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Error purging queue: {result.stderr}")
            
    except Exception as e:
        print(f"Error purging queue {queue_name}: {e}")


def inspect_workers():
    """Inspect active workers."""
    print("=== Worker Inspection ===")
    try:
        # Use Celery inspect command
        cmd = [
            "celery", "inspect",
            "--app=app.core.celery:celery_app",
            "active"
        ]
        
        result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("Active tasks:")
                print(result.stdout)
            else:
                print("No active tasks found")
        else:
            print(f"Error inspecting workers: {result.stderr}")
            
    except Exception as e:
        print(f"Error inspecting workers: {e}")


def show_task_stats():
    """Show task statistics."""
    print("=== Task Statistics ===")
    try:
        # Use Celery inspect command for stats
        cmd = [
            "celery", "inspect",
            "--app=app.core.celery:celery_app",
            "stats"
        ]
        
        result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    # Try to parse JSON output
                    stats = json.loads(result.stdout)
                    for worker, worker_stats in stats.items():
                        print(f"Worker: {worker}")
                        if 'total' in worker_stats:
                            total_stats = worker_stats['total']
                            for key, value in total_stats.items():
                                print(f"  {key}: {value}")
                        print()
                except json.JSONDecodeError:
                    print(result.stdout)
            else:
                print("No statistics available")
        else:
            print(f"Error getting task statistics: {result.stderr}")
            
    except Exception as e:
        print(f"Error getting task statistics: {e}")


def flower_monitor():
    """Start Flower monitoring interface."""
    print("Starting Flower monitoring interface...")
    try:
        cmd = [
            "celery", "flower",
            "--app=app.core.celery:celery_app",
            "--port=5555",
            "--broker_api=http://localhost:15672/api/"
        ]
        
        print("Flower will be available at: http://localhost:5555")
        print("Press Ctrl+C to stop...")
        
        subprocess.run(cmd, cwd=backend_dir)
        
    except KeyboardInterrupt:
        print("\nFlower monitoring stopped")
    except Exception as e:
        print(f"Error starting Flower: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor and manage Celery workers")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show complete system status")
    subparsers.add_parser("queues", help="Show queue status")
    subparsers.add_parser("workers", help="Show worker status")
    subparsers.add_parser("config", help="Show worker configuration")
    
    # Management commands
    purge_parser = subparsers.add_parser("purge", help="Purge a queue")
    purge_parser.add_argument("queue_name", help="Name of queue to purge")
    
    subparsers.add_parser("inspect", help="Inspect active workers")
    subparsers.add_parser("stats", help="Show task statistics")
    subparsers.add_parser("flower", help="Start Flower monitoring interface")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "status":
        show_system_status()
    elif args.command == "queues":
        show_queue_status()
    elif args.command == "workers":
        show_worker_status()
    elif args.command == "config":
        show_worker_config()
    elif args.command == "purge":
        purge_queue(args.queue_name)
    elif args.command == "inspect":
        inspect_workers()
    elif args.command == "stats":
        show_task_stats()
    elif args.command == "flower":
        flower_monitor()
    else:
        print(f"Unknown command: {args.command}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())