import numpy as np

class StressTestEngine:
    """
    Implement stress testing scenarios:
    - Historical scenarios (2008 crisis, COVID crash)
    - Hypothetical scenarios
    - Sensitivity analysis
    """
    
    def __init__(self):
        self.scenarios = {
            'market_crash': {
                'name': 'Market Crash (-3σ)',
                'nifty_shock': -0.15,  # -15%
                'equity_correlation': 0.9
            },
            'covid_style': {
                'name': 'COVID-style Crash',
                'nifty_shock': -0.38,  # -38% (March 2020)
                'equity_correlation': 0.95
            },
            'volatility_spike': {
                'name': 'Volatility Spike',
                'vol_multiplier': 2.5,
                'nifty_shock': -0.10
            },
            '2008_crisis': {
                'name': '2008-style Crisis',
                'nifty_shock': -0.52,  # -52% (2008 peak to trough)
                'equity_correlation': 0.98
            }
        }
    
    def apply_scenario(self, scenario_name, position_values, returns_data):
        """Apply stress scenario to portfolio"""
        if scenario_name not in self.scenarios:
            return None
        
        scenario = self.scenarios[scenario_name]
        results = {}
        total_loss = 0
        
        for symbol, position in position_values.items():
            if '^NSEI' in symbol:
                # Direct Nifty shock
                loss = position * abs(scenario['nifty_shock'])
            else:
                # Correlated shock for equities
                if 'equity_correlation' in scenario:
                    shock = scenario['nifty_shock'] * scenario['equity_correlation']
                else:
                    shock = scenario['nifty_shock'] * 0.8
                
                loss = position * abs(shock)
            
            results[symbol] = {
                'position': position,
                'loss': loss,
                'loss_pct': (loss / position) * 100
            }
            total_loss += loss
        
        return {
            'scenario_name': scenario['name'],
            'total_loss': total_loss,
            'asset_breakdown': results
        }
    
    def sensitivity_analysis(self, position_value, base_volatility):
        """Perform sensitivity analysis on volatility changes"""
        vol_scenarios = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
        results = []
        
        for multiplier in vol_scenarios:
            new_vol = base_volatility * multiplier
            # Approximate VaR scaling with volatility
            var_impact = position_value * (new_vol / np.sqrt(252)) * 2.33  # 99% quantile
            
            results.append({
                'vol_multiplier': multiplier,
                'annual_vol': new_vol * 100,
                'estimated_var_99': var_impact
            })
        
        return results