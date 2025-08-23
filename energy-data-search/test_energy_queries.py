#!/usr/bin/env python
"""Comprehensive test suite for energy market document search."""

import sys
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from energy_data_search.query.search_engine import EnergyDataSearchEngine
from energy_data_search.config import Config

console = Console()


class EnergyQueryTester:
    """Test suite for energy market queries."""
    
    def __init__(self):
        """Initialize test suite with search engine."""
        self.config = Config()
        self.engine = EnergyDataSearchEngine(self.config)
        self.test_queries = self._get_test_queries()
        self.results = []
    
    def _get_test_queries(self) -> List[Dict[str, Any]]:
        """Define comprehensive test queries for energy market topics."""
        return [
            # BESS (Battery Energy Storage System) queries
            {
                "category": "BESS",
                "query": "battery energy storage system requirements and specifications",
                "expected_topics": ["battery", "storage", "BESS", "ESR", "capacity"]
            },
            {
                "category": "BESS",
                "query": "BESS market participation and bidding strategies",
                "expected_topics": ["BESS", "bidding", "market", "participation"]
            },
            {
                "category": "BESS",
                "query": "energy storage resource operational requirements",
                "expected_topics": ["ESR", "storage", "operational", "requirements"]
            },
            {
                "category": "BESS",
                "query": "battery storage ancillary services qualification",
                "expected_topics": ["battery", "ancillary", "services", "qualification"]
            },
            
            # EMS (Energy Management System) queries
            {
                "category": "EMS",
                "query": "energy management system integration requirements",
                "expected_topics": ["EMS", "management", "integration", "system"]
            },
            {
                "category": "EMS",
                "query": "EMS data exchange protocols and standards",
                "expected_topics": ["EMS", "data", "exchange", "protocols"]
            },
            {
                "category": "EMS",
                "query": "real-time energy management and optimization",
                "expected_topics": ["real-time", "management", "optimization"]
            },
            
            # Bidding queries
            {
                "category": "Bidding",
                "query": "day ahead market bidding procedures",
                "expected_topics": ["day ahead", "DAM", "bidding", "market"]
            },
            {
                "category": "Bidding",
                "query": "real time market bid submission requirements",
                "expected_topics": ["real time", "RTM", "bid", "submission"]
            },
            {
                "category": "Bidding",
                "query": "ancillary services bidding and offer curves",
                "expected_topics": ["ancillary", "bidding", "offer", "curves"]
            },
            {
                "category": "Bidding",
                "query": "energy offer curves and bid parameters",
                "expected_topics": ["energy", "offer", "curves", "parameters"]
            },
            
            # SCADA queries
            {
                "category": "SCADA",
                "query": "SCADA system requirements and telemetry",
                "expected_topics": ["SCADA", "telemetry", "requirements", "system"]
            },
            {
                "category": "SCADA",
                "query": "real time telemetry data submission",
                "expected_topics": ["telemetry", "real time", "data", "submission"]
            },
            {
                "category": "SCADA",
                "query": "SCADA integration and communication protocols",
                "expected_topics": ["SCADA", "integration", "communication", "protocols"]
            },
            
            # Real-Time Co-optimization queries
            {
                "category": "RTC",
                "query": "real time co-optimization implementation",
                "expected_topics": ["RTC", "co-optimization", "real time", "implementation"]
            },
            {
                "category": "RTC",
                "query": "co-optimization of energy and ancillary services",
                "expected_topics": ["co-optimization", "energy", "ancillary", "services"]
            },
            
            # Market operations queries
            {
                "category": "Market Operations",
                "query": "market clearing price calculation methodology",
                "expected_topics": ["market", "clearing", "price", "LMP", "MCP"]
            },
            {
                "category": "Market Operations",
                "query": "settlement and billing procedures",
                "expected_topics": ["settlement", "billing", "procedures", "payment"]
            },
            {
                "category": "Market Operations",
                "query": "congestion revenue rights and transmission",
                "expected_topics": ["congestion", "CRR", "transmission", "rights"]
            },
            
            # Compliance and regulations
            {
                "category": "Compliance",
                "query": "ERCOT nodal protocols compliance requirements",
                "expected_topics": ["ERCOT", "nodal", "protocols", "compliance"]
            },
            {
                "category": "Compliance",
                "query": "resource qualification and registration process",
                "expected_topics": ["resource", "qualification", "registration", "process"]
            }
        ]
    
    def run_query_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single query test."""
        query = test_case["query"]
        category = test_case["category"]
        expected = test_case["expected_topics"]
        
        try:
            # Run search
            results = self.engine.search(
                query=query,
                max_results=5,
                score_threshold=0.2
            )
            
            # Analyze results
            found_topics = []
            if results:
                # Check if expected topics appear in results
                combined_text = " ".join([r.content.lower() for r in results[:3]])
                found_topics = [topic for topic in expected 
                              if topic.lower() in combined_text]
            
            return {
                "category": category,
                "query": query,
                "num_results": len(results),
                "best_score": results[0].score if results else 0,
                "found_topics": found_topics,
                "expected_topics": expected,
                "success": len(found_topics) > 0 and len(results) > 0,
                "top_source": Path(results[0].source).name if results else "No results"
            }
            
        except Exception as e:
            return {
                "category": category,
                "query": query,
                "error": str(e),
                "success": False
            }
    
    def run_all_tests(self):
        """Run all test queries and display results."""
        console.print(Panel.fit(
            "[bold cyan]Energy Market Query Test Suite[/bold cyan]\n"
            f"Testing {len(self.test_queries)} queries across multiple categories",
            border_style="cyan"
        ))
        
        # Run tests
        for test_case in track(self.test_queries, description="Running queries..."):
            result = self.run_query_test(test_case)
            self.results.append(result)
        
        # Display results
        self._display_results()
        self._display_summary()
    
    def _display_results(self):
        """Display detailed test results."""
        # Group by category
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, cat_results in categories.items():
            console.print(f"\n[bold yellow]{category} Queries:[/bold yellow]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Query", style="cyan", width=50)
            table.add_column("Results", style="green", justify="center")
            table.add_column("Score", style="yellow", justify="center")
            table.add_column("Status", justify="center")
            
            for result in cat_results:
                if "error" in result:
                    status = "[red]ERROR[/red]"
                    score = "N/A"
                    num_results = "0"
                else:
                    status = "[green]✓ PASS[/green]" if result["success"] else "[red]✗ FAIL[/red]"
                    score = f"{result['best_score']:.3f}"
                    num_results = str(result['num_results'])
                
                table.add_row(
                    result["query"][:50],
                    num_results,
                    score,
                    status
                )
            
            console.print(table)
    
    def _display_summary(self):
        """Display test summary statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success", False))
        failed = total - passed
        
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            f"[bold]Test Summary[/bold]\n\n"
            f"Total Tests: {total}\n"
            f"[green]Passed: {passed}[/green]\n"
            f"[red]Failed: {failed}[/red]\n"
            f"Success Rate: {(passed/total)*100:.1f}%",
            border_style="cyan"
        ))
    
    def run_interactive_query(self):
        """Run an interactive query session."""
        console.print("\n[bold cyan]Interactive Query Mode[/bold cyan]")
        console.print("Enter your query (or 'exit' to quit):\n")
        
        while True:
            query = console.input("[cyan]Query> [/cyan]")
            if query.lower() in ['exit', 'quit']:
                break
            
            results = self.engine.search(query, max_results=3)
            
            if results:
                console.print(f"\n[green]Found {len(results)} results:[/green]")
                for i, result in enumerate(results, 1):
                    console.print(f"\n[bold]{i}. Score: {result.score:.3f}[/bold]")
                    console.print(f"   Source: {Path(result.source).name}")
                    console.print(f"   {result.content[:200]}...")
            else:
                console.print("[yellow]No results found[/yellow]")
            console.print()


def main():
    """Main test execution."""
    tester = EnergyQueryTester()
    
    # Run automated tests
    console.print("[bold]Running Automated Test Suite...[/bold]\n")
    tester.run_all_tests()
    
    # Offer interactive mode
    console.print("\n[bold]Would you like to try interactive queries?[/bold]")
    if console.input("Enter 'y' for yes: ").lower() == 'y':
        tester.run_interactive_query()


if __name__ == "__main__":
    main()