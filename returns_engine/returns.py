import pandas as pd
import numpy as np

class ReturnsEngine:
    """Calculate returns, volatility, and related metrics"""
    
    def calculate_returns(self, price_data):
        """Calculate daily log returns"""
        if price_data is None or len(price_data) < 2:
            return None
        
        returns = np.log(price_data['Close'] / price_data['Close'].shift(1))
        return returns.dropna()
    
    def calculate_volatility(self, returns, window=30, annualize=True):
        """Calculate rolling volatility"""
        vol = returns.rolling(window=window).std()
        
        if annualize:
            vol = vol * np.sqrt(252)  # Annualize
        
        return vol
    
    def get_summary_stats(self, returns):
        """Get summary statistics for returns"""
        if returns is None or len(returns) == 0:
            return None
        
        return {
            'mean': returns.mean() * 252,  # Annualized
            'std': returns.std() * np.sqrt(252),  # Annualized
            'skew': returns.skew(),
            'kurtosis': returns.kurtosis(),
            'min': returns.min(),
            'max': returns.max(),
            'sharpe': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        }
