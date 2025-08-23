#!/usr/bin/env python3
"""
ERCOT Requirements Database Extractor
Extracts and categorizes all requirements, deadlines, and obligations from ERCOT protocols
"""

import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import csv

class RequirementsExtractor:
    def __init__(self, base_dir="/pool/ssd8tb/data/iso/ERCOT/market_rules/nodal_protocols/"):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / "requirements_database"
        self.output_dir.mkdir(exist_ok=True)
        
        self.requirements = []
        self.deadlines = []
        self.forms = []
        self.fees = []
        self.testing = []
        self.operational = []
        
        # Categories for requirements
        self.categories = {
            'registration': [],
            'metering': [],
            'telemetry': [],
            'ancillary_services': [],
            'market_participation': [],
            'compliance': [],
            'testing': [],
            'operational': [],
            'financial': [],
            'reporting': [],
            'outage': [],
            'interconnection': [],
            'data_submission': []
        }
        
    def load_document(self, file_path):
        """Load a text document"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    
    def extract_all_requirements(self):
        """Extract requirements from all documents"""
        print("Extracting requirements from all documents...")
        
        txt_files = sorted(self.base_dir.glob("*Nodal.txt"))
        txt_files.append(self.base_dir / "ERCOT-Fee-Schedule-060125.txt")
        
        for doc_path in txt_files:
            if doc_path.exists():
                doc_id = doc_path.stem
                print(f"  Processing: {doc_id}")
                
                lines = self.load_document(doc_path)
                
                # Extract different types of requirements
                self._extract_shall_must(doc_id, lines)
                self._extract_deadlines(doc_id, lines)
                self._extract_forms(doc_id, lines)
                self._extract_fees(doc_id, lines)
                self._extract_testing_requirements(doc_id, lines)
                self._extract_operational_requirements(doc_id, lines)
        
        print(f"\nExtraction complete:")
        print(f"  Requirements: {len(self.requirements)}")
        print(f"  Deadlines: {len(self.deadlines)}")
        print(f"  Forms: {len(self.forms)}")
        print(f"  Fees: {len(self.fees)}")
        print(f"  Testing: {len(self.testing)}")
        print(f"  Operational: {len(self.operational)}")
    
    def _extract_shall_must(self, doc_id, lines):
        """Extract SHALL and MUST requirements"""
        patterns = [
            (r'\bshall\s+(.{20,200})', 'SHALL'),
            (r'\bmust\s+(.{20,200})', 'MUST'),
            (r'\brequired to\s+(.{20,200})', 'REQUIRED'),
            (r'\bresponsible for\s+(.{20,200})', 'RESPONSIBLE'),
            (r'\bwill be required\s+(.{20,200})', 'WILL_BE_REQUIRED'),
            (r'\bobligated to\s+(.{20,200})', 'OBLIGATED')
        ]
        
        for i, line in enumerate(lines):
            for pattern, req_type in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    requirement = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'type': req_type,
                        'text': match.group(0).strip(),
                        'context': line.strip()[:300],
                        'category': self._categorize_requirement(line)
                    }
                    
                    self.requirements.append(requirement)
                    
                    # Add to category
                    category = requirement['category']
                    if category in self.categories:
                        self.categories[category].append(requirement)
    
    def _extract_deadlines(self, doc_id, lines):
        """Extract time-based requirements and deadlines"""
        patterns = [
            (r'within\s+(\d+)\s+(business\s+)?days?', 'DAYS'),
            (r'(\d+)\s+(business\s+)?days?\s+(before|after|prior|following)', 'DAYS_RELATIVE'),
            (r'no later than\s+(\d+)\s+days?', 'NO_LATER_THAN'),
            (r'at least\s+(\d+)\s+(business\s+)?days?', 'AT_LEAST'),
            (r'(\d+)\s+hours?\s+(before|after|prior)', 'HOURS'),
            (r'by\s+(\d{1,2}:\d{2})\s*([AaPp][Mm])?', 'TIME'),
            (r'(\d+)\s+minutes?', 'MINUTES'),
            (r'immediately', 'IMMEDIATE'),
            (r'as soon as (practicable|possible)', 'ASAP'),
            (r'annually', 'ANNUAL'),
            (r'monthly', 'MONTHLY'),
            (r'quarterly', 'QUARTERLY'),
            (r'daily', 'DAILY')
        ]
        
        for i, line in enumerate(lines):
            for pattern, deadline_type in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    deadline = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'type': deadline_type,
                        'value': match.group(1) if len(match.groups()) > 0 else match.group(0),
                        'text': match.group(0),
                        'context': line.strip()[:300],
                        'category': self._categorize_requirement(line)
                    }
                    
                    self.deadlines.append(deadline)
    
    def _extract_forms(self, doc_id, lines):
        """Extract form references and requirements"""
        patterns = [
            r'Form\s+([A-Z0-9-]+)',
            r'Section\s+(22[A-Z])\s+form',
            r'Attachment\s+([A-Z0-9]+)',
            r'Appendix\s+([A-Z0-9]+)',
            r'Exhibit\s+([A-Z0-9]+)',
            r'Schedule\s+([A-Z0-9]+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    form = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'form_id': match.group(1),
                        'form_type': pattern.split('\\s+')[0],
                        'context': line.strip()[:300],
                        'submission_required': 'submit' in line.lower() or 'provide' in line.lower()
                    }
                    
                    self.forms.append(form)
    
    def _extract_fees(self, doc_id, lines):
        """Extract fee and cost information"""
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'fee\s+of\s+\$[\d,]+',
            r'\$[\d,]+\s+per\s+\w+',
            r'cost\s+of\s+\$[\d,]+',
            r'charge\s+of\s+\$[\d,]+',
            r'deposit\s+of\s+\$[\d,]+',
            r'penalty\s+of\s+\$[\d,]+'
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    fee = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'amount': match.group(0),
                        'context': line.strip()[:300],
                        'fee_type': self._categorize_fee(line)
                    }
                    
                    self.fees.append(fee)
    
    def _extract_testing_requirements(self, doc_id, lines):
        """Extract testing and qualification requirements"""
        keywords = [
            'test', 'testing', 'qualification', 'certification',
            'validation', 'verification', 'inspection', 'audit',
            'demonstration', 'performance test', 'acceptance test'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in keywords:
                if keyword in line_lower and ('shall' in line_lower or 'must' in line_lower or 'required' in line_lower):
                    test_req = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'test_type': keyword,
                        'text': line.strip()[:300],
                        'frequency': self._extract_frequency(line)
                    }
                    
                    self.testing.append(test_req)
    
    def _extract_operational_requirements(self, doc_id, lines):
        """Extract operational requirements specific to ESR/BESS"""
        keywords = [
            'state of charge', 'soc', 'charging', 'discharging',
            'ramp rate', 'response time', 'availability',
            'telemetry', 'scada', 'dispatch', 'base point',
            'ancillary service', 'regulation', 'reserve',
            'efficiency', 'degradation', 'capacity'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in keywords:
                if keyword in line_lower and any(req in line_lower for req in ['shall', 'must', 'required']):
                    op_req = {
                        'doc_id': doc_id,
                        'section': self._get_section(doc_id),
                        'line_num': i + 1,
                        'topic': keyword,
                        'text': line.strip()[:300],
                        'category': 'operational'
                    }
                    
                    self.operational.append(op_req)
    
    def _get_section(self, doc_id):
        """Get section number from document ID"""
        match = re.match(r'^(\d+[A-Z]?)', doc_id)
        if match:
            return f"Section {match.group(1)}"
        return "Unknown"
    
    def _categorize_requirement(self, text):
        """Categorize requirement based on keywords"""
        text_lower = text.lower()
        
        categories = {
            'registration': ['register', 'registration', 'enroll'],
            'metering': ['meter', 'metering', 'eps', 'measurement'],
            'telemetry': ['telemetry', 'scada', 'rtu', 'iccp'],
            'ancillary_services': ['ancillary', 'regulation', 'reserve', 'rrs', 'ecrs'],
            'market_participation': ['bid', 'offer', 'dam', 'rtm', 'sced'],
            'compliance': ['comply', 'compliance', 'violation', 'penalty'],
            'testing': ['test', 'qualification', 'certification'],
            'operational': ['operate', 'dispatch', 'soc', 'charge', 'discharge'],
            'financial': ['payment', 'invoice', 'settlement', 'credit'],
            'reporting': ['report', 'submit', 'provide', 'notify'],
            'outage': ['outage', 'derate', 'unavailable'],
            'interconnection': ['interconnection', 'poi', 'transmission'],
            'data_submission': ['data', 'information', 'documentation']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _categorize_fee(self, text):
        """Categorize fee type"""
        text_lower = text.lower()
        
        if 'registration' in text_lower:
            return 'registration'
        elif 'test' in text_lower or 'qualification' in text_lower:
            return 'testing'
        elif 'study' in text_lower:
            return 'study'
        elif 'deposit' in text_lower:
            return 'deposit'
        elif 'penalty' in text_lower:
            return 'penalty'
        elif 'administrative' in text_lower:
            return 'administrative'
        else:
            return 'other'
    
    def _extract_frequency(self, text):
        """Extract frequency from text"""
        text_lower = text.lower()
        
        if 'annual' in text_lower:
            return 'annual'
        elif 'monthly' in text_lower:
            return 'monthly'
        elif 'quarterly' in text_lower:
            return 'quarterly'
        elif 'daily' in text_lower:
            return 'daily'
        elif 'one-time' in text_lower or 'initial' in text_lower:
            return 'one-time'
        else:
            return 'as-needed'
    
    def save_requirements_database(self):
        """Save all requirements to various formats"""
        print("\nSaving requirements database...")
        
        # Save as JSON
        self._save_json()
        
        # Save as CSV
        self._save_csv()
        
        # Save as Markdown
        self._save_markdown()
        
        print("Requirements database saved successfully!")
    
    def _save_json(self):
        """Save requirements as JSON"""
        json_data = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'total_requirements': len(self.requirements),
                'total_deadlines': len(self.deadlines),
                'total_forms': len(self.forms),
                'total_fees': len(self.fees),
                'total_testing': len(self.testing),
                'total_operational': len(self.operational)
            },
            'requirements': self.requirements,
            'deadlines': self.deadlines,
            'forms': self.forms,
            'fees': self.fees,
            'testing': self.testing,
            'operational': self.operational,
            'categories': self.categories
        }
        
        json_path = self.output_dir / "requirements_database.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"  JSON saved to: {json_path}")
    
    def _save_csv(self):
        """Save requirements as CSV files"""
        # Requirements CSV
        req_csv = self.output_dir / "requirements.csv"
        with open(req_csv, 'w', newline='') as f:
            if self.requirements:
                writer = csv.DictWriter(f, fieldnames=self.requirements[0].keys())
                writer.writeheader()
                writer.writerows(self.requirements)
        
        # Deadlines CSV
        deadline_csv = self.output_dir / "deadlines.csv"
        with open(deadline_csv, 'w', newline='') as f:
            if self.deadlines:
                writer = csv.DictWriter(f, fieldnames=self.deadlines[0].keys())
                writer.writeheader()
                writer.writerows(self.deadlines)
        
        # Forms CSV
        forms_csv = self.output_dir / "forms.csv"
        with open(forms_csv, 'w', newline='') as f:
            if self.forms:
                writer = csv.DictWriter(f, fieldnames=self.forms[0].keys())
                writer.writeheader()
                writer.writerows(self.forms)
        
        print(f"  CSV files saved to: {self.output_dir}")
    
    def _save_markdown(self):
        """Save requirements as formatted Markdown"""
        md_path = self.output_dir / "REQUIREMENTS_DATABASE.md"
        
        with open(md_path, 'w') as f:
            f.write("# ERCOT Requirements Database\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- Total Requirements: {len(self.requirements)}\n")
            f.write(f"- Total Deadlines: {len(self.deadlines)}\n")
            f.write(f"- Total Forms: {len(self.forms)}\n")
            f.write(f"- Total Fees: {len(self.fees)}\n")
            f.write(f"- Testing Requirements: {len(self.testing)}\n")
            f.write(f"- Operational Requirements: {len(self.operational)}\n\n")
            
            # Requirements by Category
            f.write("## Requirements by Category\n\n")
            for category, reqs in self.categories.items():
                if reqs:
                    f.write(f"### {category.replace('_', ' ').title()} ({len(reqs)} requirements)\n\n")
                    
                    # Show first 5 requirements
                    for req in reqs[:5]:
                        f.write(f"- **{req['type']}** ({req['doc_id']}, line {req['line_num']})\n")
                        f.write(f"  {req['text'][:150]}...\n\n")
                    
                    if len(reqs) > 5:
                        f.write(f"  *... and {len(reqs) - 5} more*\n\n")
            
            # Critical Deadlines
            f.write("## Critical Deadlines\n\n")
            
            # Group deadlines by type
            deadline_types = defaultdict(list)
            for deadline in self.deadlines:
                deadline_types[deadline['type']].append(deadline)
            
            for dtype, items in sorted(deadline_types.items()):
                f.write(f"### {dtype} ({len(items)} deadlines)\n\n")
                
                # Show examples
                for item in items[:3]:
                    f.write(f"- {item['text']} ({item['doc_id']})\n")
                
                if len(items) > 3:
                    f.write(f"  *... and {len(items) - 3} more*\n")
                f.write("\n")
            
            # Forms and Documents
            f.write("## Forms and Documents Required\n\n")
            
            # Get unique forms
            unique_forms = {}
            for form in self.forms:
                form_key = f"{form['form_type']} {form['form_id']}"
                if form_key not in unique_forms:
                    unique_forms[form_key] = form
            
            f.write(f"Total unique forms: {len(unique_forms)}\n\n")
            
            for form_key in sorted(unique_forms.keys())[:20]:
                form = unique_forms[form_key]
                f.write(f"- **{form_key}** ({form['doc_id']})\n")
            
            if len(unique_forms) > 20:
                f.write(f"\n*... and {len(unique_forms) - 20} more forms*\n")
            
            # Fee Schedule
            f.write("\n## Fee Schedule\n\n")
            
            # Group fees by type
            fee_types = defaultdict(list)
            for fee in self.fees:
                fee_types[fee['fee_type']].append(fee)
            
            for ftype, items in sorted(fee_types.items()):
                f.write(f"### {ftype.title()} Fees\n\n")
                
                # Show examples
                for item in items[:5]:
                    f.write(f"- {item['amount']} - {item['context'][:100]}... ({item['doc_id']})\n")
                
                if len(items) > 5:
                    f.write(f"  *... and {len(items) - 5} more*\n")
                f.write("\n")
            
            # Testing Requirements
            f.write("## Testing Requirements\n\n")
            
            # Group by test type
            test_types = defaultdict(list)
            for test in self.testing:
                test_types[test['test_type']].append(test)
            
            for ttype, items in sorted(test_types.items()):
                f.write(f"### {ttype.title()} ({len(items)} requirements)\n\n")
                
                # Show examples
                for item in items[:3]:
                    f.write(f"- {item['text'][:150]}... ({item['doc_id']})\n")
                
                if len(items) > 3:
                    f.write(f"  *... and {len(items) - 3} more*\n")
                f.write("\n")
            
            # ESR/BESS Specific Requirements
            f.write("## ESR/BESS Specific Requirements\n\n")
            
            # Filter operational requirements for ESR/BESS
            esr_keywords = ['soc', 'state of charge', 'charging', 'discharging', 
                           'battery', 'storage', 'esr', 'bess', 'wsl']
            
            esr_reqs = [op for op in self.operational 
                       if any(kw in op['text'].lower() for kw in esr_keywords)]
            
            f.write(f"Total ESR/BESS specific requirements: {len(esr_reqs)}\n\n")
            
            # Group by topic
            topic_groups = defaultdict(list)
            for req in esr_reqs:
                topic_groups[req['topic']].append(req)
            
            for topic, items in sorted(topic_groups.items()):
                f.write(f"### {topic.title()} ({len(items)} requirements)\n\n")
                
                for item in items[:3]:
                    f.write(f"- {item['text'][:150]}... ({item['doc_id']})\n")
                
                if len(items) > 3:
                    f.write(f"  *... and {len(items) - 3} more*\n")
                f.write("\n")
        
        print(f"  Markdown saved to: {md_path}")
    
    def generate_compliance_checklist(self):
        """Generate a compliance checklist for ESR/BESS operators"""
        checklist_path = self.output_dir / "ESR_COMPLIANCE_CHECKLIST.md"
        
        with open(checklist_path, 'w') as f:
            f.write("# ESR/BESS Compliance Checklist\n\n")
            f.write(f"Generated from ERCOT Nodal Protocols\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            
            # Registration Requirements
            f.write("## Registration Requirements\n\n")
            reg_reqs = [r for r in self.requirements if r['category'] == 'registration'][:10]
            for req in reg_reqs:
                f.write(f"- [ ] {req['text'][:200]} ({req['doc_id']})\n")
            
            # Metering Requirements
            f.write("\n## Metering Requirements\n\n")
            meter_reqs = [r for r in self.requirements if r['category'] == 'metering'][:10]
            for req in meter_reqs:
                f.write(f"- [ ] {req['text'][:200]} ({req['doc_id']})\n")
            
            # Telemetry Requirements
            f.write("\n## Telemetry Requirements\n\n")
            telem_reqs = [r for r in self.requirements if r['category'] == 'telemetry'][:10]
            for req in telem_reqs:
                f.write(f"- [ ] {req['text'][:200]} ({req['doc_id']})\n")
            
            # Testing Requirements
            f.write("\n## Testing Requirements\n\n")
            test_reqs = self.testing[:10]
            for req in test_reqs:
                f.write(f"- [ ] {req['text'][:200]} ({req['doc_id']})\n")
            
            # Reporting Deadlines
            f.write("\n## Reporting Deadlines\n\n")
            report_deadlines = [d for d in self.deadlines if 'report' in d['context'].lower()][:10]
            for deadline in report_deadlines:
                f.write(f"- [ ] {deadline['text']}: {deadline['context'][:150]} ({deadline['doc_id']})\n")
            
            # Forms to Submit
            f.write("\n## Forms to Submit\n\n")
            submit_forms = [f for f in self.forms if f['submission_required']][:15]
            for form in submit_forms:
                f.write(f"- [ ] {form['form_type']} {form['form_id']} ({form['doc_id']})\n")
            
            # Operational Requirements
            f.write("\n## Operational Requirements\n\n")
            op_reqs = self.operational[:10]
            for req in op_reqs:
                f.write(f"- [ ] {req['text'][:200]} ({req['doc_id']})\n")
        
        print(f"  Compliance checklist saved to: {checklist_path}")
        return str(checklist_path)


def main():
    """Main function"""
    print("=" * 60)
    print("ERCOT Requirements Database Extractor")
    print("=" * 60)
    
    base_dir = "/pool/ssd8tb/data/iso/ERCOT/market_rules/nodal_protocols/"
    extractor = RequirementsExtractor(base_dir)
    
    # Extract all requirements
    extractor.extract_all_requirements()
    
    # Save the database
    extractor.save_requirements_database()
    
    # Generate compliance checklist
    extractor.generate_compliance_checklist()
    
    print("\n" + "=" * 60)
    print("Requirements extraction complete!")
    print("=" * 60)
    
    # Print summary statistics
    print("\nSummary by Category:")
    for category, reqs in extractor.categories.items():
        if reqs:
            print(f"  {category.replace('_', ' ').title()}: {len(reqs)}")
    
    print("\nFiles created:")
    print(f"  - requirements_database/requirements_database.json")
    print(f"  - requirements_database/requirements.csv")
    print(f"  - requirements_database/deadlines.csv")
    print(f"  - requirements_database/forms.csv")
    print(f"  - requirements_database/REQUIREMENTS_DATABASE.md")
    print(f"  - requirements_database/ESR_COMPLIANCE_CHECKLIST.md")


if __name__ == "__main__":
    main()