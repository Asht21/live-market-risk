import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

class RiskDashboard:
    """Streamlit dashboard for real-time risk monitoring"""
    
    def __init__(self, data_feed, returns_engine, var_calculator, 
                 backtest_engine, stress_engine, alert_monitor):
        self.data_feed = data_feed
        self.returns_engine = returns_engine
        self.var_calculator = var_calculator
        self.backtest_engine = backtest_engine
        self.stress_engine = stress_engine
        self.alert_monitor = alert_monitor
        
        # Session state
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
    
    def run(self):
        """Main dashboard loop"""
        st.set_page_config(
            page_title="Live Market Risk Monitor",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
            <style>
            .big-metric { font-size: 24px; font-weight: bold; }
            .green-text { color: #00ff00; }
            .yellow-text { color: #ffff00; }
            .red-text { color: #ff0000; }
            </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.title("🎯 Live Market Risk Monitoring System")
        st.markdown("**FRM-Aligned Risk Management** | Real-time VaR, ES, Backtesting & Stress Testing")
        
        # Sidebar
        with st.sidebar:
            st.header("⚙️ Controls")
            
            # Market status
            status = self.data_feed.get_market_status()
            status_color = "🟢" if status['status'] == 'OPEN' else "🔴"
            st.markdown(f"### {status_color} Market Status")
            st.info(f"**{status['status']}** - {status['message']}\n\n{status['time']}")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=st.session_state.auto_refresh)
            st.session_state.auto_refresh = auto_refresh
            
            # Manual refresh
            if st.button("🔄 Refresh Data Now"):
                self.alert_monitor.reset_counts()
                st.rerun()
            
            # Asset selection
            st.markdown("---")
            selected_asset = st.selectbox(
                "Select Asset",
                options=list(self.data_feed.assets.keys()),
                format_func=lambda x: f"{x} - {self.data_feed.assets[x]['name']}"
            )
            
            # Time horizon
            lookback = st.selectbox("Lookback Period", [30, 60, 90, 180, 252], index=4)
        
        # Fetch data
        with st.spinner("Fetching market data..."):
            all_data = self.data_feed.get_all_assets_data()
        
        if selected_asset not in all_data or all_data[selected_asset] is None:
            st.error(f"Unable to fetch data for {selected_asset}")
            return
        
        # Process selected asset
        price_data = all_data[selected_asset].tail(lookback)
        returns = self.returns_engine.calculate_returns(price_data)
        
        if returns is None or len(returns) < 10:
            st.error(f"Insufficient data for {selected_asset}. Need at least 10 data points.")
            return
        
        position_value = self.data_feed.assets[selected_asset]['position']
        
        # Calculate metrics
        var_metrics = self.var_calculator.calculate_all_metrics(returns, position_value)
        backtest_results = self.backtest_engine.backtest_results(returns, var_metrics, position_value)
        stats = self.returns_engine.get_summary_stats(returns)
        
        if not var_metrics or not stats:
            st.error("Unable to calculate risk metrics. Please check data quality.")
            return
        
        # Main metrics row
        col1, col2, col3, col4 = st.columns(4)
        # Extract VaR metrics
        var_95_hist = var_metrics.get('var_95%_hist', {})
        var_99_hist = var_metrics.get('var_99%_hist', {})
        
        # ================= ALERT TRIGGER =================
        latest_return = returns.iloc[-1]
        
        var_95 = var_95_hist.get('var_return', 0)
        var_99 = var_99_hist.get('var_return', 0)
        
        self.alert_monitor.check_breach(
            current_return=latest_return,
            var_95=var_95,
            var_99=var_99,
            symbol=selected_asset
        )
        # =================================================
        with col1:
            st.metric("Position Value", f"₹{position_value/1_000_000:.1f}M")
            st.metric("Annual Volatility", f"{stats['std']*100:.2f}%")
        
        with col2:
            var_95_hist = var_metrics.get('var_95%_hist', {})
            st.metric("VaR (95%, 1-day)", 
                     f"₹{var_95_hist.get('var_dollar', 0)/1000:.0f}K",
                     f"{var_95_hist.get('var_return', 0):.3f}%")
        
        with col3:
            var_99_hist = var_metrics.get('var_99%_hist', {})
            st.metric("VaR (99%, 1-day)", 
                     f"₹{var_99_hist.get('var_dollar', 0)/1000:.0f}K",
                     f"{var_99_hist.get('var_return', 0):.3f}%")
        
        with col4:
            es_95 = var_metrics.get('es_95%', {})
            st.metric("Expected Shortfall (95%)", 
                     f"₹{es_95.get('es_dollar', 0)/1000:.0f}K",
                     f"{es_95.get('es_return', 0):.3f}%")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Price History")
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(
                x=price_data.index,
                y=price_data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='cyan', width=2)
            ))
            fig_price.update_layout(
                template='plotly_dark',
                height=400,
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                showlegend=True
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            st.subheader("📊 Returns Distribution")
            fig_returns = go.Figure()
            fig_returns.add_trace(go.Histogram(
                x=returns * 100,
                nbinsx=50,
                name='Returns',
                marker_color='lightblue'
            ))
            # Add VaR lines
            fig_returns.add_vline(x=-var_95_hist.get('var_return', 0), 
                                 line_dash="dash", line_color="yellow",
                                 annotation_text="VaR 95%")
            fig_returns.add_vline(x=-var_99_hist.get('var_return', 0), 
                                 line_dash="dash", line_color="red",
                                 annotation_text="VaR 99%")
            fig_returns.update_layout(
                template='plotly_dark',
                height=400,
                xaxis_title="Daily Return (%)",
                yaxis_title="Frequency"
            )
            st.plotly_chart(fig_returns, use_container_width=True)
        
        # Backtesting results
        st.subheader("🔍 Backtesting Results (Basel Framework)")
        if backtest_results:
            col1, col2 = st.columns(2)
            
            for idx, (level, results) in enumerate(backtest_results.items()):
                with col1 if idx == 0 else col2:
                    traffic_color = {
                        'GREEN': '🟢',
                        'YELLOW': '🟡',
                        'RED': '🔴'
                    }.get(results['traffic_light'], '⚪')
                    
                    st.markdown(f"### {traffic_color} VaR {level}")
                    st.write(f"**Breaches:** {results['breaches']} / {results['total_days']} days")
                    st.write(f"**Breach Rate:** {results['breach_rate']*100:.2f}% (Expected: {results['expected_rate']*100:.2f}%)")
                    st.write(f"**Status:** {results['traffic_message']}")
                    
                    # Kupiec test
                    kupiec = results['kupiec_test']
                    st.write(f"**Kupiec Test:** {kupiec['interpretation']}")
                    st.write(f"  - LR Statistic: {kupiec['lr_statistic']:.3f}")
                    st.write(f"  - P-value: {kupiec['p_value']:.4f}")
        
        # Stress Testing
        st.subheader("⚠️ Stress Testing & Scenario Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            scenario_options = list(self.stress_engine.scenarios.keys())
            selected_scenario = st.selectbox(
                "Select Stress Scenario",
                options=scenario_options,
                format_func=lambda x: self.stress_engine.scenarios[x]['name']
            )
            
            if st.button("🔥 Run Stress Test"):
                # Get all position values
                position_values = {k: v['position'] for k, v in self.data_feed.assets.items()}
                
                stress_result = self.stress_engine.apply_scenario(
                    selected_scenario, 
                    position_values, 
                    None
                )
                
                if stress_result:
                    st.markdown("---")
                    st.markdown(f"### Scenario: {stress_result['scenario_name']}")
                    st.error(f"**Total Portfolio Loss:** ₹{stress_result['total_loss']/1_000_000:.2f}M")
                    
                    # Asset breakdown
                    st.write("**Loss Breakdown by Asset:**")
                    breakdown_df = pd.DataFrame([
                        {
                            'Asset': asset,
                            'Position (₹M)': data['position']/1_000_000,
                            'Loss (₹M)': data['loss']/1_000_000,
                            'Loss %': f"{data['loss_pct']:.2f}%"
                        }
                        for asset, data in stress_result['asset_breakdown'].items()
                    ])
                    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
                    
                    # Compare to VaR
                    if var_95_hist and var_99_hist:
                        var_95_total = var_95_hist.get('var_dollar', 0)
                        var_99_total = var_99_hist.get('var_dollar', 0)
                        
                        st.write("**Stress Loss vs VaR:**")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            ratio_95 = stress_result['total_loss'] / var_95_total if var_95_total > 0 else 0
                            st.metric("vs VaR 95%", f"{ratio_95:.2f}x")
                        with col_b:
                            ratio_99 = stress_result['total_loss'] / var_99_total if var_99_total > 0 else 0
                            st.metric("vs VaR 99%", f"{ratio_99:.2f}x")
        
        with col2:
            st.markdown("**Available Scenarios:**")
            for key, scenario in self.stress_engine.scenarios.items():
                st.write(f"• {scenario['name']}")
            
            st.markdown("---")
            st.markdown("**Model Limitations:**")
            st.caption("• Historical VaR assumes past = future")
            st.caption("• Normal distributions underestimate tails")
            st.caption("• Correlations break in crisis")
            st.caption("• Liquidity risk not captured")
            st.caption("• Static positions assumed")
        
        # Alert Monitor
        st.subheader("🚨 Live Breach Monitor")
        
        alert_summary = self.alert_monitor.get_alert_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", alert_summary['total_alerts'])
        with col2:
            st.metric("95% VaR Breaches", alert_summary['95_breaches'])
        with col3:
            st.metric("99% VaR Breaches", alert_summary['99_breaches'])
        
        # Recent alerts
        recent_alerts = alert_summary['recent']
        if recent_alerts:
            st.write("**Recent Breaches:**")
            for alert in recent_alerts:
                severity_icon = "🔴" if alert['severity'] == 'CRITICAL' else "🟡"
                st.warning(
                    f"{severity_icon} **{alert['level']} Breach** - {alert['symbol']} | "
                    f"Return: {alert['return']:.3f}% | "
                    f"Threshold: {alert['threshold']:.3f}% | "
                    f"Excess: {alert['excess']:.3f}% | "
                    f"{alert['timestamp'].strftime('%H:%M:%S')}"
                )
        else:
            st.success("✅ No breaches detected - Model performing within limits")
        
        # Summary Statistics
        st.subheader("📊 Return Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean (Annual)", f"{stats['mean']*100:.2f}%")
            st.metric("Volatility (Annual)", f"{stats['std']*100:.2f}%")
        
        with col2:
            st.metric("Sharpe Ratio", f"{stats['sharpe']:.3f}")
            st.metric("Skewness", f"{stats['skew']:.3f}")
        
        with col3:
            st.metric("Kurtosis", f"{stats['kurtosis']:.3f}")
            st.metric("Min Return", f"{stats['min']*100:.3f}%")
        
        with col4:
            st.metric("Max Return", f"{stats['max']*100:.3f}%")
            latest_return = returns.iloc[-1] * 100
            st.metric("Latest Return", f"{latest_return:.3f}%")
        
        # VaR Comparison Table
        st.subheader("📈 VaR Methods Comparison")
        
        var_comparison = []
        for conf in ['95%', '99%']:
            hist_key = f'var_{conf}_hist'
            param_key = f'var_{conf}_param'
            es_key = f'es_{conf}'
            
            if hist_key in var_metrics:
                var_comparison.append({
                    'Confidence Level': conf,
                    'Historical VaR (₹K)': f"{var_metrics[hist_key]['var_dollar']/1000:.1f}",
                    'Historical VaR (%)': f"{var_metrics[hist_key]['var_return']:.3f}",
                    'Parametric VaR (₹K)': f"{var_metrics[param_key]['var_dollar']/1000:.1f}" if param_key in var_metrics else 'N/A',
                    'Parametric VaR (%)': f"{var_metrics[param_key]['var_return']:.3f}" if param_key in var_metrics else 'N/A',
                    'Expected Shortfall (₹K)': f"{var_metrics[es_key]['es_dollar']/1000:.1f}" if es_key in var_metrics else 'N/A',
                    'Expected Shortfall (%)': f"{var_metrics[es_key]['es_return']:.3f}" if es_key in var_metrics else 'N/A',
                })
        
        if var_comparison:
            df_comparison = pd.DataFrame(var_comparison)
            st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Rolling VaR Chart
        st.subheader("📉 Rolling VaR (30-day window)")
        
        # Calculate rolling VaR
        window = 30
        rolling_var_95 = []
        rolling_var_99 = []
        dates = []
        
        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]
            sorted_rets = np.sort(window_returns)
            
            var_95_idx = int(len(sorted_rets) * 0.05)
            var_99_idx = int(len(sorted_rets) * 0.01)
            
            rolling_var_95.append(abs(sorted_rets[var_95_idx]) * 100)
            rolling_var_99.append(abs(sorted_rets[var_99_idx]) * 100)
            dates.append(window_returns.index[-1])
        
        fig_rolling = go.Figure()
        fig_rolling.add_trace(go.Scatter(
            x=dates,
            y=rolling_var_95,
            mode='lines',
            name='VaR 95%',
            line=dict(color='yellow', width=2)
        ))
        fig_rolling.add_trace(go.Scatter(
            x=dates,
            y=rolling_var_99,
            mode='lines',
            name='VaR 99%',
            line=dict(color='red', width=2)
        ))
        fig_rolling.update_layout(
            template='plotly_dark',
            height=400,
            xaxis_title="Date",
            yaxis_title="VaR (%)",
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig_rolling, use_container_width=True)
        
        # Portfolio Overview
        st.subheader("💼 Portfolio Overview")
        
        portfolio_data = []
        total_portfolio_value = 0
        
        for symbol, info in self.data_feed.assets.items():
            position_val = info['position']
            total_portfolio_value += position_val
            
            # Get latest price if available
            latest_price = "N/A"
            change_pct = "N/A"
            
            if symbol in all_data and all_data[symbol] is not None:
                df = all_data[symbol]
                if len(df) >= 2:
                    latest_price = f"₹{df['Close'].iloc[-1]:.2f}"
                    change = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
                    change_pct = f"{change:+.2f}%"
            
            portfolio_data.append({
                'Symbol': symbol,
                'Name': info['name'],
                'Position (₹M)': f"{position_val/1_000_000:.2f}",
                'Latest Price': latest_price,
                'Change': change_pct,
                'Weight': f"{(position_val/total_portfolio_value)*100:.1f}%"
            })
        
        df_portfolio = pd.DataFrame(portfolio_data)
        st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
        
        st.metric("Total Portfolio Value", f"₹{total_portfolio_value/1_000_000:.2f}M")
        
        # Footer with system info
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"📅 Last Update: {self.data_feed.last_update.strftime('%Y-%m-%d %H:%M:%S IST') if self.data_feed.last_update else 'N/A'}")
        
        with col2:
            st.caption(f"🔢 Data Points: {len(returns)} days")
        
        with col3:
            st.caption("📊 Method: Historical Simulation VaR")
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time.sleep(30)
            st.rerun()