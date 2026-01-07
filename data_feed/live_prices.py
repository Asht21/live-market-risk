import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import pytz

class MarketDataFeed:
    """
    Intelligent market data feed that:
    - Pulls live data during market hours
    - Uses most recent data when market is closed
    - Handles NSE India (Nifty 50) market hours: 9:15 AM - 3:30 PM IST
    """
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)
        
        # Asset universe
        self.assets = {
            '^NSEI': {'name': 'Nifty 50', 'position': 10000000},  # 1 Cr
            'RELIANCE.NS': {'name': 'Reliance Industries', 'position': 5000000},
            'TCS.NS': {'name': 'TCS', 'position': 5000000},
            'HDFCBANK.NS': {'name': 'HDFC Bank', 'position': 7500000},
            'INFY.NS': {'name': 'Infosys', 'position': 4000000},
        }
        
        self.current_data = {}
        self.last_update = None
        
    def is_market_open(self):
        """Check if NSE market is currently open"""
        now = datetime.now(self.ist)
        
        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if within trading hours
        current_time = now.time()
        if self.market_open <= current_time <= self.market_close:
            return True
        
        return False
    
    def get_market_status(self):
        """Get detailed market status"""
        now = datetime.now(self.ist)
        is_open = self.is_market_open()
        
        if is_open:
            return {
                'status': 'OPEN',
                'message': 'Market is currently trading',
                'time': now.strftime('%H:%M:%S IST'),
                'mode': 'LIVE'
            }
        else:
            if now.weekday() >= 5:
                reason = 'Weekend'
            elif now.time() < self.market_open:
                reason = 'Pre-market'
            else:
                reason = 'After-hours'
            
            return {
                'status': 'CLOSED',
                'message': f'Market closed ({reason})',
                'time': now.strftime('%H:%M:%S IST'),
                'mode': 'HISTORICAL'
            }
    
    def fetch_data(self, symbol, period='1y', interval='1d'):
        """
        Fetch market data intelligently:
        - Live data if market is open
        - Most recent historical if closed
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Always fetch historical data first
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"Warning: No data available for {symbol}")
                return None
            
            # If market is open, try to get latest intraday
            if self.is_market_open():
                try:
                    live_df = ticker.history(period='1d', interval='1m')
                    if not live_df.empty:
                        # Append latest price to historical data
                        latest_price = live_df['Close'].iloc[-1]
                        latest_time = live_df.index[-1]
                        
                        # Add to dataframe
                        new_row = pd.DataFrame({
                            'Close': [latest_price],
                            'Open': [live_df['Open'].iloc[-1]],
                            'High': [live_df['High'].iloc[-1]],
                            'Low': [live_df['Low'].iloc[-1]],
                            'Volume': [live_df['Volume'].iloc[-1]]
                        }, index=[latest_time])
                        
                        df = pd.concat([df, new_row])
                except:
                    pass  # Fallback to historical only
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_all_assets_data(self):
        """Fetch data for all assets in portfolio"""
        print("\nFetching market data...")
        
        for symbol in self.assets.keys():
            print(f"  → {symbol} ({self.assets[symbol]['name']})...", end=" ")
            df = self.fetch_data(symbol)
            
            if df is not None:
                self.current_data[symbol] = df
                print(f"✓ ({len(df)} data points)")
            else:
                print("✗ Failed")
        
        self.last_update = datetime.now(self.ist)
        return self.current_data
    
    def get_latest_prices(self):
        """Get latest prices for all assets"""
        if not self.current_data:
            self.get_all_assets_data()
        
        prices = {}
        for symbol, df in self.current_data.items():
            if df is not None and not df.empty:
                prices[symbol] = {
                    'price': df['Close'].iloc[-1],
                    'timestamp': df.index[-1],
                    'change_pct': ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
                }
        
        return prices