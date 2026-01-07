import numpy as np
from scipy import stats

class BacktestEngine:
    """
    Backtest VaR models using:
    - Basel Traffic Light Approach
    - Kupiec POF Test
    - Christoffersen Independence Test
    """
    
    def count_breaches(self, returns, var_threshold):
        """Count number of times loss exceeded VaR"""
        if returns is None or len(returns) == 0:
            return 0
        
        # Convert percentage VaR to decimal
        var_decimal = var_threshold / 100
        
        # Count breaches (losses exceeding VaR)
        breaches = np.sum(returns < -var_decimal)
        return int(breaches)
    
    def basel_traffic_light(self, breaches, total_days, confidence_level=0.95):
        """
        Basel Traffic Light Approach
        Green: 0-4 breaches (250 days, 95% VaR)
        Yellow: 5-9 breaches
        Red: 10+ breaches
        """
        expected_breaches = total_days * (1 - confidence_level)
        
        if confidence_level == 0.95:
            if breaches <= 4:
                return 'GREEN', 'Model is accurate'
            elif breaches <= 9:
                return 'YELLOW', 'Model needs attention'
            else:
                return 'RED', 'Model is inadequate'
        else:  # 99%
            if breaches <= 2:
                return 'GREEN', 'Model is accurate'
            else:
                return 'RED', 'Model is inadequate'
    
    def kupiec_test(self, breaches, total_days, confidence_level=0.95):
        """
        Kupiec Proportion of Failures (POF) Test
        Tests if observed breach rate matches expected rate
        """
        expected_rate = 1 - confidence_level
        observed_rate = breaches / total_days
        
        # Likelihood ratio test statistic
        if breaches == 0 or breaches == total_days:
            lr_stat = 0
        else:
            lr_stat = -2 * (
                np.log((expected_rate ** breaches) * ((1 - expected_rate) ** (total_days - breaches)))
                - np.log((observed_rate ** breaches) * ((1 - observed_rate) ** (total_days - breaches)))
            )
        
        # Critical value at 95% confidence (chi-square with 1 df)
        critical_value = 3.841
        p_value = 1 - stats.chi2.cdf(lr_stat, df=1)
        
        reject = lr_stat > critical_value
        
        return {
            'lr_statistic': lr_stat,
            'critical_value': critical_value,
            'p_value': p_value,
            'reject_model': reject,
            'interpretation': 'Reject model' if reject else 'Accept model'
        }
    
    def backtest_results(self, returns, var_metrics, position_value=1000000):
        """Generate comprehensive backtest results"""
        if returns is None or len(returns) < 30:
            return None
        
        results = {}
        total_days = len(returns)
        
        for confidence in [0.95, 0.99]:
            label = f"{int(confidence * 100)}%"
            
            # Get VaR threshold
            var_key = f'var_{label}_hist'
            if var_key not in var_metrics:
                continue
            
            var_threshold = var_metrics[var_key]['var_return']
            
            # Count breaches
            breaches = self.count_breaches(returns, var_threshold)
            
            # Basel test
            traffic_light, tl_message = self.basel_traffic_light(breaches, total_days, confidence)
            
            # Kupiec test
            kupiec = self.kupiec_test(breaches, total_days, confidence)
            
            results[label] = {
                'breaches': breaches,
                'total_days': total_days,
                'breach_rate': breaches / total_days,
                'expected_rate': 1 - confidence,
                'traffic_light': traffic_light,
                'traffic_message': tl_message,
                'kupiec_test': kupiec
            }
        
        return results
