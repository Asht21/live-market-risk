import sys
import time
from datetime import datetime
from dashboard.app import RiskDashboard
from data_feed.live_prices import MarketDataFeed
from returns_engine.returns import ReturnsEngine
from risk_metrics.var_calculator import VaRCalculator
from back_testing.validator import BacktestEngine
from stress_testing.scenarios import StressTestEngine
from alerts.monitor import AlertMonitor

def main():
    print("=" * 80)
    print("LIVE MARKET RISK MONITORING SYSTEM (FRM-ALIGNED)")
    print("=" * 80)
    print(f"System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print()
    
    # Initialize components
    print("[1/7] Initializing Market Data Feed...")
    data_feed = MarketDataFeed()
    
    print("[2/7] Initializing Returns Engine...")
    returns_engine = ReturnsEngine()
    
    print("[3/7] Initializing VaR Calculator...")
    var_calculator = VaRCalculator()
    
    print("[4/7] Initializing Backtest Engine...")
    backtest_engine = BacktestEngine()
    
    print("[5/7] Initializing Stress Test Engine...")
    stress_engine = StressTestEngine()
    
    print("[6/7] Initializing Alert Monitor...")
    alert_monitor = AlertMonitor()
    
    print("[7/7] Launching Dashboard...")
    print()
    
    # Launch dashboard
    dashboard = RiskDashboard(
        data_feed=data_feed,
        returns_engine=returns_engine,
        var_calculator=var_calculator,
        backtest_engine=backtest_engine,
        stress_engine=stress_engine,
        alert_monitor=alert_monitor
    )
    
    dashboard.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutting down system...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)