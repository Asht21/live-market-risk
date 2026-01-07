from datetime import datetime
from collections import deque

class AlertMonitor:
    """Monitor for VaR breaches and risk limit violations"""
    
    def __init__(self, max_alerts=100):
        self.alerts = deque(maxlen=max_alerts)
        self.breach_count = {'95%': 0, '99%': 0}
    
    def check_breach(self, current_return, var_95, var_99, symbol='PORTFOLIO'):
        """Check if current return breaches VaR limits"""
        breaches = []
        
        abs_return = abs(current_return * 100)
        
        if abs_return > var_99:
            self.breach_count['99%'] += 1
            breaches.append({
                'level': '99%',
                'severity': 'CRITICAL',
                'symbol': symbol,
                'return': current_return * 100,
                'threshold': var_99,
                'excess': abs_return - var_99,
                'timestamp': datetime.now()
            })
        elif abs_return > var_95:
            self.breach_count['95%'] += 1
            breaches.append({
                'level': '95%',
                'severity': 'WARNING',
                'symbol': symbol,
                'return': current_return * 100,
                'threshold': var_95,
                'excess': abs_return - var_95,
                'timestamp': datetime.now()
            })
        
        for breach in breaches:
            self.alerts.append(breach)
        
        return breaches
    
    def get_recent_alerts(self, n=10):
        """Get n most recent alerts"""
        return list(self.alerts)[-n:]
    
    def get_alert_summary(self):
        """Get summary of all alerts"""
        return {
            'total_alerts': len(self.alerts),
            '95_breaches': self.breach_count['95%'],
            '99_breaches': self.breach_count['99%'],
            'recent': self.get_recent_alerts(5)
        }
    
    def reset_counts(self):
        """Reset breach counters"""
        self.breach_count = {'95%': 0, '99%': 0}
        self.alerts.clear()
