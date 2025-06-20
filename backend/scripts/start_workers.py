#!/usr/bin/env python3
"""
Script to start Celery workers based on environment configuration.

This script provides an easy way to start all configured Celery workers
for the TaxPoynt eInvoice application.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.worker_config import create_worker_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def start_workers():
    """Start all configured Celery workers."""
    try:
        # Create worker manager for current environment
        worker_manager = create_worker_manager()
        
        logger.info(f"Starting workers for environment: {worker_manager.environment}")
        logger.info(f"Total workers to start: {len(worker_manager.worker_configs)}")
        
        # Get all worker commands
        worker_commands = worker_manager.get_all_worker_commands()
        
        processes = []
        
        for worker_name, command in worker_commands.items():
            try:
                logger.info(f"Starting worker: {worker_name}")
                logger.debug(f"Command: {' '.join(command)}")
                
                # Start the worker process
                process = subprocess.Popen(
                    command,
                    cwd=backend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                processes.append((worker_name, process))
                logger.info(f"Worker {worker_name} started with PID: {process.pid}")
                
            except Exception as e:
                logger.error(f"Failed to start worker {worker_name}: {str(e)}")
        
        if not processes:
            logger.error("No workers were started successfully")
            return 1
        
        logger.info(f"Started {len(processes)} workers successfully")
        
        # Monitor processes
        try:
            while True:
                for worker_name, process in processes:
                    if process.poll() is not None:
                        # Process has terminated
                        stdout, stderr = process.communicate()
                        if stdout:
                            logger.info(f"Worker {worker_name} stdout: {stdout}")
                        if stderr:
                            logger.error(f"Worker {worker_name} stderr: {stderr}")
                        logger.error(f"Worker {worker_name} terminated with code: {process.returncode}")
                        return process.returncode
                
                # Check every 5 seconds
                import time
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Shutting down workers...")
            for worker_name, process in processes:
                try:
                    process.terminate()
                    process.wait(timeout=10)
                    logger.info(f"Worker {worker_name} terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing worker {worker_name}")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error stopping worker {worker_name}: {str(e)}")
            
            return 0
    
    except Exception as e:
        logger.error(f"Error starting workers: {str(e)}")
        return 1


def start_single_worker(worker_name: str):
    """Start a single worker by name."""
    try:
        worker_manager = create_worker_manager()
        
        if worker_name not in worker_manager.worker_configs:
            logger.error(f"Worker '{worker_name}' not found in configuration")
            logger.info(f"Available workers: {list(worker_manager.worker_configs.keys())}")
            return 1
        
        command = worker_manager.get_worker_command(worker_name)
        
        logger.info(f"Starting single worker: {worker_name}")
        logger.debug(f"Command: {' '.join(command)}")
        
        # Execute the command directly (foreground)
        result = subprocess.run(
            command,
            cwd=backend_dir,
            check=False
        )
        
        return result.returncode
        
    except Exception as e:
        logger.error(f"Error starting worker {worker_name}: {str(e)}")
        return 1


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Celery workers for TaxPoynt eInvoice")
    parser.add_argument(
        "--worker",
        type=str,
        help="Start a specific worker by name"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available worker configurations"
    )
    parser.add_argument(
        "--environment",
        type=str,
        help="Override environment (development, staging, production)"
    )
    
    args = parser.parse_args()
    
    # Override environment if specified
    if args.environment:
        os.environ["APP_ENV"] = args.environment
    
    if args.list:
        # List available workers
        worker_manager = create_worker_manager()
        print(f"Environment: {worker_manager.environment}")
        print(f"Available workers:")
        for name, config in worker_manager.worker_configs.items():
            print(f"  {name}:")
            print(f"    Queues: {', '.join(config.queues)}")
            print(f"    Concurrency: {config.concurrency}")
            print(f"    Pool: {config.pool_type}")
            if config.autoscale:
                print(f"    Autoscale: {config.autoscale[1]}-{config.autoscale[0]} workers")
            print()
        return 0
    
    if args.worker:
        # Start single worker
        return start_single_worker(args.worker)
    else:
        # Start all workers
        return start_workers()


if __name__ == "__main__":
    sys.exit(main())