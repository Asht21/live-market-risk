import numpy as np
from scipy import stats

class VaRCalculator:
    """
    Calculate Value at Risk and Expected Shortfall
    Methods: Historical Simulation, Parametric (Normal), Monte Carlo
    """
    
    def historical_var(self, returns, confidence_level=0.95, position_value=1000000):
        """Historical Simulation VaR"""
        if returns is None or len(returns) < 10:
            return None
        
        # Sort returns
        sorted_returns = np.sort(returns)
        
        # Find VaR (loss convention: negative return)
        var_index = int((1 - confidence_level) * len(sorted_returns))
        var_return = sorted_returns[var_index]
        var_dollar = abs(var_return * position_value)
        
        return {
            'var_return': abs(var_return) * 100,  # As positive percentage
            'var_dollar': var_dollar,
            'confidence': confidence_level,
            'method': 'Historical Simulation'
        }
    
    def parametric_var(self, returns, confidence_level=0.95, position_value=1000000):
        """Parametric VaR (assumes normal distribution)"""
        if returns is None or len(returns) < 10:
            return None
        
        mean = returns.mean()
        std = returns.std()
        
        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # VaR calculation
        var_return = abs(mean + z_score * std)
        var_dollar = var_return * position_value
        
        return {
            'var_return': var_return * 100,
            'var_dollar': var_dollar,
            'confidence': confidence_level,
            'method': 'Parametric (Normal)'
        }
    
    def expected_shortfall(self, returns, confidence_level=0.95, position_value=1000000):
        """Expected Shortfall (CVaR) - average loss beyond VaR"""
        if returns is None or len(returns) < 10:
            return None
        
        sorted_returns = np.sort(returns)
        var_index = int((1 - confidence_level) * len(sorted_returns))
        
        # Average of all losses beyond VaR
        tail_returns = sorted_returns[:var_index + 1]
        es_return = abs(tail_returns.mean())
        es_dollar = es_return * position_value
        
        return {
            'es_return': es_return * 100,
            'es_dollar': es_dollar,
            'confidence': confidence_level,
            'method': 'Expected Shortfall'
        }
    
    def calculate_all_metrics(self, returns, position_value=1000000):
        """Calculate comprehensive risk metrics"""
        metrics = {}
        
        for conf in [0.95, 0.99]:
            label = f"{int(conf * 100)}%"
            
            # Historical VaR
            hist_var = self.historical_var(returns, conf, position_value)
            if hist_var:
                metrics[f'var_{label}_hist'] = hist_var
            
            # Parametric VaR
            param_var = self.parametric_var(returns, conf, position_value)
            if param_var:
                metrics[f'var_{label}_param'] = param_var
            
            # Expected Shortfall
            es = self.expected_shortfall(returns, conf, position_value)
            if es:
                metrics[f'es_{label}'] = es
        
        return metrics
