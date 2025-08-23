"""Full reindex command with progress tracking."""

import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

from ..config import Config
from ..query.incremental_indexer import IncrementalIndexer
from ..loaders.document_loader import DocumentLoader

console = Console()


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    return str(timedelta(seconds=int(seconds)))


def full_reindex(auto_confirm: bool = False):
    """Perform complete database reset and reindex with progress tracking."""
    
    start_time = time.time()
    config = Config()
    
    # Display warning
    if not auto_confirm:
        console.print(Panel.fit(
            "[bold red]⚠️  WARNING: Full Reindex Operation[/bold red]\n\n"
            "This will:\n"
            "• Delete the entire ChromaDB database\n"
            "• Remove all tracking metadata\n"
            "• Reindex ALL documents from scratch\n\n"
            "This may take several minutes depending on data size.",
            border_style="red"
        ))
        
        if not click.confirm("\nProceed with full reindex?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
    
    console.print("\n[bold cyan]Starting Full Reindex Operation[/bold cyan]\n")
    
    # Step 1: Clean existing database
    console.print("[bold]Step 1/4:[/bold] Cleaning existing database...")
    chroma_dir = config.chroma_persist_dir
    tracker_file = chroma_dir / "index_tracker.json"
    
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            console.print("  ✓ ChromaDB database deleted")
        except Exception as e:
            console.print(f"  [red]✗ Error deleting database: {e}[/red]")
            return
    else:
        console.print("  ✓ No existing database found")
    
    # Step 2: Count files to index
    console.print("\n[bold]Step 2/4:[/bold] Scanning for documents...")
    
    loader = DocumentLoader()
    all_files = []
    total_size = 0
    file_types = {}
    
    try:
        directories = config.get_subdirectories()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            scan_task = progress.add_task("Scanning directories...", total=len(directories))
            
            for directory in directories:
                for file_path in directory.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in loader.loader_map:
                        all_files.append(file_path)
                        total_size += file_path.stat().st_size
                        ext = file_path.suffix.lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                
                progress.update(scan_task, advance=1)
        
        console.print(f"  ✓ Found {len(all_files)} documents to index")
        console.print(f"  ✓ Total size: {total_size / (1024*1024):.2f} MB")
        
        # Show file type breakdown
        type_table = Table(title="Document Types", show_header=True)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green", justify="right")
        for ext, count in sorted(file_types.items()):
            type_table.add_row(ext, str(count))
        console.print(type_table)
        
    except Exception as e:
        console.print(f"[red]Error scanning directories: {e}[/red]")
        return
    
    if not all_files:
        console.print("[yellow]No documents found to index[/yellow]")
        return
    
    # Step 3: Initialize indexer
    console.print("\n[bold]Step 3/4:[/bold] Initializing indexer...")
    incremental = IncrementalIndexer(config)
    console.print("  ✓ ChromaDB initialized")
    console.print("  ✓ Index tracker initialized")
    
    # Step 4: Index all documents with detailed progress
    console.print(f"\n[bold]Step 4/4:[/bold] Indexing {len(all_files)} documents...")
    
    total_chunks = 0
    errors = []
    files_indexed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True
    ) as progress:
        
        index_task = progress.add_task(
            "[cyan]Indexing documents...", 
            total=len(all_files)
        )
        
        batch_size = 10  # Process files in batches
        batch_docs = []
        
        for i, file_path in enumerate(all_files):
            try:
                # Update progress description
                progress.update(
                    index_task, 
                    description=f"[cyan]Processing: {file_path.name[:50]}..."
                )
                
                # Load document
                documents = incremental.loader.load_document(file_path)
                
                if documents:
                    batch_docs.extend(documents)
                    incremental.tracker.mark_indexed(file_path, len(documents))
                    total_chunks += len(documents)
                    files_indexed += 1
                    
                    # Add to index in batches
                    if len(batch_docs) >= 50:
                        incremental.indexer.add_documents(batch_docs, batch_size=50)
                        batch_docs = []
                
            except Exception as e:
                errors.append({
                    'file': str(file_path),
                    'error': str(e)
                })
            
            progress.update(index_task, advance=1)
        
        # Index remaining documents
        if batch_docs:
            incremental.indexer.add_documents(batch_docs, batch_size=50)
        
        # Save tracker
        incremental.tracker.save_tracker()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Display results
    console.print("\n" + "="*60 + "\n")
    
    results_panel = Panel.fit(
        f"[bold green]✓ Full Reindex Complete![/bold green]\n\n"
        f"[cyan]Files Processed:[/cyan] {len(all_files)}\n"
        f"[cyan]Files Indexed:[/cyan] {files_indexed}\n"
        f"[cyan]Total Chunks:[/cyan] {total_chunks}\n"
        f"[cyan]Errors:[/cyan] {len(errors)}\n"
        f"[cyan]Processing Time:[/cyan] {format_time(elapsed_time)}\n"
        f"[cyan]Average Speed:[/cyan] {len(all_files) / elapsed_time:.1f} files/sec\n"
        f"[cyan]Chunks/sec:[/cyan] {total_chunks / elapsed_time:.1f}",
        title="Reindex Results",
        border_style="green"
    )
    console.print(results_panel)
    
    # Show errors if any
    if errors:
        console.print("\n[bold red]Errors encountered:[/bold red]")
        for err in errors[:5]:
            console.print(f"  • {Path(err['file']).name}: {err['error']}")
        if len(errors) > 5:
            console.print(f"  ... and {len(errors) - 5} more errors")
    
    # Show final statistics
    console.print("\n[bold]Database Statistics:[/bold]")
    stats = incremental.check_status()
    
    stats_table = Table(show_header=False)
    stats_table.add_column("Property", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Total Files Tracked", str(stats['tracker']['total_files']))
    stats_table.add_row("Total Chunks in DB", str(stats['tracker']['total_chunks']))
    stats_table.add_row("Database Size", f"{stats['tracker']['total_size_mb']:.2f} MB")
    stats_table.add_row("Collection Name", str(stats['index']['collection_name']))
    
    console.print(stats_table)
    
    console.print(f"\n[dim]Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")