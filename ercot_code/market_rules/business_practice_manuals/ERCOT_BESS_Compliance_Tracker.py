#!/usr/bin/env python3
"""
ERCOT BESS Compliance Tracking and Reporting System
Version 1.0 - August 2025

Automated compliance monitoring, tracking, and reporting for BESS operations
Tracks all ERCOT requirements, deadlines, and performance metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging
from enum import Enum
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BESS_Compliance')


class ComplianceStatus(Enum):
    """Compliance status categories"""
    COMPLIANT = "Compliant"
    WARNING = "Warning"
    NON_COMPLIANT = "Non-Compliant"
    PENDING = "Pending"
    NOT_APPLICABLE = "N/A"


class ComplianceCategory(Enum):
    """Main compliance categories"""
    TELEMETRY = "Telemetry"
    MARKET = "Market Operations"
    PERFORMANCE = "Performance Standards"
    REPORTING = "Reporting Requirements"
    TESTING = "Testing & Validation"
    DOCUMENTATION = "Documentation"
    SAFETY = "Safety & Emergency"


class BESSComplianceTracker:
    """
    Main compliance tracking system for BESS operations in ERCOT
    """
    
    def __init__(self, resource_name: str, capacity_mw: float, capacity_mwh: float):
        self.resource_name = resource_name
        self.capacity_mw = capacity_mw
        self.capacity_mwh = capacity_mwh
        self.compliance_records = []
        self.performance_metrics = {}
        self.upcoming_deadlines = []
        self.violations = []
        
        # Initialize compliance requirements
        self._initialize_requirements()
        
    def _initialize_requirements(self):
        """Initialize all ERCOT compliance requirements"""
        self.requirements = {
            'telemetry': {
                'availability_target': 0.995,  # 99.5%
                'scan_rate': 2,  # seconds
                'required_points': [
                    'MW_output', 'MVAR_output', 'Voltage', 'Frequency',
                    'SOC_current', 'SOC_min', 'SOC_max', 'Status'
                ]
            },
            'cop': {
                'submission_deadline': '14:00',  # 2 PM daily
                'update_window': 60,  # minutes for changes
                'forecast_days': 7
            },
            'performance': {
                'dispatch_compliance': 0.95,  # 95%
                'ramp_rate_accuracy': 0.95,  # Within 5% of stated
                'regulation_score': 0.75,  # 75% minimum
                'availability_factor': 0.95  # 95% excluding planned outages
            },
            'testing': {
                'capacity_test': {'frequency': 'annual', 'notice': 30},
                'as_qualification': {'frequency': 'semi-annual', 'notice': 14},
                'black_start': {'frequency': 'quarterly', 'notice': 7},
                'telemetry_check': {'frequency': 'monthly', 'notice': 0}
            },
            'reporting': {
                'outage_notification': {'immediate': 1, 'follow_up': 60},
                'meter_data': {'deadline': '12:00', 'day_after': True},
                'compliance_report': {'frequency': 'monthly', 'deadline': 5},
                'incident_report': {'deadline': 24}  # hours
            }
        }
    
    def check_telemetry_compliance(self, telemetry_data: Dict) -> Dict:
        """
        Check telemetry system compliance
        
        Parameters:
        -----------
        telemetry_data : dict
            Current telemetry statistics
        """
        results = {
            'category': ComplianceCategory.TELEMETRY,
            'timestamp': datetime.now(),
            'checks': []
        }
        
        # Check availability
        availability = telemetry_data.get('availability', 0)
        target = self.requirements['telemetry']['availability_target']
        
        if availability >= target:
            status = ComplianceStatus.COMPLIANT
        elif availability >= target * 0.98:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'Telemetry Availability',
            'value': f"{availability:.3%}",
            'target': f"{target:.3%}",
            'status': status.value
        })
        
        # Check scan rate
        scan_rate = telemetry_data.get('scan_rate', 999)
        if scan_rate <= self.requirements['telemetry']['scan_rate']:
            status = ComplianceStatus.COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'Scan Rate',
            'value': f"{scan_rate} seconds",
            'target': f"{self.requirements['telemetry']['scan_rate']} seconds",
            'status': status.value
        })
        
        # Check required points
        missing_points = []
        for point in self.requirements['telemetry']['required_points']:
            if not telemetry_data.get('points', {}).get(point, False):
                missing_points.append(point)
        
        if not missing_points:
            status = ComplianceStatus.COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'Required Telemetry Points',
            'value': f"{len(missing_points)} missing",
            'details': missing_points,
            'status': status.value
        })
        
        # Overall status
        statuses = [check['status'] for check in results['checks']]
        if ComplianceStatus.NON_COMPLIANT.value in statuses:
            results['overall_status'] = ComplianceStatus.NON_COMPLIANT.value
        elif ComplianceStatus.WARNING.value in statuses:
            results['overall_status'] = ComplianceStatus.WARNING.value
        else:
            results['overall_status'] = ComplianceStatus.COMPLIANT.value
        
        self.compliance_records.append(results)
        return results
    
    def check_cop_compliance(self, cop_data: Dict) -> Dict:
        """
        Check Current Operating Plan compliance
        """
        results = {
            'category': ComplianceCategory.MARKET,
            'timestamp': datetime.now(),
            'checks': []
        }
        
        # Check submission time
        submission_time = cop_data.get('submission_time')
        deadline = datetime.strptime(self.requirements['cop']['submission_deadline'], '%H:%M').time()
        
        if submission_time and submission_time.time() <= deadline:
            status = ComplianceStatus.COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'COP Submission Time',
            'value': str(submission_time.time()) if submission_time else 'Not Submitted',
            'target': str(deadline),
            'status': status.value
        })
        
        # Check SOC feasibility
        soc_errors = cop_data.get('soc_feasibility_errors', [])
        if not soc_errors:
            status = ComplianceStatus.COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'SOC Feasibility',
            'value': f"{len(soc_errors)} errors",
            'details': soc_errors[:5],  # First 5 errors
            'status': status.value
        })
        
        # Check update timeliness
        capability_changes = cop_data.get('capability_changes', [])
        late_updates = 0
        
        for change in capability_changes:
            update_time = change.get('update_minutes', 999)
            if update_time > self.requirements['cop']['update_window']:
                late_updates += 1
        
        if late_updates == 0:
            status = ComplianceStatus.COMPLIANT
        elif late_updates <= 2:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'COP Update Timeliness',
            'value': f"{late_updates} late updates",
            'target': f"Within {self.requirements['cop']['update_window']} minutes",
            'status': status.value
        })
        
        # Overall status
        statuses = [check['status'] for check in results['checks']]
        if ComplianceStatus.NON_COMPLIANT.value in statuses:
            results['overall_status'] = ComplianceStatus.NON_COMPLIANT.value
        elif ComplianceStatus.WARNING.value in statuses:
            results['overall_status'] = ComplianceStatus.WARNING.value
        else:
            results['overall_status'] = ComplianceStatus.COMPLIANT.value
        
        self.compliance_records.append(results)
        return results
    
    def check_performance_compliance(self, performance_data: Dict) -> Dict:
        """
        Check performance standards compliance
        """
        results = {
            'category': ComplianceCategory.PERFORMANCE,
            'timestamp': datetime.now(),
            'checks': []
        }
        
        # Dispatch compliance
        dispatch_compliance = performance_data.get('dispatch_compliance', 0)
        target = self.requirements['performance']['dispatch_compliance']
        
        if dispatch_compliance >= target:
            status = ComplianceStatus.COMPLIANT
        elif dispatch_compliance >= target * 0.95:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'Dispatch Compliance',
            'value': f"{dispatch_compliance:.2%}",
            'target': f"{target:.2%}",
            'status': status.value
        })
        
        # Regulation performance score
        if 'regulation_score' in performance_data:
            reg_score = performance_data['regulation_score']
            target = self.requirements['performance']['regulation_score']
            
            if reg_score >= target:
                status = ComplianceStatus.COMPLIANT
            elif reg_score >= target * 0.95:
                status = ComplianceStatus.WARNING
            else:
                status = ComplianceStatus.NON_COMPLIANT
                
            results['checks'].append({
                'item': 'Regulation Performance Score',
                'value': f"{reg_score:.2%}",
                'target': f"{target:.2%}",
                'status': status.value
            })
        
        # Availability factor
        availability = performance_data.get('availability_factor', 0)
        target = self.requirements['performance']['availability_factor']
        
        if availability >= target:
            status = ComplianceStatus.COMPLIANT
        elif availability >= target * 0.98:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        results['checks'].append({
            'item': 'Availability Factor',
            'value': f"{availability:.2%}",
            'target': f"{target:.2%}",
            'status': status.value
        })
        
        # Overall status
        statuses = [check['status'] for check in results['checks']]
        if ComplianceStatus.NON_COMPLIANT.value in statuses:
            results['overall_status'] = ComplianceStatus.NON_COMPLIANT.value
        elif ComplianceStatus.WARNING.value in statuses:
            results['overall_status'] = ComplianceStatus.WARNING.value
        else:
            results['overall_status'] = ComplianceStatus.COMPLIANT.value
        
        self.compliance_records.append(results)
        return results
    
    def track_testing_requirements(self) -> List[Dict]:
        """
        Track upcoming testing requirements and deadlines
        """
        upcoming_tests = []
        current_date = datetime.now()
        
        for test_type, requirements in self.requirements['testing'].items():
            # Calculate next test date based on frequency
            if requirements['frequency'] == 'annual':
                next_date = current_date + timedelta(days=365)
            elif requirements['frequency'] == 'semi-annual':
                next_date = current_date + timedelta(days=180)
            elif requirements['frequency'] == 'quarterly':
                next_date = current_date + timedelta(days=90)
            elif requirements['frequency'] == 'monthly':
                next_date = current_date + timedelta(days=30)
            else:
                continue
            
            # Calculate notification date
            notification_date = next_date - timedelta(days=requirements['notice'])
            
            upcoming_tests.append({
                'test_type': test_type,
                'next_test_date': next_date,
                'notification_date': notification_date,
                'days_until_test': (next_date - current_date).days,
                'status': 'Scheduled' if notification_date > current_date else 'Notice Required'
            })
        
        self.upcoming_deadlines = sorted(upcoming_tests, key=lambda x: x['next_test_date'])
        return self.upcoming_deadlines
    
    def log_violation(self, violation_type: str, description: str, 
                     severity: str = 'Medium') -> Dict:
        """
        Log a compliance violation
        
        Parameters:
        -----------
        violation_type : str
            Type of violation
        description : str
            Description of the violation
        severity : str
            'Low', 'Medium', 'High', 'Critical'
        """
        violation = {
            'id': len(self.violations) + 1,
            'timestamp': datetime.now(),
            'type': violation_type,
            'description': description,
            'severity': severity,
            'status': 'Open',
            'resolution': None,
            'resolution_date': None
        }
        
        self.violations.append(violation)
        logger.warning(f"Compliance violation logged: {violation_type} - {description}")
        
        # Send alert if high or critical
        if severity in ['High', 'Critical']:
            self._send_compliance_alert(violation)
        
        return violation
    
    def resolve_violation(self, violation_id: int, resolution: str) -> bool:
        """
        Mark a violation as resolved
        """
        for violation in self.violations:
            if violation['id'] == violation_id:
                violation['status'] = 'Resolved'
                violation['resolution'] = resolution
                violation['resolution_date'] = datetime.now()
                logger.info(f"Violation {violation_id} resolved: {resolution}")
                return True
        return False
    
    def _send_compliance_alert(self, violation: Dict):
        """
        Send alert for critical compliance issues
        """
        alert = {
            'resource': self.resource_name,
            'timestamp': violation['timestamp'],
            'alert_type': 'Compliance Violation',
            'severity': violation['severity'],
            'description': violation['description'],
            'required_action': 'Immediate attention required'
        }
        
        # In production, this would send email/SMS/system alerts
        logger.critical(f"COMPLIANCE ALERT: {alert}")
        
    def generate_compliance_report(self, period_days: int = 30) -> Dict:
        """
        Generate comprehensive compliance report
        
        Parameters:
        -----------
        period_days : int
            Number of days to include in report
        """
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        # Filter records for period
        period_records = [
            r for r in self.compliance_records 
            if r['timestamp'] >= cutoff_date
        ]
        
        # Calculate compliance rates by category
        compliance_by_category = {}
        for category in ComplianceCategory:
            category_records = [
                r for r in period_records 
                if r['category'] == category
            ]
            
            if category_records:
                compliant = sum(1 for r in category_records 
                              if r['overall_status'] == ComplianceStatus.COMPLIANT.value)
                total = len(category_records)
                compliance_by_category[category.value] = {
                    'rate': compliant / total if total > 0 else 0,
                    'compliant': compliant,
                    'total': total
                }
        
        # Count violations
        period_violations = [
            v for v in self.violations 
            if v['timestamp'] >= cutoff_date
        ]
        
        open_violations = [v for v in period_violations if v['status'] == 'Open']
        
        # Generate report
        report = {
            'resource': self.resource_name,
            'capacity': f"{self.capacity_mw} MW / {self.capacity_mwh} MWh",
            'report_date': datetime.now().isoformat(),
            'period': f"{period_days} days",
            'overall_compliance_rate': self._calculate_overall_compliance_rate(period_records),
            'compliance_by_category': compliance_by_category,
            'violations': {
                'total': len(period_violations),
                'open': len(open_violations),
                'resolved': len(period_violations) - len(open_violations),
                'by_severity': self._count_violations_by_severity(period_violations)
            },
            'upcoming_requirements': self.track_testing_requirements()[:5],
            'recommendations': self._generate_recommendations(period_records, period_violations)
        }
        
        return report
    
    def _calculate_overall_compliance_rate(self, records: List[Dict]) -> float:
        """Calculate overall compliance rate"""
        if not records:
            return 1.0
        
        compliant = sum(1 for r in records 
                       if r['overall_status'] == ComplianceStatus.COMPLIANT.value)
        return compliant / len(records) if records else 1.0
    
    def _count_violations_by_severity(self, violations: List[Dict]) -> Dict:
        """Count violations by severity level"""
        severity_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for v in violations:
            severity = v.get('severity', 'Medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts
    
    def _generate_recommendations(self, records: List[Dict], 
                                 violations: List[Dict]) -> List[str]:
        """Generate recommendations based on compliance data"""
        recommendations = []
        
        # Check telemetry compliance
        telemetry_records = [r for r in records 
                            if r['category'] == ComplianceCategory.TELEMETRY]
        if telemetry_records:
            telemetry_rate = self._calculate_overall_compliance_rate(telemetry_records)
            if telemetry_rate < 0.95:
                recommendations.append(
                    "Improve telemetry system reliability - current compliance below 95%"
                )
        
        # Check for repeated violations
        violation_types = {}
        for v in violations:
            vtype = v.get('type', 'Unknown')
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        for vtype, count in violation_types.items():
            if count >= 3:
                recommendations.append(
                    f"Address recurring {vtype} violations - {count} occurrences in period"
                )
        
        # Check upcoming deadlines
        upcoming = self.track_testing_requirements()
        urgent_tests = [t for t in upcoming if t['days_until_test'] <= 30]
        if urgent_tests:
            recommendations.append(
                f"Prepare for {len(urgent_tests)} upcoming tests within 30 days"
            )
        
        return recommendations if recommendations else ["All systems operating within compliance parameters"]


class PerformanceMonitor:
    """
    Monitor and track BESS performance metrics for compliance
    """
    
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.performance_data = []
        
    def track_dispatch_compliance(self, base_point: float, actual: float, 
                                 timestamp: datetime) -> Dict:
        """
        Track dispatch instruction compliance
        """
        tolerance = 0.05  # 5% or 5 MW tolerance
        tolerance_mw = max(5, abs(base_point) * tolerance)
        
        deviation = abs(actual - base_point)
        compliant = deviation <= tolerance_mw
        
        record = {
            'timestamp': timestamp,
            'base_point': base_point,
            'actual': actual,
            'deviation': deviation,
            'tolerance': tolerance_mw,
            'compliant': compliant
        }
        
        self.performance_data.append(record)
        return record
    
    def calculate_metrics(self, period_hours: int = 24) -> Dict:
        """
        Calculate performance metrics over specified period
        """
        cutoff_time = datetime.now() - timedelta(hours=period_hours)
        period_data = [d for d in self.performance_data 
                      if d['timestamp'] >= cutoff_time]
        
        if not period_data:
            return {
                'dispatch_compliance': 1.0,
                'average_deviation': 0,
                'max_deviation': 0,
                'data_points': 0
            }
        
        compliant_count = sum(1 for d in period_data if d['compliant'])
        total_count = len(period_data)
        
        deviations = [d['deviation'] for d in period_data]
        
        return {
            'dispatch_compliance': compliant_count / total_count if total_count > 0 else 1.0,
            'average_deviation': np.mean(deviations) if deviations else 0,
            'max_deviation': np.max(deviations) if deviations else 0,
            'data_points': total_count
        }


class COPValidator:
    """
    Validate Current Operating Plan submissions for compliance
    """
    
    def __init__(self, capacity_mw: float, capacity_mwh: float):
        self.hsl = capacity_mw  # High Sustained Limit
        self.lsl = -capacity_mw  # Low Sustained Limit (charging)
        self.max_soc = capacity_mwh
        self.min_soc = 0
        
    def validate_cop(self, cop_data: pd.DataFrame) -> Dict:
        """
        Validate COP data for ERCOT compliance
        
        Parameters:
        -----------
        cop_data : DataFrame
            COP data with columns: hour, hsl, lsl, soc_begin, soc_min, soc_max
        """
        errors = []
        warnings = []
        
        for i in range(len(cop_data) - 1):
            hour = cop_data.iloc[i]
            next_hour = cop_data.iloc[i + 1]
            
            # Check SOC feasibility
            max_discharge = min(hour['hsl'], hour['soc_begin'] - hour['soc_min'])
            max_charge = min(abs(hour['lsl']), hour['soc_max'] - hour['soc_begin'])
            
            soc_change = next_hour['soc_begin'] - hour['soc_begin']
            
            if soc_change > max_charge:
                errors.append({
                    'hour': i,
                    'type': 'SOC Infeasible',
                    'message': f"Cannot charge {soc_change:.1f} MWh in one hour (max: {max_charge:.1f})"
                })
            elif soc_change < -max_discharge:
                errors.append({
                    'hour': i,
                    'type': 'SOC Infeasible',
                    'message': f"Cannot discharge {-soc_change:.1f} MWh in one hour (max: {max_discharge:.1f})"
                })
            
            # Check SOC bounds
            if hour['soc_begin'] < self.min_soc:
                errors.append({
                    'hour': i,
                    'type': 'SOC Below Minimum',
                    'message': f"SOC {hour['soc_begin']:.1f} below minimum {self.min_soc}"
                })
            elif hour['soc_begin'] > self.max_soc:
                errors.append({
                    'hour': i,
                    'type': 'SOC Above Maximum',
                    'message': f"SOC {hour['soc_begin']:.1f} above maximum {self.max_soc}"
                })
            
            # Check HSL/LSL consistency
            if hour['hsl'] > self.hsl:
                warnings.append({
                    'hour': i,
                    'type': 'HSL Exceeds Capability',
                    'message': f"HSL {hour['hsl']:.1f} exceeds registered {self.hsl:.1f}"
                })
            if hour['lsl'] < self.lsl:
                warnings.append({
                    'hour': i,
                    'type': 'LSL Exceeds Capability',
                    'message': f"LSL {hour['lsl']:.1f} exceeds registered {self.lsl:.1f}"
                })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize compliance tracker
    tracker = BESSComplianceTracker(
        resource_name="BESS_WEST_100MW",
        capacity_mw=100,
        capacity_mwh=200
    )
    
    # Test telemetry compliance
    telemetry_data = {
        'availability': 0.996,
        'scan_rate': 2,
        'points': {
            'MW_output': True,
            'MVAR_output': True,
            'Voltage': True,
            'Frequency': True,
            'SOC_current': True,
            'SOC_min': True,
            'SOC_max': True,
            'Status': True
        }
    }
    
    telemetry_result = tracker.check_telemetry_compliance(telemetry_data)
    print("\n=== Telemetry Compliance Check ===")
    print(f"Overall Status: {telemetry_result['overall_status']}")
    for check in telemetry_result['checks']:
        print(f"  {check['item']}: {check['status']} ({check['value']})")
    
    # Test COP compliance
    cop_data = {
        'submission_time': datetime.now().replace(hour=13, minute=45),
        'soc_feasibility_errors': [],
        'capability_changes': [
            {'update_minutes': 45},
            {'update_minutes': 58}
        ]
    }
    
    cop_result = tracker.check_cop_compliance(cop_data)
    print("\n=== COP Compliance Check ===")
    print(f"Overall Status: {cop_result['overall_status']}")
    for check in cop_result['checks']:
        print(f"  {check['item']}: {check['status']} ({check['value']})")
    
    # Test performance compliance
    performance_data = {
        'dispatch_compliance': 0.97,
        'regulation_score': 0.82,
        'availability_factor': 0.96
    }
    
    performance_result = tracker.check_performance_compliance(performance_data)
    print("\n=== Performance Compliance Check ===")
    print(f"Overall Status: {performance_result['overall_status']}")
    for check in performance_result['checks']:
        print(f"  {check['item']}: {check['status']} ({check['value']})")
    
    # Track testing requirements
    print("\n=== Upcoming Testing Requirements ===")
    upcoming_tests = tracker.track_testing_requirements()
    for test in upcoming_tests[:3]:
        print(f"  {test['test_type']}: Due in {test['days_until_test']} days ({test['status']})")
    
    # Log a violation
    tracker.log_violation(
        violation_type="COP Submission",
        description="COP submitted 15 minutes late",
        severity="Medium"
    )
    
    # Generate compliance report
    report = tracker.generate_compliance_report(period_days=30)
    print("\n=== Compliance Report Summary ===")
    print(f"Resource: {report['resource']}")
    print(f"Overall Compliance Rate: {report['overall_compliance_rate']:.1%}")
    print(f"Open Violations: {report['violations']['open']}")
    print("Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # Test COP Validator
    print("\n=== COP Validation Test ===")
    validator = COPValidator(capacity_mw=100, capacity_mwh=200)
    
    # Create sample COP data
    cop_df = pd.DataFrame({
        'hour': range(24),
        'hsl': [100] * 24,
        'lsl': [-100] * 24,
        'soc_begin': [100, 75, 50, 75, 100, 100, 75, 50, 50, 75, 
                     100, 125, 150, 175, 200, 175, 150, 125, 100, 
                     75, 50, 75, 100, 100],
        'soc_min': [0] * 24,
        'soc_max': [200] * 24
    })
    
    validation_result = validator.validate_cop(cop_df)
    print(f"COP Valid: {validation_result['valid']}")
    print(f"Errors: {validation_result['error_count']}")
    print(f"Warnings: {validation_result['warning_count']}")
    
    if validation_result['errors']:
        print("First error:", validation_result['errors'][0])
    
    print("\n=== Compliance Tracking System Initialized ===")
    print("Ready to monitor BESS compliance with ERCOT requirements")