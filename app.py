import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Manufacturing Quote Risk Analyzer", page_icon="🔧", layout="wide")

st.title("🔧 Manufacturing Quote Risk Analyzer")
st.markdown("**Get data-driven confidence intervals for your manufacturing quotes**")
st.markdown("---")

st.sidebar.header("📊 Job Parameters")

st.sidebar.subheader("💰 Material Costs")
material_cost = st.sidebar.number_input("Base Material Cost ($)", min_value=100, max_value=50000, value=3500, step=100)
material_uncertainty = st.sidebar.slider("Material Cost Uncertainty (%)", min_value=5, max_value=40, value=12)

st.sidebar.subheader("⏱️ Labor Estimates")
machining_hours = st.sidebar.number_input("Machining Time (hours)", min_value=1.0, max_value=500.0, value=35.0, step=1.0)
labor_uncertainty = st.sidebar.slider("Labor Time Uncertainty (%)", min_value=10, max_value=50, value=20)
labor_rate = st.sidebar.number_input("Labor Rate ($/hr)", min_value=30, max_value=200, value=75, step=5)

st.sidebar.subheader("📈 Business Factors")
overhead_multiplier = st.sidebar.number_input("Overhead Multiplier", min_value=1.0, max_value=3.0, value=1.35, step=0.05)
profit_margin = st.sidebar.number_input("Profit Margin Multiplier", min_value=1.0, max_value=2.0, value=1.15, step=0.05)

n_simulations = 10000

if st.sidebar.button("🚀 Run Risk Analysis", type="primary"):
    
    with st.spinner("Running Monte Carlo simulation..."):
        
        # Material simulation
        mat_std = material_cost * (material_uncertainty / 100)
        material_total = np.random.normal(material_cost, mat_std, n_simulations)
        
        # Labor simulation
        labor_std = machining_hours * (labor_uncertainty / 100)
        labor_hours_sim = np.random.normal(machining_hours, labor_std, n_simulations)
        labor_cost = labor_hours_sim * labor_rate
        
        # Total cost
        direct_costs = material_total + labor_cost
        total_quote = direct_costs * overhead_multiplier * profit_margin
        
        mean_cost = total_quote.mean()
        median_cost = np.percentile(total_quote, 50)
        p75 = np.percentile(total_quote, 75)
        p90 = np.percentile(total_quote, 90)
        
    st.success("✅ Analysis Complete!")
    
    st.subheader("📊 Key Results")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Expected Cost", f"${mean_cost:,.0f}")
    with col2:
        st.metric("Median (50%)", f"${median_cost:,.0f}")
    with col3:
        st.metric("Conservative (75%)", f"${p75:,.0f}", delta=f"+${p75-median_cost:,.0f}")
    with col4:
        st.metric("High Confidence (90%)", f"${p90:,.0f}", delta=f"+${p90-median_cost:,.0f}")
    
    st.subheader("📈 Cost Distribution")
    
    # Use Streamlit's built-in chart instead of matplotlib
    chart_df = pd.DataFrame({'Quote Price': total_quote})
    st.bar_chart(chart_df['Quote Price'].value_counts().sort_index(), height=400)
    
    st.subheader("💡 Quoting Recommendations")
    
    rec_col1, rec_col2 = st.columns(2)
    
    with rec_col1:
        st.info(f"**🎯 COMPETITIVE QUOTE**\n\n### ${median_cost:,.0f}\n\n- 50% confidence level\n- Use for: Competitive bidding\n- Risk: 50/50 chance of overrun")
    
    with rec_col2:
        st.success(f"**✅ CONSERVATIVE QUOTE**\n\n### ${p75:,.0f}\n\n- 75% confidence level\n- Use for: New customers, complex jobs\n- Risk premium: ${p75-median_cost:,.0f}")
    
    # Statistics table
    st.subheader("📋 Detailed Statistics")
    stats_df = pd.DataFrame({
        'Percentile': ['10th', '25th', '50th (Median)', '75th', '90th'],
        'Quote Price': [
            f"${np.percentile(total_quote, 10):,.0f}",
            f"${np.percentile(total_quote, 25):,.0f}",
            f"${median_cost:,.0f}",
            f"${p75:,.0f}",
            f"${p90:,.0f}"
        ]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

else:
    st.info("👈 **Adjust parameters in sidebar and click 'Run Risk Analysis'**")
    
    st.markdown("""
    ### How to Use:
    
    1. Enter job parameters in sidebar
    2. Click 'Run Risk Analysis'
    3. Review results and recommendations
    """)

st.markdown("---")
st.markdown("*Monte Carlo simulation with 10,000 iterations*")
