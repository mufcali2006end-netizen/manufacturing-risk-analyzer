import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Manufacturing Quote Risk Analyzer", page_icon="🔧", layout="wide")

st.title("🔧 Manufacturing Quote Risk Analyzer")
st.markdown("**Get data-driven confidence intervals for your manufacturing quotes**")
st.markdown("---")

st.sidebar.header("📊 Job Parameters")

st.sidebar.subheader("💰 Material Costs")
material_cost = st.sidebar.number_input("Base Material Cost ($)", min_value=100, max_value=50000, value=3500, step=100)
material_uncertainty = st.sidebar.slider("Material Cost Uncertainty (%)", min_value=5, max_value=40, value=12)
waste_pct = st.sidebar.slider("Expected Material Waste (%)", min_value=5, max_value=30, value=10)

st.sidebar.subheader("⏱️ Labor Estimates")
setup_hours = st.sidebar.number_input("Setup Time (hours)", min_value=0.5, max_value=40.0, value=4.0, step=0.5)
machining_hours = st.sidebar.number_input("Machining Time (hours)", min_value=1.0, max_value=500.0, value=35.0, step=1.0)
finishing_hours = st.sidebar.number_input("Finishing Time (hours)", min_value=0.5, max_value=40.0, value=5.0, step=0.5)
labor_uncertainty = st.sidebar.slider("Labor Time Uncertainty (%)", min_value=10, max_value=50, value=20)
labor_rate = st.sidebar.number_input("Labor Rate ($/hr)", min_value=30, max_value=200, value=75, step=5)

st.sidebar.subheader("🔩 Other Costs")
tooling_cost = st.sidebar.number_input("Tooling/Consumables ($)", min_value=50, max_value=5000, value=400, step=50)
subcontractor_cost = st.sidebar.number_input("Subcontractor Cost ($)", min_value=0, max_value=10000, value=800, step=100)
rework_probability = st.sidebar.slider("Rework Probability (%)", min_value=0, max_value=50, value=15)

st.sidebar.subheader("📈 Business Factors")
overhead_multiplier = st.sidebar.number_input("Overhead Multiplier", min_value=1.0, max_value=3.0, value=1.35, step=0.05)
profit_margin = st.sidebar.number_input("Profit Margin Multiplier", min_value=1.0, max_value=2.0, value=1.15, step=0.05)

n_simulations = 10000

if st.sidebar.button("🚀 Run Risk Analysis", type="primary"):
    
    with st.spinner("Running Monte Carlo simulation..."):
        
        mat_std = material_cost * (material_uncertainty / 100)
        raw_material = np.random.normal(material_cost, mat_std, n_simulations)
        waste = np.random.triangular(waste_pct*0.5, waste_pct, waste_pct*2, n_simulations) / 100
        material_total = raw_material * (1 + waste)
        
        setup_std = setup_hours * (labor_uncertainty / 100)
        machining_std = machining_hours * (labor_uncertainty / 100)
        finishing_std = finishing_hours * (labor_uncertainty / 100)
        
        setup_sim = np.random.normal(setup_hours, setup_std, n_simulations)
        machining_sim = np.random.normal(machining_hours, machining_std, n_simulations)
        finishing_sim = np.random.normal(finishing_hours, finishing_std, n_simulations)
        
        total_labor_hours = setup_sim + machining_sim + finishing_sim
        
        overtime = np.random.random(n_simulations) < 0.10
        effective_rate = np.where(overtime, labor_rate * 1.5, labor_rate)
        labor_cost = total_labor_hours * effective_rate
        
        needs_rework = np.random.random(n_simulations) < (rework_probability / 100)
        rework_hours = np.where(needs_rework, np.random.uniform(5, 15, n_simulations), 0)
        rework_cost = rework_hours * labor_rate
        
        direct_costs = material_total + labor_cost + tooling_cost + subcontractor_cost + rework_cost
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
    
    st.subheader("📈 Visualizations")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        ax1.hist(total_quote, bins=60, edgecolor='black', alpha=0.7, color='steelblue')
        ax1.axvline(median_cost, color='red', linestyle='--', linewidth=2, label='Median')
        ax1.axvline(p75, color='orange', linestyle='--', linewidth=2, label='75th percentile')
        ax1.axvline(p90, color='darkred', linestyle=':', linewidth=2, label='90th percentile')
        ax1.set_xlabel('Total Quote Price ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Cost Distribution', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        st.pyplot(fig1)
    
    with col_right:
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sorted_costs = np.sort(total_quote)
        cumulative = np.arange(1, n_simulations + 1) / n_simulations * 100
        ax2.plot(sorted_costs, cumulative, linewidth=2, color='darkgreen')
        ax2.axhline(50, color='red', linestyle='--', alpha=0.5, label='50%')
        ax2.axhline(75, color='orange', linestyle='--', alpha=0.5, label='75%')
        ax2.axhline(90, color='darkred', linestyle='--', alpha=0.5, label='90%')
        ax2.set_xlabel('Quote Price ($)', fontsize=11)
        ax2.set_ylabel('Probability (%)', fontsize=11)
        ax2.set_title('Cumulative Probability', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
        st.pyplot(fig2)
    
    st.subheader("💡 Quoting Recommendations")
    
    rec_col1, rec_col2 = st.columns(2)
    
    with rec_col1:
        st.info(f"**🎯 COMPETITIVE QUOTE**\n\n### ${median_cost:,.0f}\n\n- 50% confidence level\n- Use for: Competitive bidding\n- Risk: 50/50 chance of overrun")
    
    with rec_col2:
        st.success(f"**✅ CONSERVATIVE QUOTE**\n\n### ${p75:,.0f}\n\n- 75% confidence level\n- Use for: New customers, complex jobs\n- Risk premium: ${p75-median_cost:,.0f}")

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
