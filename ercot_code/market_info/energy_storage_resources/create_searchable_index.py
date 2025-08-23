#!/usr/bin/env python3
"""
Create a searchable index and comprehensive documentation for ERCOT ESR knowledge base.
Provides search capabilities and generates reference documentation.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ESRKnowledgeIndex:
    """Create and manage searchable index for ERCOT ESR knowledge base."""
    
    def __init__(self):
        self.index = {
            "metadata": {
                "creation_date": datetime.now().isoformat(),
                "version": "1.0"
            },
            "search_index": {},
            "topic_index": {},
            "document_index": {},
            "concept_index": {},
            "requirement_index": {},
            "timeline_index": {}
        }
        self.knowledge_base = None
        self.extracted_content = None
    
    def load_data(self):
        """Load knowledge base and extracted content."""
        try:
            with open("ercot_esr_knowledge_base.json", 'r') as f:
                self.knowledge_base = json.load(f)
            
            with open("ercot_esr_extracted_content.json", 'r') as f:
                self.extracted_content = json.load(f)
            
            logger.info("Data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def build_index(self):
        """Build comprehensive search index."""
        logger.info("Building search index...")
        
        # Index topics
        self._index_topics()
        
        # Index documents
        self._index_documents()
        
        # Index concepts
        self._index_concepts()
        
        # Index requirements
        self._index_requirements()
        
        # Index timeline
        self._index_timeline()
        
        # Build full-text search index
        self._build_search_index()
        
        logger.info(f"Index built with {len(self.index['search_index'])} searchable items")
    
    def _index_topics(self):
        """Index topics for quick lookup."""
        for topic_name, topic_data in self.knowledge_base["topics"].items():
            self.index["topic_index"][topic_name] = {
                "ktc": topic_data["ktc"],
                "document_count": topic_data["documents"],
                "key_points": topic_data["key_points"],
                "search_terms": self._extract_search_terms(topic_name + " " + " ".join(topic_data["key_points"]))
            }
    
    def _index_documents(self):
        """Index documents for quick lookup."""
        for doc in self.extracted_content["documents"]:
            doc_id = doc["file_name"]
            self.index["document_index"][doc_id] = {
                "path": doc["file_path"],
                "type": doc["file_type"],
                "ktc": doc["ktc"],
                "status": doc.get("metadata", {}).get("status", "Unknown"),
                "search_terms": self._extract_search_terms(doc["file_name"])
            }
            
            # Add content search terms
            if doc["file_type"] == "docx":
                content_text = " ".join(doc["content"]["paragraphs"][:10])  # First 10 paragraphs
            else:  # pptx
                content_text = " ".join(doc["content"]["titles"])
            
            self.index["document_index"][doc_id]["content_preview"] = content_text[:500]
            self.index["document_index"][doc_id]["search_terms"].extend(
                self._extract_search_terms(content_text)
            )
    
    def _index_concepts(self):
        """Index key concepts."""
        for concept, data in self.knowledge_base["glossary"].items():
            self.index["concept_index"][concept] = {
                "definition": data["definition"],
                "mentions": data["mentions"],
                "documents": data["related_documents"],
                "search_terms": self._extract_search_terms(concept + " " + data["definition"])
            }
    
    def _index_requirements(self):
        """Index technical requirements and specifications."""
        tech_specs = self.knowledge_base["technical_specs"]
        
        for req_type, requirements in tech_specs.items():
            self.index["requirement_index"][req_type] = []
            
            for req in requirements:
                if isinstance(req, dict):
                    indexed_req = {
                        "type": req_type,
                        "content": req.get("requirement", "") or str(req.get("table", "")),
                        "source": req.get("source", ""),
                        "search_terms": self._extract_search_terms(str(req))
                    }
                    self.index["requirement_index"][req_type].append(indexed_req)
    
    def _index_timeline(self):
        """Index regulatory timeline."""
        for event in self.knowledge_base["timeline"]:
            date_key = event["date"]
            if date_key not in self.index["timeline_index"]:
                self.index["timeline_index"][date_key] = []
            
            self.index["timeline_index"][date_key].append({
                "event": event["event"],
                "document": event["document"],
                "search_terms": self._extract_search_terms(event["event"] + " " + event["document"])
            })
    
    def _build_search_index(self):
        """Build full-text search index."""
        search_id = 0
        
        # Index topics
        for topic_name, topic_data in self.index["topic_index"].items():
            self.index["search_index"][f"topic_{search_id}"] = {
                "type": "topic",
                "title": topic_name,
                "content": " ".join(topic_data["key_points"]),
                "reference": topic_data["ktc"],
                "search_terms": topic_data["search_terms"]
            }
            search_id += 1
        
        # Index documents
        for doc_name, doc_data in self.index["document_index"].items():
            self.index["search_index"][f"doc_{search_id}"] = {
                "type": "document",
                "title": doc_name,
                "content": doc_data.get("content_preview", ""),
                "reference": doc_data["path"],
                "search_terms": doc_data["search_terms"]
            }
            search_id += 1
        
        # Index concepts
        for concept, concept_data in self.index["concept_index"].items():
            self.index["search_index"][f"concept_{search_id}"] = {
                "type": "concept",
                "title": concept,
                "content": concept_data["definition"],
                "reference": f"Mentioned {concept_data['mentions']} times",
                "search_terms": concept_data["search_terms"]
            }
            search_id += 1
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract search terms from text."""
        # Convert to lowercase and split
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                     'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
                     'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might'}
        
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def search(self, query: str, search_type: Optional[str] = None) -> List[Dict]:
        """Search the index for matching items."""
        query_terms = self._extract_search_terms(query)
        results = []
        
        for item_id, item_data in self.index["search_index"].items():
            # Filter by type if specified
            if search_type and item_data["type"] != search_type:
                continue
            
            # Calculate relevance score
            score = 0
            for term in query_terms:
                if term in item_data["search_terms"]:
                    score += item_data["search_terms"].count(term)
                if term in item_data["title"].lower():
                    score += 5  # Higher weight for title matches
                if term in item_data["content"].lower():
                    score += 1
            
            if score > 0:
                results.append({
                    "id": item_id,
                    "type": item_data["type"],
                    "title": item_data["title"],
                    "content": item_data["content"][:200] + "..." if len(item_data["content"]) > 200 else item_data["content"],
                    "reference": item_data["reference"],
                    "score": score
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:20]  # Return top 20 results
    
    def save_index(self, output_file: str = "ercot_esr_search_index.json"):
        """Save the search index to file."""
        with open(output_file, 'w') as f:
            json.dump(self.index, f, indent=2)
        logger.info(f"Search index saved to {output_file}")
    
    def generate_documentation(self):
        """Generate comprehensive reference documentation."""
        logger.info("Generating reference documentation...")
        
        doc = []
        doc.append("# ERCOT Energy Storage Resources - Comprehensive Reference Documentation")
        doc.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("\n---\n")
        
        # Executive Summary
        doc.append("## Executive Summary\n")
        doc.append("This documentation provides a comprehensive reference for ERCOT's Energy Storage Resource (ESR) ")
        doc.append("implementation framework, including technical requirements, market operations, and regulatory guidelines.\n")
        
        # Table of Contents
        doc.append("## Table of Contents\n")
        doc.append("1. [Key Topics and Concepts](#key-topics-and-concepts)")
        doc.append("2. [Technical Requirements](#technical-requirements)")
        doc.append("3. [Market Operations](#market-operations)")
        doc.append("4. [Regulatory Timeline](#regulatory-timeline)")
        doc.append("5. [Glossary](#glossary)")
        doc.append("6. [Document Index](#document-index)\n")
        
        # Key Topics and Concepts
        doc.append("## Key Topics and Concepts\n")
        for topic_name, topic_data in sorted(self.knowledge_base["topics"].items()):
            doc.append(f"\n### {topic_name}")
            doc.append(f"\n**KTC Reference:** {topic_data['ktc']}")
            doc.append(f"\n**Documents:** {topic_data['documents']}")
            
            if topic_data["key_points"]:
                doc.append("\n\n**Key Points:**")
                for point in topic_data["key_points"][:5]:
                    doc.append(f"\n- {point}")
        
        # Technical Requirements
        doc.append("\n## Technical Requirements\n")
        tech_specs = self.knowledge_base["technical_specs"]
        
        for req_type, requirements in tech_specs.items():
            if requirements:
                doc.append(f"\n### {req_type.replace('_', ' ').title()}")
                
                for i, req in enumerate(requirements[:5], 1):
                    if isinstance(req, dict):
                        if "requirement" in req:
                            doc.append(f"\n{i}. {req['requirement'][:200]}...")
                            doc.append(f"\n   *Source: {req.get('source', 'Unknown')}*")
        
        # Market Operations
        doc.append("\n## Market Operations\n")
        doc.append("\n### Energy Storage Resource Participation")
        doc.append("\nESRs can participate in ERCOT markets through:")
        doc.append("\n- Energy-only offers and bids")
        doc.append("\n- Ancillary services (Regulation, Responsive Reserve)")
        doc.append("\n- Non-Spin reserve services")
        doc.append("\n- Real-time energy dispatch")
        
        # Regulatory Timeline
        doc.append("\n## Regulatory Timeline\n")
        if self.knowledge_base["timeline"]:
            for event in sorted(self.knowledge_base["timeline"], key=lambda x: x["date"]):
                doc.append(f"\n**{event['date']}** - {event['event']}")
                doc.append(f"\n*Document: {event['document']}*")
        
        # Glossary
        doc.append("\n## Glossary\n")
        for concept, data in sorted(self.knowledge_base["glossary"].items()):
            doc.append(f"\n**{concept}**")
            if data["definition"]:
                doc.append(f"\n{data['definition'][:300]}...")
            doc.append(f"\n*Mentions: {data['mentions']} | Documents: {len(data['related_documents'])}*")
        
        # Document Index
        doc.append("\n## Document Index\n")
        doc.append("\n### By KTC Category\n")
        
        for ktc in sorted(self.extracted_content["ktc_content"].keys()):
            ktc_data = self.extracted_content["ktc_content"][ktc]
            doc.append(f"\n**{ktc.upper()} - {ktc_data['topic']}**")
            
            for doc_data in ktc_data["documents"]:
                doc.append(f"\n- {doc_data['file_name']}")
                if "metadata" in doc_data and "status" in doc_data["metadata"]:
                    doc.append(f" [{doc_data['metadata']['status']}]")
        
        # Save documentation
        output_file = "ERCOT_ESR_REFERENCE_DOCUMENTATION.md"
        with open(output_file, 'w') as f:
            f.write("\n".join(doc))
        
        logger.info(f"Documentation saved to {output_file}")
        
        return output_file


def create_quick_reference():
    """Create a quick reference guide."""
    logger.info("Creating quick reference guide...")
    
    ref = []
    ref.append("# ERCOT ESR Quick Reference Guide")
    ref.append("\n## Essential Information for Energy Storage Resources\n")
    
    # Key Acronyms
    ref.append("### Key Acronyms")
    ref.append("- **ESR**: Energy Storage Resource")
    ref.append("- **ESRDP**: Energy Storage Resource Deployment Plan")
    ref.append("- **SOC**: State of Charge")
    ref.append("- **GINR**: Generation Interconnection or Change Request")
    ref.append("- **WSL**: Wholesale Storage Load")
    ref.append("- **ORDC**: Operating Reserve Demand Curve")
    ref.append("- **PRC**: Physical Responsive Capability")
    ref.append("- **BPD**: Base-Point Deviation")
    ref.append("- **TAC**: Technical Advisory Committee")
    ref.append("- **BESTF**: Battery Energy Storage Task Force\n")
    
    # Key Topics
    ref.append("### Key Topic Categories (KTCs)")
    ref.append("1. **KTC1**: ESR Registration Process")
    ref.append("2. **KTC2**: PRC and ORDC Reserve Participation")
    ref.append("3. **KTC3**: Nodal Pricing and Dispatch")
    ref.append("4. **KTC4**: Technical Requirements")
    ref.append("5. **KTC5**: Single Model ESRDP")
    ref.append("6. **KTC6**: State of Charge Management")
    ref.append("7. **KTC7**: Base-Point Deviation")
    ref.append("8. **KTC8**: Wholesale Storage Load Treatment")
    ref.append("9. **KTC10**: RUC/COP Submittals")
    ref.append("10. **KTC11**: DC-Coupled Hybrid Resources")
    ref.append("11. **KTC12**: AC-Connected Co-Located Resources")
    ref.append("12. **KTC13**: Self-Limiting GINRs")
    ref.append("13. **KTC14**: New Studies")
    ref.append("14. **KTC15**: Proxy Energy Offers and Bids\n")
    
    # Critical Requirements
    ref.append("### Critical Requirements")
    ref.append("- Minimum capacity: 1 MW")
    ref.append("- Must be capable of both charging and discharging")
    ref.append("- Required telemetry for SOC reporting")
    ref.append("- Compliance with interconnection standards")
    ref.append("- Registration as both generator and load\n")
    
    # Market Participation
    ref.append("### Market Participation Options")
    ref.append("- **Energy Market**: Buy/sell energy at LMP")
    ref.append("- **Ancillary Services**: Regulation Up/Down, Responsive Reserve")
    ref.append("- **Non-Spin Reserve**: Stand-by capacity")
    ref.append("- **Emergency Response Service**: Critical grid support\n")
    
    # Key Dates
    ref.append("### Implementation Timeline")
    ref.append("- **Oct 2019**: Initial BESTF proposals")
    ref.append("- **Nov 2019**: Consensus on registration (KTC1)")
    ref.append("- **Jan 2020**: TAC approval of KTC1, KTC5, KTC8")
    ref.append("- **Mar 2020**: Consensus on hybrid resources")
    ref.append("- **Apr 2020**: TAC approval of final KTCs\n")
    
    # Resources
    ref.append("### Additional Resources")
    ref.append("- Full documentation: `ERCOT_ESR_REFERENCE_DOCUMENTATION.md`")
    ref.append("- Search index: `ercot_esr_search_index.json`")
    ref.append("- Knowledge base: `ercot_esr_knowledge_base.json`")
    ref.append("- Raw documents: `downloads/` directory\n")
    
    # Save quick reference
    output_file = "ERCOT_ESR_QUICK_REFERENCE.md"
    with open(output_file, 'w') as f:
        f.write("\n".join(ref))
    
    logger.info(f"Quick reference saved to {output_file}")
    
    return output_file


def main():
    """Main execution function."""
    # Create index
    indexer = ESRKnowledgeIndex()
    
    # Load data
    indexer.load_data()
    
    # Build index
    indexer.build_index()
    
    # Save index
    indexer.save_index()
    
    # Generate documentation
    doc_file = indexer.generate_documentation()
    
    # Create quick reference
    ref_file = create_quick_reference()
    
    # Test search functionality
    print("\n" + "="*60)
    print("ERCOT ESR Knowledge Base Indexing Complete")
    print("="*60)
    
    print(f"\nIndex Statistics:")
    print(f"  - Searchable items: {len(indexer.index['search_index'])}")
    print(f"  - Topics indexed: {len(indexer.index['topic_index'])}")
    print(f"  - Documents indexed: {len(indexer.index['document_index'])}")
    print(f"  - Concepts indexed: {len(indexer.index['concept_index'])}")
    
    print("\nOutput Files Created:")
    print(f"  - Search index: ercot_esr_search_index.json")
    print(f"  - Reference documentation: {doc_file}")
    print(f"  - Quick reference: {ref_file}")
    
    # Demo search
    print("\nSample Search Results:")
    test_queries = ["registration", "state of charge", "hybrid"]
    
    for query in test_queries:
        results = indexer.search(query)
        print(f"\n  Query: '{query}'")
        print(f"  Found: {len(results)} results")
        if results:
            print(f"  Top result: {results[0]['title']} (score: {results[0]['score']})")


if __name__ == "__main__":
    main()