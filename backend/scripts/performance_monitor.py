#!/usr/bin/env python3
"""
Performance monitoring script for TaxPoynt eInvoice API.

This script establishes performance baselines for the current Uvicorn setup
and provides metrics for comparison when evaluating Hypercorn migration.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import sys


class PerformanceMonitor:
    """Performance monitoring and benchmarking tool."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results = []
    
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """Test a single endpoint and measure performance."""
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "response_time": response_time,
                        "content_length": len(content),
                        "success": 200 <= response.status < 300
                    }
            elif method == "POST":
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "response_time": response_time,
                        "content_length": len(content),
                        "success": 200 <= response.status < 300
                    }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "response_time": response_time,
                "content_length": 0,
                "success": False,
                "error": str(e)
            }
    
    async def run_load_test(self, endpoint: str, concurrent_requests: int = 10, total_requests: int = 100) -> List[Dict[str, Any]]:
        """Run load test on a specific endpoint."""
        print(f"🔄 Running load test: {endpoint} ({concurrent_requests} concurrent, {total_requests} total)")
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for i in range(total_requests):
                task = self.test_endpoint(session, endpoint)
                tasks.append(task)
                
                # Batch requests to avoid overwhelming the server
                if len(tasks) >= concurrent_requests:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    self.results.extend([r for r in batch_results if isinstance(r, dict)])
                    tasks = []
                    
                    # Small delay between batches
                    await asyncio.sleep(0.1)
            
            # Process remaining tasks
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                self.results.extend([r for r in batch_results if isinstance(r, dict)])
        
        return self.results
    
    async def health_check_benchmark(self) -> Dict[str, Any]:
        """Benchmark health check endpoints specifically."""
        print("🏥 Benchmarking health check endpoints...")
        
        health_endpoints = [
            "/api/v1/health/ready",
            "/api/v1/health/health", 
            "/api/v1/health/live",
            "/api/v1/health/startup"
        ]
        
        connector = aiohttp.TCPConnector(limit=5)
        timeout = aiohttp.ClientTimeout(total=10)
        
        health_results = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for endpoint in health_endpoints:
                # Test each health endpoint 20 times
                tasks = [self.test_endpoint(session, endpoint) for _ in range(20)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                endpoint_results = [r for r in results if isinstance(r, dict)]
                health_results.extend(endpoint_results)
        
        return self.analyze_results(health_results, "Health Check")
    
    async def api_endpoints_benchmark(self) -> Dict[str, Any]:
        """Benchmark core API endpoints."""
        print("🚀 Benchmarking core API endpoints...")
        
        # Test public/accessible endpoints
        api_endpoints = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/debug/enums"
        ]
        
        connector = aiohttp.TCPConnector(limit=5)
        timeout = aiohttp.ClientTimeout(total=15)
        
        api_results = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for endpoint in api_endpoints:
                # Test each endpoint 10 times
                tasks = [self.test_endpoint(session, endpoint) for _ in range(10)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                endpoint_results = [r for r in results if isinstance(r, dict)]
                api_results.extend(endpoint_results)
        
        return self.analyze_results(api_results, "API Endpoints")
    
    def analyze_results(self, results: List[Dict[str, Any]], test_name: str) -> Dict[str, Any]:
        """Analyze performance test results."""
        if not results:
            return {"test_name": test_name, "error": "No results to analyze"}
        
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        if not successful_results:
            return {
                "test_name": test_name,
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_results),
                "success_rate": 0.0,
                "error": "All requests failed"
            }
        
        response_times = [r["response_time"] for r in successful_results]
        content_lengths = [r["content_length"] for r in successful_results]
        
        analysis = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / len(results) * 100,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0],
                "p99": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 1 else response_times[0]
            },
            "content_sizes": {
                "min": min(content_lengths),
                "max": max(content_lengths),
                "mean": statistics.mean(content_lengths)
            }
        }
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print formatted analysis results."""
        print(f"\n📊 {analysis['test_name']} Performance Analysis")
        print("=" * 60)
        print(f"Total Requests: {analysis['total_requests']}")
        print(f"Successful: {analysis['successful_requests']}")
        print(f"Failed: {analysis['failed_requests']}")
        print(f"Success Rate: {analysis['success_rate']:.2f}%")
        
        if "response_times" in analysis:
            rt = analysis["response_times"]
            print(f"\nResponse Times (seconds):")
            print(f"  Min: {rt['min']:.4f}s")
            print(f"  Max: {rt['max']:.4f}s")
            print(f"  Mean: {rt['mean']:.4f}s")
            print(f"  Median: {rt['median']:.4f}s")
            print(f"  95th percentile: {rt['p95']:.4f}s")
            print(f"  99th percentile: {rt['p99']:.4f}s")
            print(f"  Std Dev: {rt['std_dev']:.4f}s")
        
        if "content_sizes" in analysis:
            cs = analysis["content_sizes"]
            print(f"\nContent Sizes (bytes):")
            print(f"  Min: {cs['min']}")
            print(f"  Max: {cs['max']}")
            print(f"  Mean: {cs['mean']:.0f}")
    
    def save_baseline(self, analyses: List[Dict[str, Any]], filename: str = None):
        """Save performance baseline to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_baseline_{timestamp}.json"
        
        baseline_data = {
            "timestamp": datetime.now().isoformat(),
            "server": "uvicorn",
            "configuration": {
                "host": "0.0.0.0",
                "workers": 1,
                "timeout_keep_alive": 65,
                "loop": "uvloop",
                "http": "httptools"
            },
            "test_results": analyses
        }
        
        with open(filename, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"💾 Performance baseline saved to: {filename}")


async def main():
    """Main performance monitoring function."""
    parser = argparse.ArgumentParser(description="TaxPoynt Performance Monitor")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    parser.add_argument("--load-test", help="Run load test on specific endpoint")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests for load test")
    parser.add_argument("--total", type=int, default=100, help="Total requests for load test")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.url)
    
    print("🎯 TaxPoynt Performance Monitoring - Uvicorn Baseline")
    print("=" * 60)
    
    analyses = []
    
    try:
        # Health check benchmark
        health_analysis = await monitor.health_check_benchmark()
        monitor.print_analysis(health_analysis)
        analyses.append(health_analysis)
        
        # API endpoints benchmark
        api_analysis = await monitor.api_endpoints_benchmark()
        monitor.print_analysis(api_analysis)
        analyses.append(api_analysis)
        
        # Custom load test if specified
        if args.load_test:
            print(f"\n🔄 Custom Load Test: {args.load_test}")
            print("-" * 40)
            await monitor.run_load_test(args.load_test, args.concurrent, args.total)
            load_analysis = monitor.analyze_results(monitor.results, f"Load Test: {args.load_test}")
            monitor.print_analysis(load_analysis)
            analyses.append(load_analysis)
        
        # Save results if requested
        if args.save:
            monitor.save_baseline(analyses)
        
        print("\n✅ Performance monitoring completed!")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())