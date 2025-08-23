#!/usr/bin/env python3
"""
ERCOT Nodal Protocols Search Engine
A comprehensive text search system with indexing and requirement extraction
"""

import os
import re
import json
import pickle
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import string
from typing import List, Dict, Tuple, Set

class ERCOTSearchEngine:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.index_dir = self.base_dir / "search_index"
        self.index_dir.mkdir(exist_ok=True)
        
        # Document metadata
        self.documents = {}
        self.doc_sections = {}
        
        # Search indices
        self.word_index = defaultdict(set)  # word -> set of doc_ids
        self.phrase_index = defaultdict(set)  # phrase -> set of doc_ids
        self.section_index = defaultdict(dict)  # section -> {doc_id: [line_numbers]}
        
        # Requirements database
        self.requirements = defaultdict(list)
        self.definitions = defaultdict(list)
        self.deadlines = defaultdict(list)
        self.forms = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'total_words': 0,
            'total_lines': 0,
            'total_requirements': 0,
            'total_definitions': 0,
            'index_created': None
        }
        
    def load_documents(self):
        """Load all text documents into memory"""
        print("Loading documents...")
        txt_files = sorted(self.base_dir.glob("*Nodal.txt"))
        txt_files.append(self.base_dir / "ERCOT-Fee-Schedule-060125.txt")
        
        for doc_path in txt_files:
            if doc_path.exists():
                doc_id = doc_path.stem
                print(f"  Loading: {doc_id}")
                
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                self.documents[doc_id] = {
                    'path': str(doc_path),
                    'content': content,
                    'lines': lines,
                    'size': len(content),
                    'line_count': len(lines),
                    'section': self._extract_section_info(doc_id)
                }
                
                self.stats['total_documents'] += 1
                self.stats['total_lines'] += len(lines)
        
        print(f"Loaded {self.stats['total_documents']} documents")
        return self.stats['total_documents']
    
    def _extract_section_info(self, doc_id):
        """Extract section information from document ID"""
        # Pattern for main sections (e.g., "01-040125_Nodal" -> Section 1)
        main_match = re.match(r'^(\d+)-', doc_id)
        if main_match:
            return f"Section {int(main_match.group(1))}"
        
        # Pattern for subsections (e.g., "22A-040122_Nodal" -> Section 22A)
        sub_match = re.match(r'^(\d+[A-Z])-', doc_id)
        if sub_match:
            return f"Section {sub_match.group(1)}"
        
        # Special cases
        if "Fee-Schedule" in doc_id:
            return "Fee Schedule"
        
        return "Unknown Section"
    
    def build_index(self):
        """Build comprehensive search indices"""
        print("\nBuilding search indices...")
        
        for doc_id, doc_data in self.documents.items():
            print(f"  Indexing: {doc_id}")
            content = doc_data['content'].lower()
            lines = doc_data['lines']
            
            # Build word index
            words = re.findall(r'\b[a-z]+\b', content)
            unique_words = set(words)
            for word in unique_words:
                if len(word) > 2:  # Skip very short words
                    self.word_index[word].add(doc_id)
            
            self.stats['total_words'] += len(words)
            
            # Build phrase index for common ERCOT terms
            self._index_phrases(doc_id, content)
            
            # Build section index
            self._index_sections(doc_id, lines)
            
            # Extract requirements
            self._extract_requirements(doc_id, lines)
            
            # Extract definitions
            self._extract_definitions(doc_id, lines)
            
            # Extract deadlines and timelines
            self._extract_deadlines(doc_id, lines)
            
            # Extract forms
            self._extract_forms(doc_id, lines)
        
        self.stats['index_created'] = datetime.now().isoformat()
        print(f"Index built: {len(self.word_index)} unique words indexed")
        
    def _index_phrases(self, doc_id, content):
        """Index common ERCOT phrases"""
        phrases = [
            'energy storage resource', 'esr',
            'battery energy storage', 'bess',
            'ancillary service', 'ancillary services',
            'responsive reserve', 'rrs',
            'regulation up', 'regulation down',
            'ercot contingency reserve', 'ecrs',
            'non-spinning reserve', 'non-spin',
            'security constrained economic dispatch', 'sced',
            'day-ahead market', 'dam',
            'real-time market', 'rtm',
            'locational marginal price', 'lmp',
            'point of interconnection', 'poi',
            'transmission service provider', 'tsp',
            'distribution service provider', 'dsp',
            'qualified scheduling entity', 'qse',
            'resource entity', 're',
            'current operating plan', 'cop',
            'outage scheduler', 'os',
            'network operations model', 'nom',
            'state of charge', 'soc',
            'wholesale storage load', 'wsl',
            'settlement only', 'sotess', 'sodess',
            'generation resource', 'gen',
            'load resource', 'lr',
            'controllable load resource', 'clr',
            'distributed energy resource', 'der',
            'distribution energy storage resource', 'desr'
        ]
        
        for phrase in phrases:
            if phrase in content:
                self.phrase_index[phrase].add(doc_id)
    
    def _index_sections(self, doc_id, lines):
        """Index document sections and subsections"""
        current_section = None
        section_pattern = re.compile(r'^(\d+\.?\d*)\s+(.+)')
        
        for i, line in enumerate(lines):
            match = section_pattern.match(line.strip())
            if match:
                section_num = match.group(1)
                section_title = match.group(2)
                
                # Store section info
                if section_num not in self.section_index:
                    self.section_index[section_num] = {}
                
                if doc_id not in self.section_index[section_num]:
                    self.section_index[section_num][doc_id] = []
                
                self.section_index[section_num][doc_id].append({
                    'line': i,
                    'title': section_title
                })
    
    def _extract_requirements(self, doc_id, lines):
        """Extract requirements from document"""
        requirement_patterns = [
            r'shall\s+(.+)',
            r'must\s+(.+)',
            r'required to\s+(.+)',
            r'responsible for\s+(.+)',
            r'obligation to\s+(.+)',
            r'will be required\s+(.+)',
            r'are required\s+(.+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in requirement_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    requirement = {
                        'doc_id': doc_id,
                        'line_num': i,
                        'text': line.strip(),
                        'type': pattern.split('\\s+')[0]
                    }
                    self.requirements[doc_id].append(requirement)
                    self.stats['total_requirements'] += 1
                    break
    
    def _extract_definitions(self, doc_id, lines):
        """Extract definitions from document"""
        definition_patterns = [
            r'"([^"]+)"\s+means\s+(.+)',
            r'"([^"]+)"\s+is defined as\s+(.+)',
            r'"([^"]+)":\s+(.+)',
            r'([A-Z][^"]+)\s+means\s+(.+)',
            r'([A-Z][^"]+)\s+is defined as\s+(.+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in definition_patterns:
                match = re.search(pattern, line)
                if match:
                    definition = {
                        'term': match.group(1),
                        'definition': match.group(2) if len(match.groups()) > 1 else line,
                        'doc_id': doc_id,
                        'line_num': i
                    }
                    self.definitions[doc_id].append(definition)
                    self.stats['total_definitions'] += 1
                    break
    
    def _extract_deadlines(self, doc_id, lines):
        """Extract deadlines and timelines"""
        deadline_patterns = [
            r'(\d+)\s+days?\s+(before|after|prior|following)',
            r'within\s+(\d+)\s+days?',
            r'no later than\s+(\d+)',
            r'at least\s+(\d+)\s+days?',
            r'(\d+)\s+business days?',
            r'(\d+)\s+hours?\s+(before|after|prior)',
            r'by\s+(\d+:\d+)\s*([AaPp][Mm])?'
        ]
        
        for i, line in enumerate(lines):
            for pattern in deadline_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    deadline = {
                        'doc_id': doc_id,
                        'line_num': i,
                        'text': line.strip(),
                        'deadline': match.group(0)
                    }
                    self.deadlines[doc_id].append(deadline)
    
    def _extract_forms(self, doc_id, lines):
        """Extract form references"""
        form_patterns = [
            r'Form\s+([A-Z0-9-]+)',
            r'Section\s+(22[A-Z])',
            r'Appendix\s+([A-Z0-9]+)',
            r'Attachment\s+([A-Z0-9]+)',
            r'Exhibit\s+([A-Z0-9]+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in form_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    form = {
                        'doc_id': doc_id,
                        'line_num': i,
                        'form_id': match.group(1),
                        'type': pattern.split('\\s+')[0],
                        'context': line.strip()
                    }
                    self.forms[doc_id].append(form)
    
    def search(self, query, search_type='all', max_results=50):
        """
        Search documents with various search types
        
        Args:
            query: Search query string
            search_type: 'all', 'exact', 'requirements', 'definitions', 'forms'
            max_results: Maximum number of results to return
        """
        results = []
        query_lower = query.lower()
        
        if search_type in ['all', 'exact']:
            # Word-based search
            words = re.findall(r'\b[a-z]+\b', query_lower)
            matching_docs = None
            
            for word in words:
                if word in self.word_index:
                    if matching_docs is None:
                        matching_docs = self.word_index[word].copy()
                    else:
                        matching_docs &= self.word_index[word]
            
            if matching_docs:
                for doc_id in matching_docs:
                    doc = self.documents[doc_id]
                    # Find matching lines
                    matching_lines = []
                    for i, line in enumerate(doc['lines']):
                        if query_lower in line.lower():
                            matching_lines.append({
                                'line_num': i + 1,
                                'text': line.strip()[:200]  # First 200 chars
                            })
                    
                    if matching_lines:
                        results.append({
                            'doc_id': doc_id,
                            'section': doc['section'],
                            'matches': matching_lines[:5],  # Top 5 matches
                            'total_matches': len(matching_lines)
                        })
        
        if search_type in ['all', 'requirements']:
            # Search requirements
            for doc_id, reqs in self.requirements.items():
                for req in reqs:
                    if query_lower in req['text'].lower():
                        results.append({
                            'doc_id': doc_id,
                            'type': 'requirement',
                            'line_num': req['line_num'] + 1,
                            'text': req['text'][:200]
                        })
        
        if search_type in ['all', 'definitions']:
            # Search definitions
            for doc_id, defs in self.definitions.items():
                for defn in defs:
                    if query_lower in defn['term'].lower() or query_lower in defn.get('definition', '').lower():
                        results.append({
                            'doc_id': doc_id,
                            'type': 'definition',
                            'term': defn['term'],
                            'definition': defn.get('definition', '')[:200]
                        })
        
        if search_type in ['all', 'forms']:
            # Search forms
            for doc_id, form_list in self.forms.items():
                for form in form_list:
                    if query_lower in form['form_id'].lower() or query_lower in form['context'].lower():
                        results.append({
                            'doc_id': doc_id,
                            'type': 'form',
                            'form_id': form['form_id'],
                            'context': form['context'][:200]
                        })
        
        return results[:max_results]
    
    def generate_master_index(self):
        """Generate a master index document"""
        print("\nGenerating master index...")
        
        index_path = self.base_dir / "MASTER_INDEX.md"
        
        with open(index_path, 'w') as f:
            f.write("# ERCOT Nodal Protocols - Master Index\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Document overview
            f.write("## Document Overview\n\n")
            f.write("| Section | Document ID | Title | Lines | Size (KB) |\n")
            f.write("|---------|------------|-------|-------|----------|\n")
            
            for doc_id in sorted(self.documents.keys()):
                doc = self.documents[doc_id]
                f.write(f"| {doc['section']} | {doc_id} | ")
                f.write(f"{self._get_doc_title(doc_id)} | ")
                f.write(f"{doc['line_count']:,} | ")
                f.write(f"{doc['size'] // 1024} |\n")
            
            # Key topics index
            f.write("\n## Key Topics Index\n\n")
            
            # ESR/BESS specific topics
            f.write("### Energy Storage Resources (ESR/BESS)\n\n")
            esr_terms = ['energy storage resource', 'esr', 'battery energy storage', 'bess',
                        'wholesale storage load', 'wsl', 'state of charge', 'soc']
            for term in esr_terms:
                if term in self.phrase_index:
                    docs = self.phrase_index[term]
                    f.write(f"- **{term.upper()}**: Found in {len(docs)} documents\n")
                    for doc_id in sorted(list(docs)[:5]):
                        f.write(f"  - {doc_id}\n")
            
            # Ancillary Services
            f.write("\n### Ancillary Services\n\n")
            as_terms = ['ancillary service', 'regulation up', 'regulation down',
                       'responsive reserve', 'rrs', 'ecrs', 'non-spinning reserve']
            for term in as_terms:
                if term in self.phrase_index:
                    docs = self.phrase_index[term]
                    f.write(f"- **{term.upper()}**: Found in {len(docs)} documents\n")
            
            # Market Operations
            f.write("\n### Market Operations\n\n")
            market_terms = ['day-ahead market', 'dam', 'real-time market', 'rtm',
                           'sced', 'lmp', 'cop']
            for term in market_terms:
                if term in self.phrase_index:
                    docs = self.phrase_index[term]
                    f.write(f"- **{term.upper()}**: Found in {len(docs)} documents\n")
            
            # Requirements Summary
            f.write("\n## Requirements Summary\n\n")
            f.write(f"Total requirements identified: {self.stats['total_requirements']}\n\n")
            
            req_by_type = defaultdict(int)
            for doc_id, reqs in self.requirements.items():
                for req in reqs:
                    req_by_type[req['type']] += 1
            
            f.write("| Requirement Type | Count |\n")
            f.write("|-----------------|-------|\n")
            for req_type, count in sorted(req_by_type.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {req_type} | {count} |\n")
            
            # Forms and Documents
            f.write("\n## Forms and Documents\n\n")
            all_forms = set()
            for doc_id, form_list in self.forms.items():
                for form in form_list:
                    all_forms.add(f"{form['type']} {form['form_id']}")
            
            f.write(f"Total forms identified: {len(all_forms)}\n\n")
            for form in sorted(all_forms)[:20]:
                f.write(f"- {form}\n")
            
            # Statistics
            f.write("\n## Index Statistics\n\n")
            f.write(f"- Total documents: {self.stats['total_documents']}\n")
            f.write(f"- Total words indexed: {self.stats['total_words']:,}\n")
            f.write(f"- Total lines: {self.stats['total_lines']:,}\n")
            f.write(f"- Unique words: {len(self.word_index):,}\n")
            f.write(f"- Requirements extracted: {self.stats['total_requirements']:,}\n")
            f.write(f"- Definitions extracted: {self.stats['total_definitions']:,}\n")
            f.write(f"- Index created: {self.stats['index_created']}\n")
        
        print(f"Master index saved to: {index_path}")
        return str(index_path)
    
    def _get_doc_title(self, doc_id):
        """Get document title based on section number"""
        titles = {
            '01': 'Overview',
            '02': 'Definitions and Acronyms',
            '03': 'Management Activities',
            '04': 'Day-Ahead Operations',
            '05': 'Transmission Security Analysis',
            '06': 'Adjustment Period and Real-Time Operations',
            '07': 'System Operations',
            '08': 'Transmission Congestion Management',
            '09': 'Settlement',
            '10': 'Metering',
            '11': 'Data Collection and Aggregation',
            '12': 'Transmission and Distribution Losses',
            '13': 'Dispute Resolution',
            '14': 'State of Texas Renewable Energy Credit Trading',
            '15': 'Renewable Energy Credit Trading',
            '16': 'Registration and Qualification',
            '17': 'Planning',
            '18': 'Texas Nodal Market Implementation',
            '19': 'Texas RE-Market Reliability',
            '20': 'System Support Services',
            '21': 'Generation Resources',
            '22': 'Market Participant Agreements',
            '23': 'Common Practices',
            '24': 'Emergency Operations',
            '25': 'Activities for Reliability Must-Run',
            '26': 'Public Utility Commission Rules',
            '27': 'Electric Substantive Rules'
        }
        
        # Extract section number
        match = re.match(r'^(\d+)', doc_id)
        if match:
            section = match.group(1)
            if section in titles:
                return titles[section]
        
        if 'Fee-Schedule' in doc_id:
            return 'Fee Schedule'
        
        return 'Protocol Document'
    
    def save_index(self):
        """Save index to disk for faster loading"""
        index_file = self.index_dir / "search_index.pkl"
        
        index_data = {
            'documents': self.documents,
            'word_index': dict(self.word_index),
            'phrase_index': dict(self.phrase_index),
            'section_index': dict(self.section_index),
            'requirements': dict(self.requirements),
            'definitions': dict(self.definitions),
            'deadlines': dict(self.deadlines),
            'forms': dict(self.forms),
            'stats': self.stats
        }
        
        with open(index_file, 'wb') as f:
            pickle.dump(index_data, f)
        
        print(f"Index saved to: {index_file}")
        return str(index_file)
    
    def load_index(self):
        """Load index from disk"""
        index_file = self.index_dir / "search_index.pkl"
        
        if index_file.exists():
            with open(index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            self.documents = index_data['documents']
            self.word_index = defaultdict(set, index_data['word_index'])
            self.phrase_index = defaultdict(set, index_data['phrase_index'])
            self.section_index = defaultdict(dict, index_data['section_index'])
            self.requirements = defaultdict(list, index_data['requirements'])
            self.definitions = defaultdict(list, index_data['definitions'])
            self.deadlines = defaultdict(list, index_data['deadlines'])
            self.forms = defaultdict(list, index_data['forms'])
            self.stats = index_data['stats']
            
            print(f"Index loaded from: {index_file}")
            return True
        
        return False


def main():
    """Main function to build and test the search engine"""
    print("=" * 60)
    print("ERCOT Nodal Protocols Search Engine")
    print("=" * 60)
    
    engine = ERCOTSearchEngine()
    
    # Try to load existing index
    if not engine.load_index():
        # Build new index
        engine.load_documents()
        engine.build_index()
        engine.save_index()
    
    # Generate master index
    engine.generate_master_index()
    
    # Interactive search
    print("\n" + "=" * 60)
    print("Search Engine Ready!")
    print("Commands: 'search <query>', 'req <query>', 'def <term>', 'quit'")
    print("=" * 60)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() == 'quit':
                break
            
            if command.startswith('search '):
                query = command[7:]
                results = engine.search(query, 'all')
                
                if results:
                    print(f"\nFound {len(results)} results for '{query}':\n")
                    for i, result in enumerate(results[:10], 1):
                        print(f"{i}. {result['doc_id']} - ", end="")
                        if 'type' in result:
                            print(f"[{result['type']}] ", end="")
                        if 'text' in result:
                            print(result['text'][:100])
                        elif 'matches' in result:
                            print(f"{result['total_matches']} matches")
                else:
                    print(f"No results found for '{query}'")
            
            elif command.startswith('req '):
                query = command[4:]
                results = engine.search(query, 'requirements')
                
                if results:
                    print(f"\nFound {len(results)} requirements for '{query}':\n")
                    for i, result in enumerate(results[:10], 1):
                        print(f"{i}. {result['doc_id']} (line {result['line_num']})")
                        print(f"   {result['text'][:150]}")
                else:
                    print(f"No requirements found for '{query}'")
            
            elif command.startswith('def '):
                query = command[4:]
                results = engine.search(query, 'definitions')
                
                if results:
                    print(f"\nFound {len(results)} definitions for '{query}':\n")
                    for i, result in enumerate(results[:10], 1):
                        print(f"{i}. {result['term']}")
                        print(f"   {result['definition'][:150]}")
                else:
                    print(f"No definitions found for '{query}'")
            
            elif command == 'stats':
                print("\nSearch Engine Statistics:")
                for key, value in engine.stats.items():
                    print(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")
            
            elif command == 'help':
                print("\nAvailable commands:")
                print("  search <query> - Full text search")
                print("  req <query>    - Search requirements")
                print("  def <term>     - Search definitions")
                print("  stats          - Show statistics")
                print("  quit           - Exit")
            
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()