#!/usr/bin/env python3
"""
ERCOT BESS COP Automation and Validation System
Version 1.0 - August 2025

Automated Current Operating Plan (COP) generation, validation, and submission
Ensures compliance with ERCOT requirements and SOC feasibility
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import requests
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('COP_Automation')


class ResourceStatus(Enum):
    """ERCOT Resource Status Codes"""
    ON = "ON"  # Online and dispatchable
    OFF = "OFF"  # Offline
    ONTEST = "ONTEST"  # Testing
    ONREG = "ONREG"  # Providing Regulation
    ONRR = "ONRR"  # Providing Responsive Reserve
    ONECRS = "ONECRS"  # Providing ECRS
    OFFNS = "OFFNS"  # Offline Non-Spin
    OFFQS = "OFFQS"  # Offline Quick Start
    OUT = "OUT"  # Forced Outage
    STARTUP = "STARTUP"  # Starting up
    SHUTDOWN = "SHUTDOWN"  # Shutting down
    ONEMR = "ONEMR"  # Emergency run


@dataclass
class BESSParameters:
    """BESS technical parameters"""
    resource_name: str
    capacity_mw: float  # Nameplate MW
    capacity_mwh: float  # Nameplate MWh
    efficiency: float  # Round-trip efficiency
    ramp_rate_up: float  # MW/min
    ramp_rate_down: float  # MW/min
    min_soc: float  # Minimum SOC (MWh)
    max_soc: float  # Maximum SOC (MWh)
    aux_load: float  # Auxiliary load (MW)
    
    @property
    def hsl(self) -> float:
        """High Sustained Limit"""
        return self.capacity_mw
    
    @property
    def lsl(self) -> float:
        """Low Sustained Limit (negative for charging)"""
        return -self.capacity_mw
    
    @property
    def duration(self) -> float:
        """Duration in hours"""
        return self.capacity_mwh / self.capacity_mw


class COPGenerator:
    """
    Generate optimized Current Operating Plan for BESS
    """
    
    def __init__(self, bess_params: BESSParameters):
        self.bess = bess_params
        self.cop_data = None
        
    def generate_cop(self, 
                     start_date: datetime,
                     days: int = 7,
                     price_forecast: Optional[pd.DataFrame] = None,
                     as_commitments: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Generate COP for specified period
        
        Parameters:
        -----------
        start_date : datetime
            Start date for COP
        days : int
            Number of days to generate (default 7)
        price_forecast : DataFrame
            Optional price forecast for optimization
        as_commitments : DataFrame
            Optional AS commitments to honor
        
        Returns:
        --------
        DataFrame with COP data
        """
        
        # Generate hourly timestamps
        hours = pd.date_range(
            start=start_date,
            periods=days * 24,
            freq='H'
        )
        
        # Initialize COP DataFrame
        cop = pd.DataFrame(index=hours)
        cop['hour_ending'] = cop.index
        cop['resource_name'] = self.bess.resource_name
        
        # Generate operational plan
        if price_forecast is not None:
            cop = self._optimize_for_prices(cop, price_forecast)
        else:
            cop = self._generate_default_plan(cop)
        
        # Apply AS commitments if provided
        if as_commitments is not None:
            cop = self._apply_as_commitments(cop, as_commitments)
        
        # Validate and adjust for feasibility
        cop = self._ensure_soc_feasibility(cop)
        
        # Add required COP fields
        cop = self._add_cop_fields(cop)
        
        self.cop_data = cop
        return cop
    
    def _generate_default_plan(self, cop: pd.DataFrame) -> pd.DataFrame:
        """
        Generate default operational plan (1.5 cycles per day)
        """
        cop['status'] = ResourceStatus.ON.value
        cop['hsl'] = self.bess.hsl
        cop['lsl'] = self.bess.lsl
        cop['soc_begin'] = self.bess.max_soc * 0.5  # Start at 50%
        
        # Default pattern: charge at night, discharge during day
        for i, hour in enumerate(cop.index):
            hour_of_day = hour.hour
            
            if 0 <= hour_of_day < 6:  # Night - charge
                cop.loc[hour, 'mode'] = 'charge'
                cop.loc[hour, 'target_mw'] = self.bess.lsl * 0.8
            elif 6 <= hour_of_day < 10:  # Morning - hold
                cop.loc[hour, 'mode'] = 'hold'
                cop.loc[hour, 'target_mw'] = 0
            elif 14 <= hour_of_day < 20:  # Afternoon peak - discharge
                cop.loc[hour, 'mode'] = 'discharge'
                cop.loc[hour, 'target_mw'] = self.bess.hsl * 0.9
            else:  # Other hours - hold
                cop.loc[hour, 'mode'] = 'hold'
                cop.loc[hour, 'target_mw'] = 0
        
        # Calculate SOC trajectory
        cop = self._calculate_soc_trajectory(cop)
        
        return cop
    
    def _optimize_for_prices(self, cop: pd.DataFrame, 
                           price_forecast: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize COP based on price forecast
        """
        cop['status'] = ResourceStatus.ON.value
        cop['hsl'] = self.bess.hsl
        cop['lsl'] = self.bess.lsl
        
        # Merge price forecast
        cop = cop.merge(price_forecast, left_index=True, right_index=True, how='left')
        
        # Simple threshold-based optimization
        for hour in cop.index:
            price = cop.loc[hour, 'price'] if 'price' in cop.columns else 50
            
            if price > 80:  # High price - discharge
                cop.loc[hour, 'mode'] = 'discharge'
                cop.loc[hour, 'target_mw'] = self.bess.hsl
            elif price < 25:  # Low price - charge
                cop.loc[hour, 'mode'] = 'charge'
                cop.loc[hour, 'target_mw'] = self.bess.lsl
            elif price > 50:  # Medium-high - partial discharge
                cop.loc[hour, 'mode'] = 'discharge'
                cop.loc[hour, 'target_mw'] = self.bess.hsl * 0.5
            else:  # Hold
                cop.loc[hour, 'mode'] = 'hold'
                cop.loc[hour, 'target_mw'] = 0
        
        # Calculate SOC trajectory
        cop = self._calculate_soc_trajectory(cop)
        
        return cop
    
    def _calculate_soc_trajectory(self, cop: pd.DataFrame, 
                                 initial_soc: Optional[float] = None) -> pd.DataFrame:
        """
        Calculate SOC trajectory based on charge/discharge plan
        """
        if initial_soc is None:
            initial_soc = self.bess.max_soc * 0.5  # Default 50%
        
        cop['soc_begin'] = initial_soc
        
        for i in range(len(cop)):
            if i > 0:
                # Previous hour's ending SOC becomes this hour's beginning SOC
                prev_target = cop.iloc[i-1]['target_mw']
                
                if prev_target > 0:  # Discharging
                    soc_change = -prev_target  # MWh discharged
                elif prev_target < 0:  # Charging
                    soc_change = -prev_target * self.bess.efficiency  # MWh charged
                else:  # Holding
                    soc_change = 0
                
                cop.iloc[i, cop.columns.get_loc('soc_begin')] = (
                    cop.iloc[i-1]['soc_begin'] + soc_change
                )
        
        # Set min/max SOC bounds
        cop['soc_min'] = cop['soc_begin'].apply(
            lambda x: max(self.bess.min_soc, x - self.bess.hsl)
        )
        cop['soc_max'] = cop['soc_begin'].apply(
            lambda x: min(self.bess.max_soc, x + abs(self.bess.lsl) * self.bess.efficiency)
        )
        
        return cop
    
    def _ensure_soc_feasibility(self, cop: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure SOC transitions are feasible
        """
        for i in range(len(cop) - 1):
            current_soc = cop.iloc[i]['soc_begin']
            next_soc = cop.iloc[i + 1]['soc_begin']
            
            # Maximum possible change in one hour
            max_discharge = min(self.bess.hsl, current_soc - self.bess.min_soc)
            max_charge = min(abs(self.bess.lsl) * self.bess.efficiency, 
                           self.bess.max_soc - current_soc)
            
            soc_change = next_soc - current_soc
            
            # Check feasibility
            if soc_change > max_charge:
                # Cannot charge this much - adjust
                cop.iloc[i + 1, cop.columns.get_loc('soc_begin')] = current_soc + max_charge
                cop.iloc[i, cop.columns.get_loc('target_mw')] = self.bess.lsl
                logger.warning(f"Adjusted SOC at hour {i+1} - infeasible charge")
                
            elif soc_change < -max_discharge:
                # Cannot discharge this much - adjust
                cop.iloc[i + 1, cop.columns.get_loc('soc_begin')] = current_soc - max_discharge
                cop.iloc[i, cop.columns.get_loc('target_mw')] = self.bess.hsl
                logger.warning(f"Adjusted SOC at hour {i+1} - infeasible discharge")
        
        # Ensure SOC stays within bounds
        cop['soc_begin'] = cop['soc_begin'].clip(self.bess.min_soc, self.bess.max_soc)
        
        return cop
    
    def _apply_as_commitments(self, cop: pd.DataFrame, 
                            as_commitments: pd.DataFrame) -> pd.DataFrame:
        """
        Apply ancillary service commitments to COP
        """
        for hour in as_commitments.index:
            if hour in cop.index:
                # Get AS commitments for this hour
                reg_mw = as_commitments.loc[hour, 'regulation'] if 'regulation' in as_commitments.columns else 0
                rrs_mw = as_commitments.loc[hour, 'rrs'] if 'rrs' in as_commitments.columns else 0
                ecrs_mw = as_commitments.loc[hour, 'ecrs'] if 'ecrs' in as_commitments.columns else 0
                
                # Update status based on AS
                if reg_mw > 0:
                    cop.loc[hour, 'status'] = ResourceStatus.ONREG.value
                    cop.loc[hour, 'target_mw'] = 0  # Energy neutral for regulation
                elif rrs_mw > 0:
                    cop.loc[hour, 'status'] = ResourceStatus.ONRR.value
                    # Reserve SOC for RRS
                    cop.loc[hour, 'soc_min'] = max(cop.loc[hour, 'soc_min'], rrs_mw)
                elif ecrs_mw > 0:
                    cop.loc[hour, 'status'] = ResourceStatus.ONECRS.value
                    # Reserve SOC for ECRS (2 hours)
                    cop.loc[hour, 'soc_min'] = max(cop.loc[hour, 'soc_min'], ecrs_mw * 2)
        
        return cop
    
    def _add_cop_fields(self, cop: pd.DataFrame) -> pd.DataFrame:
        """
        Add all required COP fields
        """
        # Ramp rates
        cop['normal_ramp_up'] = self.bess.ramp_rate_up
        cop['normal_ramp_down'] = self.bess.ramp_rate_down
        cop['emergency_ramp_up'] = self.bess.ramp_rate_up * 1.5
        cop['emergency_ramp_down'] = self.bess.ramp_rate_down * 1.5
        
        # Emergency limits (same as normal for BESS)
        cop['hel'] = cop['hsl']  # High Emergency Limit
        cop['lel'] = cop['lsl']  # Low Emergency Limit
        
        # Auxiliary load
        cop['aux_load'] = self.bess.aux_load
        
        # Resource type
        cop['resource_type'] = 'ESR'
        
        # Fuel type (N/A for BESS)
        cop['fuel_type'] = 'BATTERY'
        
        return cop


class COPValidator:
    """
    Validate COP for ERCOT compliance
    """
    
    def __init__(self, bess_params: BESSParameters):
        self.bess = bess_params
        self.validation_errors = []
        self.validation_warnings = []
        
    def validate(self, cop: pd.DataFrame) -> Dict:
        """
        Comprehensive COP validation
        
        Returns:
        --------
        Dict with validation results
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Run all validation checks
        self._validate_soc_feasibility(cop)
        self._validate_soc_bounds(cop)
        self._validate_ramp_rates(cop)
        self._validate_as_requirements(cop)
        self._validate_data_completeness(cop)
        self._validate_timeline_requirements(cop)
        
        # Compile results
        results = {
            'valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings),
            'summary': self._generate_validation_summary()
        }
        
        return results
    
    def _validate_soc_feasibility(self, cop: pd.DataFrame):
        """
        Validate SOC transitions are feasible
        """
        for i in range(len(cop) - 1):
            current = cop.iloc[i]
            next_hour = cop.iloc[i + 1]
            
            # Calculate maximum possible SOC change
            max_discharge = min(current['hsl'], 
                              current['soc_begin'] - current['soc_min'])
            max_charge = min(abs(current['lsl']) * self.bess.efficiency,
                           current['soc_max'] - current['soc_begin'])
            
            # Actual SOC change
            soc_change = next_hour['soc_begin'] - current['soc_begin']
            
            # Check feasibility
            if soc_change > max_charge + 0.01:  # Small tolerance for rounding
                self.validation_errors.append({
                    'hour': i,
                    'type': 'SOC_INFEASIBLE_CHARGE',
                    'message': f"Hour {i}: Cannot charge {soc_change:.1f} MWh (max: {max_charge:.1f})",
                    'severity': 'ERROR'
                })
            elif soc_change < -(max_discharge + 0.01):
                self.validation_errors.append({
                    'hour': i,
                    'type': 'SOC_INFEASIBLE_DISCHARGE',
                    'message': f"Hour {i}: Cannot discharge {-soc_change:.1f} MWh (max: {max_discharge:.1f})",
                    'severity': 'ERROR'
                })
    
    def _validate_soc_bounds(self, cop: pd.DataFrame):
        """
        Validate SOC stays within min/max bounds
        """
        for i, row in cop.iterrows():
            # Check absolute bounds
            if row['soc_begin'] < self.bess.min_soc:
                self.validation_errors.append({
                    'hour': i,
                    'type': 'SOC_BELOW_MIN',
                    'message': f"SOC {row['soc_begin']:.1f} below minimum {self.bess.min_soc}",
                    'severity': 'ERROR'
                })
            elif row['soc_begin'] > self.bess.max_soc:
                self.validation_errors.append({
                    'hour': i,
                    'type': 'SOC_ABOVE_MAX',
                    'message': f"SOC {row['soc_begin']:.1f} above maximum {self.bess.max_soc}",
                    'severity': 'ERROR'
                })
            
            # Check min/max SOC consistency
            if row['soc_min'] > row['soc_begin']:
                self.validation_warnings.append({
                    'hour': i,
                    'type': 'SOC_MIN_INCONSISTENT',
                    'message': f"MinSOC {row['soc_min']:.1f} > Beginning SOC {row['soc_begin']:.1f}",
                    'severity': 'WARNING'
                })
            if row['soc_max'] < row['soc_begin']:
                self.validation_warnings.append({
                    'hour': i,
                    'type': 'SOC_MAX_INCONSISTENT',
                    'message': f"MaxSOC {row['soc_max']:.1f} < Beginning SOC {row['soc_begin']:.1f}",
                    'severity': 'WARNING'
                })
    
    def _validate_ramp_rates(self, cop: pd.DataFrame):
        """
        Validate ramp rates are achievable
        """
        for i in range(len(cop) - 1):
            current = cop.iloc[i]
            next_hour = cop.iloc[i + 1]
            
            # Skip if status changing (startup/shutdown)
            if current['status'] != next_hour['status']:
                continue
            
            # Calculate required ramp
            if 'target_mw' in cop.columns:
                mw_change = abs(next_hour.get('target_mw', 0) - current.get('target_mw', 0))
                max_ramp = max(current['normal_ramp_up'], current['normal_ramp_down']) * 60  # MW/hour
                
                if mw_change > max_ramp * 1.05:  # 5% tolerance
                    self.validation_warnings.append({
                        'hour': i,
                        'type': 'RAMP_RATE_EXCEEDED',
                        'message': f"Hour {i}: Ramp {mw_change:.1f} MW exceeds capability {max_ramp:.1f} MW/hr",
                        'severity': 'WARNING'
                    })
    
    def _validate_as_requirements(self, cop: pd.DataFrame):
        """
        Validate AS commitments have sufficient SOC
        """
        for i, row in cop.iterrows():
            if row['status'] == ResourceStatus.ONRR.value:
                # RRS requires 1 hour of energy
                required_soc = row['hsl'] * 1.0
                if row['soc_begin'] < required_soc:
                    self.validation_warnings.append({
                        'hour': i,
                        'type': 'INSUFFICIENT_SOC_FOR_RRS',
                        'message': f"Hour {i}: SOC {row['soc_begin']:.1f} insufficient for RRS {required_soc:.1f}",
                        'severity': 'WARNING'
                    })
            
            elif row['status'] == ResourceStatus.ONECRS.value:
                # ECRS requires 2 hours of energy
                required_soc = row['hsl'] * 2.0
                if row['soc_begin'] < required_soc:
                    self.validation_warnings.append({
                        'hour': i,
                        'type': 'INSUFFICIENT_SOC_FOR_ECRS',
                        'message': f"Hour {i}: SOC {row['soc_begin']:.1f} insufficient for ECRS {required_soc:.1f}",
                        'severity': 'WARNING'
                    })
    
    def _validate_data_completeness(self, cop: pd.DataFrame):
        """
        Validate all required fields are present
        """
        required_fields = [
            'hour_ending', 'resource_name', 'status',
            'hsl', 'lsl', 'soc_begin', 'soc_min', 'soc_max',
            'normal_ramp_up', 'normal_ramp_down'
        ]
        
        missing_fields = [f for f in required_fields if f not in cop.columns]
        
        if missing_fields:
            self.validation_errors.append({
                'type': 'MISSING_FIELDS',
                'message': f"Missing required fields: {missing_fields}",
                'severity': 'ERROR'
            })
        
        # Check for null values
        for field in required_fields:
            if field in cop.columns and cop[field].isnull().any():
                self.validation_errors.append({
                    'type': 'NULL_VALUES',
                    'message': f"Null values found in required field: {field}",
                    'severity': 'ERROR'
                })
    
    def _validate_timeline_requirements(self, cop: pd.DataFrame):
        """
        Validate COP covers required period (7 days)
        """
        if len(cop) < 168:  # 7 days * 24 hours
            self.validation_warnings.append({
                'type': 'INSUFFICIENT_HORIZON',
                'message': f"COP contains {len(cop)} hours, 168 required for 7 days",
                'severity': 'WARNING'
            })
    
    def _generate_validation_summary(self) -> str:
        """
        Generate validation summary message
        """
        if len(self.validation_errors) == 0:
            return "COP validation PASSED - ready for submission"
        else:
            error_types = list(set([e['type'] for e in self.validation_errors]))
            return f"COP validation FAILED - {len(self.validation_errors)} errors: {', '.join(error_types)}"


class COPSubmitter:
    """
    Submit COP to ERCOT systems
    """
    
    def __init__(self, credentials: Dict):
        """
        Initialize with ERCOT credentials
        
        Parameters:
        -----------
        credentials : dict
            Contains 'username', 'password', 'api_key', 'endpoint'
        """
        self.credentials = credentials
        self.submission_history = []
        
    def submit_cop(self, cop: pd.DataFrame, test_mode: bool = True) -> Dict:
        """
        Submit COP to ERCOT
        
        Parameters:
        -----------
        cop : DataFrame
            Validated COP data
        test_mode : bool
            If True, simulate submission without sending
        
        Returns:
        --------
        Dict with submission results
        """
        
        # Convert COP to ERCOT format
        cop_payload = self._format_for_ercot(cop)
        
        if test_mode:
            # Simulate submission
            result = {
                'status': 'TEST_SUCCESS',
                'message': 'COP validated and ready for submission (test mode)',
                'timestamp': datetime.now().isoformat(),
                'cop_id': f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'payload_size': len(json.dumps(cop_payload))
            }
        else:
            # Actual submission
            result = self._send_to_ercot(cop_payload)
        
        # Log submission
        self.submission_history.append({
            'timestamp': datetime.now(),
            'result': result,
            'cop_summary': {
                'hours': len(cop),
                'start': cop.iloc[0]['hour_ending'],
                'end': cop.iloc[-1]['hour_ending']
            }
        })
        
        return result
    
    def _format_for_ercot(self, cop: pd.DataFrame) -> Dict:
        """
        Format COP data for ERCOT submission
        """
        # Convert to ERCOT XML/JSON format
        cop_data = []
        
        for _, row in cop.iterrows():
            cop_entry = {
                'hour_ending': row['hour_ending'].isoformat(),
                'resource_name': row['resource_name'],
                'resource_status': row['status'],
                'hsl': row['hsl'],
                'lsl': row['lsl'],
                'hel': row.get('hel', row['hsl']),
                'lel': row.get('lel', row['lsl']),
                'normal_ramp_rate_up': row['normal_ramp_up'],
                'normal_ramp_rate_down': row['normal_ramp_down'],
                'emergency_ramp_rate_up': row.get('emergency_ramp_up', row['normal_ramp_up'] * 1.5),
                'emergency_ramp_rate_down': row.get('emergency_ramp_down', row['normal_ramp_down'] * 1.5),
                'minimum_soc': row['soc_min'],
                'maximum_soc': row['soc_max'],
                'hour_beginning_planned_soc': row['soc_begin']
            }
            cop_data.append(cop_entry)
        
        payload = {
            'cop_submission': {
                'qse_name': self.credentials.get('qse_name', 'TEST_QSE'),
                'submission_time': datetime.now().isoformat(),
                'cop_data': cop_data
            }
        }
        
        return payload
    
    def _send_to_ercot(self, payload: Dict) -> Dict:
        """
        Send COP to ERCOT API (production)
        """
        try:
            headers = {
                'Authorization': f"Bearer {self.credentials['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.credentials['endpoint'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'status': 'SUCCESS',
                    'message': 'COP submitted successfully',
                    'timestamp': datetime.now().isoformat(),
                    'cop_id': response.json().get('cop_id'),
                    'response': response.json()
                }
            else:
                return {
                    'status': 'ERROR',
                    'message': f"Submission failed: {response.status_code}",
                    'timestamp': datetime.now().isoformat(),
                    'error': response.text
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f"Submission failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def check_submission_status(self, cop_id: str) -> Dict:
        """
        Check status of submitted COP
        """
        # In production, this would query ERCOT API
        # For now, return mock status
        return {
            'cop_id': cop_id,
            'status': 'ACCEPTED',
            'validation_results': 'PASSED',
            'effective_time': datetime.now().isoformat()
        }


class COPAutomationSystem:
    """
    Complete COP automation system
    """
    
    def __init__(self, bess_params: BESSParameters, credentials: Dict):
        self.bess = bess_params
        self.generator = COPGenerator(bess_params)
        self.validator = COPValidator(bess_params)
        self.submitter = COPSubmitter(credentials)
        
    def run_daily_cop(self, 
                     price_forecast: Optional[pd.DataFrame] = None,
                     as_commitments: Optional[pd.DataFrame] = None,
                     auto_submit: bool = False) -> Dict:
        """
        Run complete daily COP process
        """
        logger.info("Starting daily COP generation process")
        
        # Generate COP
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        cop = self.generator.generate_cop(
            start_date=start_date,
            days=7,
            price_forecast=price_forecast,
            as_commitments=as_commitments
        )
        
        logger.info(f"Generated COP with {len(cop)} hours")
        
        # Validate COP
        validation_results = self.validator.validate(cop)
        
        if validation_results['valid']:
            logger.info("COP validation PASSED")
            
            if auto_submit:
                # Submit COP
                submission_result = self.submitter.submit_cop(cop, test_mode=False)
                logger.info(f"COP submission result: {submission_result['status']}")
            else:
                submission_result = {
                    'status': 'NOT_SUBMITTED',
                    'message': 'Auto-submit disabled'
                }
        else:
            logger.error(f"COP validation FAILED: {validation_results['error_count']} errors")
            submission_result = {
                'status': 'NOT_SUBMITTED',
                'message': 'Validation failed'
            }
        
        # Compile results
        results = {
            'generation_time': datetime.now().isoformat(),
            'cop_summary': {
                'hours': len(cop),
                'start_date': cop.iloc[0]['hour_ending'],
                'end_date': cop.iloc[-1]['hour_ending']
            },
            'validation': validation_results,
            'submission': submission_result,
            'cop_data': cop.to_dict('records') if validation_results['valid'] else None
        }
        
        return results


# Example usage and testing
if __name__ == "__main__":
    # Define BESS parameters
    bess_params = BESSParameters(
        resource_name="BESS_WEST_100MW",
        capacity_mw=100,
        capacity_mwh=200,
        efficiency=0.86,
        ramp_rate_up=50,  # MW/min
        ramp_rate_down=50,
        min_soc=0,
        max_soc=200,
        aux_load=2  # MW
    )
    
    # Mock credentials (would be real in production)
    credentials = {
        'username': 'test_user',
        'password': 'test_pass',
        'api_key': 'test_api_key',
        'endpoint': 'https://api.ercot.com/cop/submit',
        'qse_name': 'TEST_QSE'
    }
    
    # Create automation system
    cop_system = COPAutomationSystem(bess_params, credentials)
    
    # Generate sample price forecast
    hours = pd.date_range(start=datetime.now(), periods=168, freq='H')
    price_forecast = pd.DataFrame(index=hours)
    
    # Simple price pattern
    for hour in hours:
        if hour.hour in range(14, 20):  # Peak hours
            price_forecast.loc[hour, 'price'] = np.random.uniform(60, 120)
        elif hour.hour in range(0, 6):  # Off-peak
            price_forecast.loc[hour, 'price'] = np.random.uniform(10, 30)
        else:  # Shoulder
            price_forecast.loc[hour, 'price'] = np.random.uniform(30, 60)
    
    # Run daily COP process
    print("\n=== ERCOT BESS COP Automation System ===")
    print(f"Resource: {bess_params.resource_name}")
    print(f"Capacity: {bess_params.capacity_mw} MW / {bess_params.capacity_mwh} MWh")
    
    results = cop_system.run_daily_cop(
        price_forecast=price_forecast,
        as_commitments=None,
        auto_submit=False  # Test mode
    )
    
    print(f"\nCOP Generation: COMPLETE")
    print(f"Validation: {results['validation']['summary']}")
    print(f"Errors: {results['validation']['error_count']}")
    print(f"Warnings: {results['validation']['warning_count']}")
    
    if results['validation']['errors']:
        print("\nFirst 3 Errors:")
        for error in results['validation']['errors'][:3]:
            print(f"  - {error['message']}")
    
    if results['validation']['warnings']:
        print("\nFirst 3 Warnings:")
        for warning in results['validation']['warnings'][:3]:
            print(f"  - {warning['message']}")
    
    print(f"\nSubmission Status: {results['submission']['status']}")
    print(f"Message: {results['submission']['message']}")
    
    # Save COP to file if valid
    if results['cop_data']:
        cop_df = pd.DataFrame(results['cop_data'])
        cop_df.to_csv('cop_submission.csv', index=False)
        print("\nCOP saved to 'cop_submission.csv'")
    
    print("\n=== COP Automation Complete ===")