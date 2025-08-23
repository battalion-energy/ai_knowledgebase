"""Command-line interface for Energy Data Search."""

import logging
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from ..config import Config
from ..query.search_engine import EnergyDataSearchEngine
from ..query.incremental_indexer import IncrementalIndexer
from .reindex import full_reindex

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Energy Data Search - Query energy market documents with AI."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config()
    # Don't create engine here - let commands create it when needed
    ctx.obj['engine'] = None


@cli.command()
@click.option('--directory', '-d', type=click.Path(exists=True), help='Specific directory to index')
@click.option('--recursive/--no-recursive', default=True, help='Index subdirectories recursively')
@click.option('--clear', is_flag=True, help='Clear existing index before indexing')
@click.pass_context
def index(ctx, directory, recursive, clear):
    """Index documents from source directories."""
    if ctx.obj['engine'] is None:
        ctx.obj['engine'] = EnergyDataSearchEngine(ctx.obj['config'])
    engine = ctx.obj['engine']
    
    if clear:
        console.print("[yellow]Clearing existing index...[/yellow]")
        engine.clear_index()
        console.print("[green]Index cleared![/green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        if directory:
            task = progress.add_task(f"Indexing {directory}...", total=None)
            count = engine.index_directory(Path(directory), recursive=recursive)
            progress.update(task, completed=True)
            console.print(f"[green]Indexed {count} document chunks from {directory}[/green]")
        else:
            task = progress.add_task("Indexing all source directories...", total=None)
            results = engine.index_all_sources()
            progress.update(task, completed=True)
            
            table = Table(title="Indexing Results")
            table.add_column("Directory", style="cyan")
            table.add_column("Documents", style="green")
            
            total = 0
            for dir_path, count in results.items():
                table.add_row(Path(dir_path).name, str(count))
                total += count
            
            console.print(table)
            console.print(f"[bold green]Total: {total} document chunks indexed[/bold green]")


@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', default=10, help='Maximum number of results')
@click.option('--directory', '-d', help='Filter by source directory name')
@click.option('--file-type', '-t', help='Filter by file type (pdf, txt, csv, etc.)')
@click.option('--threshold', '-s', type=float, help='Minimum similarity score threshold')
@click.option('--verbose', '-v', is_flag=True, help='Show full content')
@click.pass_context
def search(ctx, query, max_results, directory, file_type, threshold, verbose):
    """Search for documents matching a query."""
    if ctx.obj['engine'] is None:
        ctx.obj['engine'] = EnergyDataSearchEngine(ctx.obj['config'])
    engine = ctx.obj['engine']
    
    with console.status("[bold green]Searching..."):
        results = engine.search(
            query=query,
            max_results=max_results,
            filter_directory=directory,
            filter_file_type=file_type,
            score_threshold=threshold
        )
    
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    console.print(f"\n[bold green]Found {len(results)} results for:[/bold green] {query}\n")
    
    for i, result in enumerate(results, 1):
        title = f"Result {i} | Score: {result.score:.3f} | {Path(result.source).name}"
        
        content = result.content if verbose else result.content[:500] + "..."
        
        panel_content = f"[cyan]Source:[/cyan] {result.source}\n"
        panel_content += f"[cyan]Type:[/cyan] {result.metadata.get('file_type', 'unknown')}\n"
        panel_content += f"[cyan]Directory:[/cyan] {result.metadata.get('directory', 'unknown')}\n\n"
        panel_content += f"[white]{content}[/white]"
        
        console.print(Panel(panel_content, title=title, expand=False))
        console.print()


@cli.command()
@click.pass_context
def stats(ctx):
    """Show statistics about the indexed documents."""
    if ctx.obj['engine'] is None:
        ctx.obj['engine'] = EnergyDataSearchEngine(ctx.obj['config'])
    engine = ctx.obj['engine']
    stats = engine.get_stats()
    
    table = Table(title="Index Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear the index?')
@click.pass_context
def clear(ctx):
    """Clear all indexed documents."""
    if ctx.obj['engine'] is None:
        ctx.obj['engine'] = EnergyDataSearchEngine(ctx.obj['config'])
    engine = ctx.obj['engine']
    engine.clear_index()
    console.print("[green]Index cleared successfully![/green]")


@cli.command()
@click.option('--directory', '-d', type=click.Path(exists=True), help='Specific directory to check')
@click.option('--auto/--no-auto', default=False, help='Automatically index new files')
@click.pass_context
def update(ctx, directory, auto):
    """Index only new or modified documents (incremental update)."""
    incremental = IncrementalIndexer(ctx.obj['config'])
    
    # Check status first
    status = incremental.check_status()
    
    console.print(Panel.fit(
        f"[bold cyan]Incremental Index Update[/bold cyan]\n"
        f"Tracked files: {status['tracker']['total_files']}\n"
        f"New files available: {status['new_files_available']}\n"
        f"Last update: {status['last_update'] or 'Never'}",
        border_style="cyan"
    ))
    
    if status['new_files_available'] == 0:
        console.print("[yellow]No new files to index[/yellow]")
        return
    
    if not auto:
        console.print(f"\n[bold]Found {status['new_files_available']} new/modified files[/bold]")
        if not click.confirm("Proceed with indexing?"):
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Indexing new documents...", total=None)
        results = incremental.index_new_documents(directory=directory)
        progress.update(task, completed=True)
    
    # Display results
    if results['new_files']:
        console.print(f"\n[green]New files indexed: {len(results['new_files'])}[/green]")
        for f in results['new_files'][:5]:
            console.print(f"  + {Path(f).name}")
        if len(results['new_files']) > 5:
            console.print(f"  ... and {len(results['new_files']) - 5} more")
    
    if results['modified_files']:
        console.print(f"\n[yellow]Modified files reindexed: {len(results['modified_files'])}[/yellow]")
        for f in results['modified_files'][:5]:
            console.print(f"  ~ {Path(f).name}")
    
    if results['removed_files']:
        console.print(f"\n[red]Removed files: {len(results['removed_files'])}[/red]")
        for f in results['removed_files'][:5]:
            console.print(f"  - {Path(f).name}")
    
    if results['errors']:
        console.print(f"\n[red]Errors: {len(results['errors'])}[/red]")
        for err in results['errors'][:3]:
            console.print(f"  ! {Path(err['file']).name}: {err['error']}")
    
    console.print(f"\n[bold green]Update complete![/bold green]")
    console.print(f"Total chunks added: {results['total_chunks_added']}")
    console.print(f"Processing time: {results['processing_time']:.2f} seconds")


@cli.command()
@click.pass_context
def status(ctx):
    """Show detailed indexing status and tracking information."""
    incremental = IncrementalIndexer(ctx.obj['config'])
    status = incremental.check_status()
    
    # Tracker statistics table
    table = Table(title="Index Tracker Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Tracked Files", str(status['tracker']['total_files']))
    table.add_row("Total Chunks", str(status['tracker']['total_chunks']))
    table.add_row("Total Size", f"{status['tracker']['total_size_mb']} MB")
    table.add_row("New Files Available", str(status['new_files_available']))
    table.add_row("Last Update", status['last_update'] or "Never")
    table.add_row("Tracker File", status['tracker']['tracker_file'])
    
    console.print(table)
    
    # File type breakdown
    if status['tracker']['file_types']:
        type_table = Table(title="File Types Indexed")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green")
        
        for ext, count in status['tracker']['file_types'].items():
            type_table.add_row(ext or "no extension", str(count))
        
        console.print(type_table)
    
    # ChromaDB statistics
    index_table = Table(title="ChromaDB Index Statistics")
    index_table.add_column("Property", style="cyan")
    index_table.add_column("Value", style="green")
    
    for key, value in status['index'].items():
        index_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(index_table)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def reindex(ctx, file_path):
    """Force reindex a specific file."""
    incremental = IncrementalIndexer(ctx.obj['config'])
    file_path = Path(file_path)
    
    console.print(f"[yellow]Force reindexing: {file_path}[/yellow]")
    
    with console.status("[bold green]Reindexing..."):
        results = incremental.force_reindex_file(file_path)
    
    if results['success']:
        console.print(f"[green]Successfully reindexed![/green]")
        console.print(f"Chunks added: {results['chunks_added']}")
    else:
        console.print(f"[red]Reindexing failed: {results['error']}[/red]")


@cli.command()
@click.confirmation_option(prompt='This will reset tracking. All files will be considered new. Continue?')
@click.pass_context
def reset_tracker(ctx):
    """Reset the index tracker (marks all files as unindexed)."""
    incremental = IncrementalIndexer(ctx.obj['config'])
    incremental.reset_tracker()
    console.print("[green]Tracker reset successfully![/green]")
    console.print("All files will be considered new on next update.")


@cli.command()
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def full_reindex(ctx, yes):
    """Delete database and perform complete reindex with progress tracking."""
    from .reindex import full_reindex as do_reindex
    do_reindex(auto_confirm=yes)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive query mode."""
    if ctx.obj['engine'] is None:
        ctx.obj['engine'] = EnergyDataSearchEngine(ctx.obj['config'])
    engine = ctx.obj['engine']
    
    console.print(Panel.fit(
        "[bold cyan]Energy Data Search - Interactive Mode[/bold cyan]\n"
        "Type your questions about energy markets, ISO rules, tariffs, etc.\n"
        "Type 'exit' or 'quit' to leave.",
        border_style="cyan"
    ))
    
    while True:
        try:
            query = console.input("\n[bold cyan]Query>[/bold cyan] ")
            
            if query.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if not query.strip():
                continue
            
            with console.status("[bold green]Searching..."):
                results = engine.search(query, max_results=5)
            
            if not results:
                console.print("[yellow]No results found. Try a different query.[/yellow]")
                continue
            
            console.print(f"\n[bold green]Top {len(results)} results:[/bold green]\n")
            
            for i, result in enumerate(results, 1):
                console.print(f"[bold]{i}. Score: {result.score:.3f}[/bold]")
                console.print(f"   Source: {Path(result.source).name}")
                console.print(f"   {result.content[:200]}...")
                console.print()
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()