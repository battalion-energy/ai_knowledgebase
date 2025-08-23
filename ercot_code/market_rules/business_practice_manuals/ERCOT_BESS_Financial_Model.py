#!/usr/bin/env python3
"""
ERCOT BESS Financial Model and Revenue Analysis Tool
Version 1.0 - August 2025

Comprehensive financial modeling tool for BESS projects in ERCOT market
Includes revenue projections, NPV analysis, and sensitivity analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

class BESSFinancialModel:
    """
    Complete financial model for BESS projects in ERCOT
    """
    
    def __init__(self, config: Dict):
        """
        Initialize financial model with project parameters
        
        Parameters:
        -----------
        config : dict
            Configuration containing:
            - capacity_mw: Nameplate capacity in MW
            - capacity_mwh: Energy capacity in MWh
            - capex_per_mwh: Capital cost per MWh
            - project_life_years: Project lifetime
            - discount_rate: WACC for NPV calculations
        """
        self.capacity_mw = config['capacity_mw']
        self.capacity_mwh = config['capacity_mwh']
        self.duration_hours = self.capacity_mwh / self.capacity_mw
        self.capex_per_mwh = config.get('capex_per_mwh', 300000)
        self.project_life = config.get('project_life_years', 20)
        self.discount_rate = config.get('discount_rate', 0.08)
        
        # Technical parameters
        self.round_trip_efficiency = config.get('efficiency', 0.85)
        self.initial_soh = 1.0  # State of Health
        self.degradation_per_cycle = config.get('degradation_per_cycle', 0.00002)
        self.aux_consumption = config.get('aux_consumption_percent', 0.02)
        
        # Financial parameters
        self.debt_ratio = config.get('debt_ratio', 0.7)
        self.interest_rate = config.get('interest_rate', 0.05)
        self.tax_rate = config.get('tax_rate', 0.21)
        self.depreciation_years = config.get('depreciation_years', 7)
        
        # O&M parameters
        self.fixed_om_per_mw_year = config.get('fixed_om_per_mw_year', 10000)
        self.variable_om_per_mwh = config.get('variable_om_per_mwh', 2)
        self.insurance_percent = config.get('insurance_percent', 0.005)
        
        # Initialize results storage
        self.results = {}
        
    def calculate_capex(self) -> Dict:
        """
        Calculate total capital expenditure and financing
        """
        # Direct costs
        battery_cost = self.capacity_mwh * self.capex_per_mwh
        
        # Indirect costs (% of battery cost)
        epc_cost = battery_cost * 0.15  # EPC markup
        development_cost = battery_cost * 0.05  # Development costs
        interconnection_cost = battery_cost * 0.10  # Grid connection
        land_cost = battery_cost * 0.02  # Land lease/purchase
        
        total_capex = (battery_cost + epc_cost + development_cost + 
                      interconnection_cost + land_cost)
        
        # Financing
        debt_amount = total_capex * self.debt_ratio
        equity_amount = total_capex * (1 - self.debt_ratio)
        
        return {
            'battery_cost': battery_cost,
            'epc_cost': epc_cost,
            'development_cost': development_cost,
            'interconnection_cost': interconnection_cost,
            'land_cost': land_cost,
            'total_capex': total_capex,
            'debt_amount': debt_amount,
            'equity_amount': equity_amount,
            'debt_service_annual': self._calculate_debt_service(debt_amount)
        }
    
    def _calculate_debt_service(self, principal: float, term_years: int = 10) -> float:
        """
        Calculate annual debt service (principal + interest)
        """
        if self.interest_rate == 0:
            return principal / term_years
        
        # Calculate annual payment using amortization formula
        r = self.interest_rate
        n = term_years
        annual_payment = principal * (r * (1 + r)**n) / ((1 + r)**n - 1)
        
        return annual_payment
    
    def calculate_revenues(self, market_prices: Optional[Dict] = None) -> pd.DataFrame:
        """
        Calculate revenue projections over project lifetime
        
        Parameters:
        -----------
        market_prices : dict, optional
            Custom market price assumptions, otherwise uses defaults
        """
        if market_prices is None:
            market_prices = self._default_market_prices()
        
        years = range(1, self.project_life + 1)
        revenues = pd.DataFrame(index=years)
        
        # Track degradation
        soh = self.initial_soh
        cycles_total = 0
        
        for year in years:
            # Adjust capacity for degradation
            effective_capacity_mwh = self.capacity_mwh * soh
            effective_capacity_mw = self.capacity_mw * soh
            
            # Energy arbitrage revenue
            daily_cycles = market_prices['daily_cycles']
            annual_cycles = daily_cycles * 350  # Allow for maintenance
            
            # Average spread captured
            avg_spread = market_prices['energy_spread_base'] * (
                1 + market_prices['energy_spread_growth'] * (year - 1)
            )
            
            energy_revenue = (
                annual_cycles * 
                effective_capacity_mwh * 
                avg_spread * 
                self.round_trip_efficiency
            )
            
            # Ancillary services revenue
            as_hours = 8760 * market_prices['as_participation_rate']
            as_price = market_prices['as_price_base'] * (
                1 + market_prices['as_price_growth'] * (year - 1)
            )
            
            as_revenue = (
                as_hours * 
                effective_capacity_mw * 
                as_price * 
                market_prices['as_performance_score']
            )
            
            # Capacity payment (if available, future market)
            capacity_revenue = 0
            if year > market_prices.get('capacity_market_start_year', 100):
                capacity_price = market_prices.get('capacity_price_mw_year', 50000)
                capacity_revenue = effective_capacity_mw * capacity_price
            
            # Store results
            revenues.loc[year, 'energy_arbitrage'] = energy_revenue
            revenues.loc[year, 'ancillary_services'] = as_revenue
            revenues.loc[year, 'capacity_payments'] = capacity_revenue
            revenues.loc[year, 'total_revenue'] = (
                energy_revenue + as_revenue + capacity_revenue
            )
            
            # Update degradation
            cycles_total += annual_cycles
            soh = max(0.6, 1 - cycles_total * self.degradation_per_cycle)
            revenues.loc[year, 'soh'] = soh
            revenues.loc[year, 'annual_cycles'] = annual_cycles
        
        return revenues
    
    def _default_market_prices(self) -> Dict:
        """
        Default market price assumptions for ERCOT
        """
        return {
            'energy_spread_base': 35,  # $/MWh average spread captured
            'energy_spread_growth': 0.02,  # Annual growth rate
            'daily_cycles': 1.5,  # Average cycles per day
            'as_participation_rate': 0.3,  # % of hours providing AS
            'as_price_base': 15,  # $/MW-hr for AS
            'as_price_growth': 0.03,  # Annual AS price growth
            'as_performance_score': 0.95,  # AS performance factor
            'capacity_market_start_year': 100,  # No capacity market yet
            'capacity_price_mw_year': 0  # $/MW-year if implemented
        }
    
    def calculate_expenses(self, revenues_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate operating expenses over project lifetime
        """
        years = revenues_df.index
        expenses = pd.DataFrame(index=years)
        
        capex_results = self.calculate_capex()
        
        for year in years:
            # Fixed O&M
            fixed_om = self.fixed_om_per_mw_year * self.capacity_mw
            
            # Variable O&M (based on throughput)
            annual_throughput = (
                revenues_df.loc[year, 'annual_cycles'] * 
                self.capacity_mwh * 2  # Charge + discharge
            )
            variable_om = self.variable_om_per_mwh * annual_throughput
            
            # Insurance
            insurance = capex_results['total_capex'] * self.insurance_percent
            
            # Property tax (assume 1% of capex)
            property_tax = capex_results['total_capex'] * 0.01
            
            # Land lease (if applicable)
            land_lease = self.capacity_mw * 2000  # $/MW-year typical
            
            # Auxiliary power consumption
            aux_power_cost = (
                revenues_df.loc[year, 'total_revenue'] * 
                self.aux_consumption
            )
            
            # Augmentation costs (every 5 years to maintain capacity)
            augmentation = 0
            if year % 5 == 0 and year > 0:
                # Restore 10% of capacity
                augmentation = self.capacity_mwh * 0.1 * self.capex_per_mwh * 0.5
            
            # Total operating expenses
            expenses.loc[year, 'fixed_om'] = fixed_om
            expenses.loc[year, 'variable_om'] = variable_om
            expenses.loc[year, 'insurance'] = insurance
            expenses.loc[year, 'property_tax'] = property_tax
            expenses.loc[year, 'land_lease'] = land_lease
            expenses.loc[year, 'aux_power'] = aux_power_cost
            expenses.loc[year, 'augmentation'] = augmentation
            expenses.loc[year, 'total_opex'] = (
                fixed_om + variable_om + insurance + property_tax + 
                land_lease + aux_power_cost + augmentation
            )
        
        return expenses
    
    def calculate_cash_flows(self, 
                           revenues_df: pd.DataFrame,
                           expenses_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate project cash flows including tax effects
        """
        years = revenues_df.index
        cash_flows = pd.DataFrame(index=years)
        
        capex_results = self.calculate_capex()
        
        # MACRS depreciation schedule (7-year)
        macrs_7_year = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446]
        
        for year in years:
            # EBITDA
            ebitda = revenues_df.loc[year, 'total_revenue'] - expenses_df.loc[year, 'total_opex']
            
            # Depreciation
            depreciation = 0
            if year <= len(macrs_7_year):
                depreciation = capex_results['total_capex'] * macrs_7_year[year-1]
            
            # Interest (simplified - declining balance)
            remaining_debt = max(0, capex_results['debt_amount'] * (1 - (year-1)/10))
            interest = remaining_debt * self.interest_rate
            
            # Taxable income
            ebt = ebitda - depreciation - interest
            
            # Taxes
            taxes = max(0, ebt * self.tax_rate)
            
            # Net income
            net_income = ebt - taxes
            
            # Add back depreciation (non-cash)
            operating_cash_flow = net_income + depreciation
            
            # Debt service
            debt_service = capex_results['debt_service_annual'] if year <= 10 else 0
            
            # Free cash flow
            if year == 0:
                fcf = -capex_results['equity_amount']  # Initial equity investment
            else:
                fcf = operating_cash_flow - debt_service
            
            # Store results
            cash_flows.loc[year, 'revenue'] = revenues_df.loc[year, 'total_revenue']
            cash_flows.loc[year, 'opex'] = expenses_df.loc[year, 'total_opex']
            cash_flows.loc[year, 'ebitda'] = ebitda
            cash_flows.loc[year, 'depreciation'] = depreciation
            cash_flows.loc[year, 'interest'] = interest
            cash_flows.loc[year, 'ebt'] = ebt
            cash_flows.loc[year, 'taxes'] = taxes
            cash_flows.loc[year, 'net_income'] = net_income
            cash_flows.loc[year, 'operating_cf'] = operating_cash_flow
            cash_flows.loc[year, 'debt_service'] = debt_service
            cash_flows.loc[year, 'free_cash_flow'] = fcf
        
        return cash_flows
    
    def calculate_returns(self, cash_flows_df: pd.DataFrame) -> Dict:
        """
        Calculate investment returns and key metrics
        """
        capex_results = self.calculate_capex()
        
        # NPV calculation
        fcf = cash_flows_df['free_cash_flow'].values
        years = np.arange(len(fcf))
        discount_factors = (1 + self.discount_rate) ** years
        npv = -capex_results['equity_amount'] + np.sum(fcf[1:] / discount_factors[1:])
        
        # IRR calculation (simplified - using numpy)
        try:
            irr = np.irr(np.insert(fcf, 0, -capex_results['equity_amount']))
        except:
            irr = None
        
        # Payback period
        cumulative_cf = np.cumsum(np.insert(fcf, 0, -capex_results['equity_amount']))
        payback_years = None
        for i, cf in enumerate(cumulative_cf):
            if cf > 0:
                payback_years = i
                break
        
        # LCOE calculation
        total_generation = cash_flows_df['revenue'].sum() / 35  # Rough estimate
        total_costs = (capex_results['total_capex'] + 
                      cash_flows_df['opex'].sum() + 
                      cash_flows_df['debt_service'].sum())
        lcoe = total_costs / total_generation if total_generation > 0 else None
        
        return {
            'npv': npv,
            'irr': irr,
            'payback_years': payback_years,
            'lcoe': lcoe,
            'total_capex': capex_results['total_capex'],
            'equity_investment': capex_results['equity_amount'],
            'average_annual_revenue': cash_flows_df['revenue'].mean(),
            'average_annual_ebitda': cash_flows_df['ebitda'].mean(),
            'project_roi': (cash_flows_df['free_cash_flow'].sum() / 
                          capex_results['equity_amount'] - 1) if capex_results['equity_amount'] > 0 else None
        }
    
    def sensitivity_analysis(self, 
                           base_case_params: Dict,
                           sensitivity_params: Dict) -> pd.DataFrame:
        """
        Perform sensitivity analysis on key parameters
        
        Parameters:
        -----------
        base_case_params : dict
            Base case market assumptions
        sensitivity_params : dict
            Parameters to test with ranges
            Example: {'energy_spread_base': [25, 35, 45]}
        """
        results = []
        
        for param_name, param_values in sensitivity_params.items():
            for value in param_values:
                # Create modified parameters
                test_params = base_case_params.copy()
                test_params[param_name] = value
                
                # Run model
                revenues = self.calculate_revenues(test_params)
                expenses = self.calculate_expenses(revenues)
                cash_flows = self.calculate_cash_flows(revenues, expenses)
                returns = self.calculate_returns(cash_flows)
                
                # Store results
                results.append({
                    'parameter': param_name,
                    'value': value,
                    'npv': returns['npv'],
                    'irr': returns['irr'],
                    'payback_years': returns['payback_years']
                })
        
        return pd.DataFrame(results)
    
    def generate_report(self, output_file: str = 'bess_financial_report.json'):
        """
        Generate comprehensive financial report
        """
        # Run full analysis
        revenues = self.calculate_revenues()
        expenses = self.calculate_expenses(revenues)
        cash_flows = self.calculate_cash_flows(revenues, expenses)
        returns = self.calculate_returns(cash_flows)
        capex = self.calculate_capex()
        
        # Sensitivity analysis
        base_params = self._default_market_prices()
        sensitivity = self.sensitivity_analysis(
            base_params,
            {
                'energy_spread_base': [25, 35, 45],
                'daily_cycles': [1.0, 1.5, 2.0],
                'as_participation_rate': [0.2, 0.3, 0.4]
            }
        )
        
        report = {
            'project_summary': {
                'capacity_mw': self.capacity_mw,
                'capacity_mwh': self.capacity_mwh,
                'duration_hours': self.duration_hours,
                'project_life_years': self.project_life
            },
            'capital_costs': capex,
            'financial_returns': returns,
            'annual_projections': {
                'revenues': revenues.to_dict(),
                'expenses': expenses.to_dict(),
                'cash_flows': cash_flows.to_dict()
            },
            'sensitivity_analysis': sensitivity.to_dict(),
            'key_metrics': {
                'capex_per_kwh': capex['total_capex'] / (self.capacity_mwh * 1000),
                'revenue_per_mw_month_avg': returns['average_annual_revenue'] / self.capacity_mw / 12,
                'ebitda_margin': returns['average_annual_ebitda'] / returns['average_annual_revenue'],
                'debt_service_coverage_ratio': cash_flows['ebitda'].mean() / capex['debt_service_annual']
            }
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report


class RevenueOptimizer:
    """
    Optimize BESS revenue across multiple market products
    """
    
    def __init__(self, bess_params: Dict):
        self.capacity_mw = bess_params['capacity_mw']
        self.capacity_mwh = bess_params['capacity_mwh']
        self.efficiency = bess_params.get('efficiency', 0.85)
        
    def optimize_daily_schedule(self, 
                               price_forecast: np.ndarray,
                               as_prices: Dict) -> Dict:
        """
        Optimize daily schedule across energy and AS markets
        
        Parameters:
        -----------
        price_forecast : array
            24-hour price forecast
        as_prices : dict
            AS prices by service and hour
        """
        schedule = {
            'energy': np.zeros(24),
            'regulation': np.zeros(24),
            'reserves': np.zeros(24),
            'soc': np.zeros(25)
        }
        
        # Initialize SOC at 50%
        schedule['soc'][0] = self.capacity_mwh * 0.5
        
        for hour in range(24):
            # Calculate opportunity values
            energy_value = price_forecast[hour]
            reg_value = as_prices.get('regulation', {}).get(hour, 10)
            reserve_value = as_prices.get('reserves', {}).get(hour, 5)
            
            # Simple decision logic (can be replaced with LP/MIP)
            if energy_value > 50 and schedule['soc'][hour] > 0.2 * self.capacity_mwh:
                # Discharge for energy
                discharge = min(self.capacity_mw, schedule['soc'][hour])
                schedule['energy'][hour] = discharge
                schedule['soc'][hour + 1] = schedule['soc'][hour] - discharge
                
            elif energy_value < 20 and schedule['soc'][hour] < 0.8 * self.capacity_mwh:
                # Charge
                charge = min(self.capacity_mw, 
                           self.capacity_mwh - schedule['soc'][hour])
                schedule['energy'][hour] = -charge
                schedule['soc'][hour + 1] = schedule['soc'][hour] + charge * self.efficiency
                
            elif reg_value > 20:
                # Provide regulation
                schedule['regulation'][hour] = self.capacity_mw * 0.5
                schedule['soc'][hour + 1] = schedule['soc'][hour]  # Assume energy neutral
                
            else:
                # Hold or provide reserves
                schedule['reserves'][hour] = self.capacity_mw
                schedule['soc'][hour + 1] = schedule['soc'][hour]
        
        # Calculate revenues
        energy_revenue = np.sum(schedule['energy'] * price_forecast)
        reg_revenue = np.sum(schedule['regulation'] * 
                            [as_prices.get('regulation', {}).get(h, 10) for h in range(24)])
        reserve_revenue = np.sum(schedule['reserves'] * 
                               [as_prices.get('reserves', {}).get(h, 5) for h in range(24)])
        
        schedule['revenue'] = {
            'energy': energy_revenue,
            'regulation': reg_revenue,
            'reserves': reserve_revenue,
            'total': energy_revenue + reg_revenue + reserve_revenue
        }
        
        return schedule
    
    def monte_carlo_simulation(self, 
                              n_simulations: int = 1000,
                              price_volatility: float = 0.3) -> Dict:
        """
        Run Monte Carlo simulation for revenue uncertainty
        """
        results = []
        
        for _ in range(n_simulations):
            # Generate random price scenario
            base_prices = np.array([
                20, 20, 20, 20, 25, 30, 40, 50,  # Morning ramp
                40, 35, 35, 40, 45, 50, 60, 80,  # Afternoon peak
                100, 90, 70, 50, 40, 30, 25, 20  # Evening decline
            ])
            
            # Add random variation
            noise = np.random.normal(0, price_volatility, 24)
            prices = base_prices * (1 + noise)
            prices = np.maximum(prices, 0)  # No negative prices
            
            # Random AS prices
            as_prices = {
                'regulation': {h: np.random.uniform(5, 30) for h in range(24)},
                'reserves': {h: np.random.uniform(2, 15) for h in range(24)}
            }
            
            # Optimize and store result
            schedule = self.optimize_daily_schedule(prices, as_prices)
            results.append(schedule['revenue']['total'])
        
        return {
            'mean_daily_revenue': np.mean(results),
            'std_daily_revenue': np.std(results),
            'var_95': np.percentile(results, 5),
            'var_99': np.percentile(results, 1),
            'max_daily_revenue': np.max(results),
            'min_daily_revenue': np.min(results)
        }


# Example usage
if __name__ == "__main__":
    # Define BESS project parameters
    project_config = {
        'capacity_mw': 100,
        'capacity_mwh': 200,  # 2-hour duration
        'capex_per_mwh': 250000,  # $250/kWh
        'project_life_years': 20,
        'discount_rate': 0.08,
        'efficiency': 0.86,
        'debt_ratio': 0.7,
        'interest_rate': 0.045
    }
    
    # Create financial model
    model = BESSFinancialModel(project_config)
    
    # Generate comprehensive report
    report = model.generate_report('ercot_bess_financial_analysis.json')
    
    # Print key results
    print("\n=== ERCOT BESS Financial Analysis ===")
    print(f"Project: {project_config['capacity_mw']} MW / {project_config['capacity_mwh']} MWh")
    print(f"Total CAPEX: ${report['capital_costs']['total_capex']:,.0f}")
    print(f"Equity Investment: ${report['capital_costs']['equity_amount']:,.0f}")
    print(f"\nFinancial Returns:")
    print(f"  NPV: ${report['financial_returns']['npv']:,.0f}")
    print(f"  IRR: {report['financial_returns']['irr']:.1%}" if report['financial_returns']['irr'] else "  IRR: N/A")
    print(f"  Payback: {report['financial_returns']['payback_years']} years")
    print(f"  Average Annual Revenue: ${report['financial_returns']['average_annual_revenue']:,.0f}")
    print(f"  Average Annual EBITDA: ${report['financial_returns']['average_annual_ebitda']:,.0f}")
    
    # Run revenue optimization
    optimizer = RevenueOptimizer(project_config)
    mc_results = optimizer.monte_carlo_simulation(n_simulations=1000)
    
    print(f"\nRevenue Simulation Results (Daily):")
    print(f"  Mean Revenue: ${mc_results['mean_daily_revenue']:,.0f}")
    print(f"  Std Deviation: ${mc_results['std_daily_revenue']:,.0f}")
    print(f"  95% VaR: ${mc_results['var_95']:,.0f}")
    print(f"  Range: ${mc_results['min_daily_revenue']:,.0f} - ${mc_results['max_daily_revenue']:,.0f}")
    
    print("\nFinancial model complete. Report saved to 'ercot_bess_financial_analysis.json'")