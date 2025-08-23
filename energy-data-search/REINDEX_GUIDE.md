# Full Reindex Guide

## Quick Commands

### Complete Reset and Reindex (Recommended)
```bash
make full-reindex
```
This command will:
- ⚠️ Show a warning and ask for confirmation
- 🗑️ Delete the entire ChromaDB database
- 📊 Scan and count all documents
- 📈 Show progress bar with time estimates
- 🔄 Index all documents with chunk tracking
- ✅ Display complete statistics and timing

### Automated Full Reindex (No Confirmation)
```bash
make full-reindex-yes
```
Same as above but skips the confirmation prompt (useful for scripts).

### Manual Database Cleanup
```bash
make clean-db        # Delete database only
make reset-tracker   # Reset tracking only
make index          # Rebuild index
```

## What Happens During Full Reindex

1. **Database Cleanup**
   - Removes `/data/chroma_db` directory completely
   - Deletes index tracking metadata

2. **Document Scanning**
   - Counts all eligible documents (.pdf, .txt, .csv, .html, .md)
   - Calculates total data size
   - Shows breakdown by file type

3. **Progress Tracking**
   - Real-time progress bar with:
     - Files completed/total
     - Time elapsed
     - Estimated time remaining
     - Current file being processed

4. **Indexing Process**
   - Loads documents in batches
   - Creates vector embeddings
   - Stores in ChromaDB
   - Updates tracking metadata

5. **Final Report**
   - Total files processed
   - Total chunks created
   - Processing time
   - Files per second
   - Any errors encountered

## Expected Output

```
╔═══════════════════════════════════════════════════════════╗
║     FULL REINDEX - Complete Database Reset & Rebuild      ║
╚═══════════════════════════════════════════════════════════╝

⚠️  WARNING: Full Reindex Operation

This will:
• Delete the entire ChromaDB database
• Remove all tracking metadata
• Reindex ALL documents from scratch

Proceed with full reindex? [y/N]: y

Starting Full Reindex Operation

Step 1/4: Cleaning existing database...
  ✓ ChromaDB database deleted

Step 2/4: Scanning for documents...
  ✓ Found 131 documents to index
  ✓ Total size: 24.56 MB

Document Types
┏━━━━━━┳━━━━━━━┓
┃ Type ┃ Count ┃
┡━━━━━━╇━━━━━━━┩
│ .pdf │    89 │
│ .txt │    32 │
│ .md  │    10 │
└──────┴───────┘

Step 3/4: Initializing indexer...
  ✓ ChromaDB initialized
  ✓ Index tracker initialized

Step 4/4: Indexing 131 documents...
Indexing documents... 131/131 100% ━━━━━━━━━ 0:01:23 0:00:00

============================================================

✓ Full Reindex Complete!

Files Processed: 131
Files Indexed: 131
Total Chunks: 5260
Errors: 0
Processing Time: 0:01:23
Average Speed: 1.6 files/sec
Chunks/sec: 63.4

Database Statistics:
Total Files Tracked    131
Total Chunks in DB     5260
Database Size          24.56 MB
Collection Name        energy_documents
```

## After Reindexing

### Check Status
```bash
make status          # Detailed tracking info
make stats          # Quick statistics
```

### Incremental Updates
```bash
make update         # Index only new files
make check-new      # See how many new files
```

### Search
```bash
make search QUERY="your search terms"
make interactive    # Interactive search mode
```

## Troubleshooting

### If reindex fails:
1. Check disk space: `df -h data/`
2. Check permissions: `ls -la data/`
3. Manual cleanup: `make clean-db`
4. Try again: `make full-reindex`

### Memory issues:
- Edit `config.py` and reduce `batch_size` (default: 50)
- Edit `config.py` and reduce `chunk_size` (default: 1000)

### Slow performance:
- Normal speed: 1-3 files/second
- Large PDFs may take longer
- Consider running overnight for large datasets

## Performance Expectations

| Dataset Size | Files | Expected Time |
|-------------|-------|---------------|
| Small       | <100  | 1-2 minutes   |
| Medium      | 100-500 | 5-10 minutes |
| Large       | 500-1000 | 15-30 minutes |
| Very Large  | 1000+ | 30+ minutes   |

## Notes

- The tracker file is stored at `data/chroma_db/index_tracker.json`
- Each file is hashed (SHA256) to detect changes
- Modified files are automatically reindexed during updates
- The system handles interrupted indexing gracefully