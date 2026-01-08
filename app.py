import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

# Initialize session state for usage tracking
if 'usage_count' not in st.session_state:
    st.session_state['usage_count'] = 0
if 'is_pro' not in st.session_state:
    st.session_state['is_pro'] = False

st.set_page_config(page_title="Manufacturing Quote Risk Analyzer", page_icon="🔧", layout="wide")

st.title("🔧 Manufacturing Quote Risk Analyzer")
st.markdown("*Get data-driven confidence intervals for your manufacturing quotes*")
st.markdown("---")

# Tier indicator at top of sidebar
st.sidebar.title("🔧 Manufacturing Risk Analyzer")

# Pro Access via Code
st.sidebar.markdown("---")
st.sidebar.subheader("✨ Pro Access")
st.sidebar.caption("After subscribing, email falconmanagementllc25@gmail.com for your access code")

pro_code = st.sidebar.text_input("Enter Pro Code:", type="password", key="pro_code_input")

# Valid Pro codes - Add customer codes here as they subscribe
VALID_PRO_CODES = [
    "DEMO2025",  # For testing - remove after testing
    # Add customer codes here like:
    # "ACME-SHOP-JAN2025",
    # "SMITH-TOOLS-2025",
]

if pro_code and pro_code in VALID_PRO_CODES:
    st.session_state['is_pro'] = True
    is_pro = True
    st.sidebar.success("✅ Pro Activated!")
    st.sidebar.caption("📧 Support: falconmanagementllc25@gmail.com")
else:
    st.session_state['is_pro'] = False
    is_pro = False
    if pro_code and pro_code not in VALID_PRO_CODES:
        st.sidebar.error("❌ Invalid code")

if is_pro:
    st.sidebar.success("*PRO USER* - Unlimited analyses")
    st.sidebar.markdown("---")
    st.sidebar.caption("Need to cancel or update payment?")
    st.sidebar.markdown("📧 Email: falconmanagementllc25@gmail.com")
else:
    # Show free tier usage
    remaining = 3 - st.session_state['usage_count']
    if remaining > 0:
        st.sidebar.info(f"🆓 *Free Trial:* {remaining}/3 analyses remaining")
    else:
        st.sidebar.error("⚠ *Free limit reached!*")
        st.sidebar.markdown("### Upgrade to Pro")
        st.sidebar.markdown("$49.99/month**")
        st.sidebar.markdown("✅ Unlimited analyses")
        st.sidebar.markdown("✅ PDF reports with charts (coming soon)")
        st.sidebar.markdown("✅ Save scenarios")
        st.sidebar.markdown("✅ Priority support")
        st.sidebar.markdown("[*Subscribe Now →*](https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800)")
        
st.sidebar.markdown("---")
                 
# Sidebar inputs
st.sidebar.header("📊 Job Parameters")

job_name = st.sidebar.text_input("Job Name (optional)", placeholder="e.g., Bracket-2024-001")

st.sidebar.subheader("💰 Material Costs")
material_cost = st.sidebar.number_input("Base Material Cost ($)", min_value=100, max_value=50000, value=3500, step=100)
material_uncertainty = st.sidebar.slider("Material Cost Uncertainty (%)", min_value=5, max_value=40, value=12)
waste_pct = st.sidebar.slider("Expected Material Waste (%)", min_value=5, max_value=30, value=10)

st.sidebar.subheader("⏱ Labor Estimates")
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

# Text Report Generation
def generate_text_report(job_name, results, params):
    report = f"""
MANUFACTURING QUOTE RISK ANALYSIS REPORT
{'='*60}

Job Name: {job_name if job_name else 'Untitled Job'}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*60}
JOB PARAMETERS
{'='*60}

Material Costs:
  - Base Material Cost: ${params['material_cost']:,.0f}
  - Uncertainty: ±{params['material_uncertainty']}%
  - Expected Waste: {params['waste_pct']}%

Labor Estimates:
  - Setup Time: {params['setup_hours']} hours
  - Machining Time: {params['machining_hours']} hours
  - Finishing Time: {params['finishing_hours']} hours
  - Labor Rate: ${params['labor_rate']}/hour
  - Time Uncertainty: ±{params['labor_uncertainty']}%

Other Costs:
  - Tooling/Consumables: ${params['tooling_cost']:,.0f}
  - Subcontractor: ${params['subcontractor_cost']:,.0f}
  - Rework Probability: {params['rework_probability']}%

Business Factors:
  - Overhead Multiplier: {params['overhead_multiplier']}x
  - Profit Margin: {params['profit_margin']}x

{'='*60}
KEY RESULTS (Monte Carlo Simulation - 10,000 iterations)
{'='*60}

Expected Cost:          ${results['mean']:>12,.0f}
Median (50%):           ${results['median']:>12,.0f}
Conservative (75%):     ${results['p75']:>12,.0f}
High Confidence (90%):  ${results['p90']:>12,.0f}

{'='*60}
QUOTING RECOMMENDATIONS
{'='*60}

🎯 COMPETITIVE QUOTE (50% confidence): ${results['median']:,.0f}
   - Use for: Competitive bidding, repeat customers
   - Risk: 50/50 chance of cost overrun

✅ CONSERVATIVE QUOTE (75% confidence): ${results['p75']:,.0f}
   - Use for: New customers, complex jobs
   - Risk Premium: ${results['p75'] - results['median']:,.0f}
   - Only 25% chance of exceeding this price

{'='*60}
DETAILED STATISTICS
{'='*60}

10th Percentile:        ${results['p10']:>12,.0f}  (10% of outcomes below)
25th Percentile:        ${results['p25']:>12,.0f}  (25% of outcomes below)
50th Percentile:        ${results['median']:>12,.0f}  (Median - half above/below)
75th Percentile:        ${results['p75']:>12,.0f}  (75% of outcomes below)
90th Percentile:        ${results['p90']:>12,.0f}  (90% of outcomes below)

{'='*60}
COST BREAKDOWN (Average Values)
{'='*60}

Material (with waste):  ${results['avg_material']:>12,.0f}
Labor:                  ${results['avg_labor']:>12,.0f}
Tooling:                ${params['tooling_cost']:>12,.0f}
Subcontractor:          ${params['subcontractor_cost']:>12,.0f}
Rework:                 ${results['avg_rework']:>12,.0f}
                        {'─'*30}
Direct Costs:           ${results['avg_direct']:>12,.0f}
After Overhead & Profit:${results['mean']:>12,.0f}

{'='*60}

Generated by Manufacturing Quote Risk Analyzer
Monte Carlo Simulation with 10,000 iterations
    """
    return report
    
# Check if user can run analysis
can_run = st.session_state['is_pro'] or st.session_state['usage_count'] < 3

if not can_run:
    st.error("🚫 You've used all 3 free analyses!")
    st.markdown("### Upgrade to Pro for Unlimited Access")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("*Free Tier:*")
        st.markdown("- 3 analyses/month")
        st.markdown("- Text reports")
        st.markdown("- Basic features")
    with col2:
        st.markdown("*Pro Tier - $49.99/month:*")
        st.markdown("- ✅ Unlimited analyses")
        st.markdown("- ✅ PDF reports with charts")
        st.markdown("- ✅ Save scenarios")
        st.markdown("- ✅ Priority support")
    st.markdown("[*Subscribe to Pro →*](https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800)")
    st.stop()

# Main App Logic
if st.sidebar.button("🚀 Run Risk Analysis", type="primary"):

    # Increment usage counter for free users
    if not st.session_state['is_pro']:
        st.session_state['usage_count'] += 1

    with st.spinner("Running Monte Carlo simulation..."):
        
        # Material simulation
        mat_std = material_cost * (material_uncertainty / 100)
        raw_material = np.random.normal(material_cost, mat_std, n_simulations)
        waste = np.random.triangular(waste_pct*0.5, waste_pct, waste_pct*2, n_simulations) / 100
        material_total = raw_material * (1 + waste)
        
        # Labor simulation
        setup_std = setup_hours * (labor_uncertainty / 100)
        machining_std = machining_hours * (labor_uncertainty / 100)
        finishing_std = finishing_hours * (labor_uncertainty / 100)
        
        setup_sim = np.random.normal(setup_hours, setup_std, n_simulations)
        machining_sim = np.random.normal(machining_hours, machining_std, n_simulations)
        finishing_sim = np.random.normal(finishing_hours, finishing_std, n_simulations)
        
        total_labor_hours = setup_sim + machining_sim + finishing_sim
        
        # Overtime risk
        overtime = np.random.random(n_simulations) < 0.10
        effective_rate = np.where(overtime, labor_rate * 1.5, labor_rate)
        labor_cost = total_labor_hours * effective_rate
        
        # Rework simulation
        needs_rework = np.random.random(n_simulations) < (rework_probability / 100)
        rework_hours = np.where(needs_rework, np.random.uniform(5, 15, n_simulations), 0)
        rework_cost = rework_hours * labor_rate
        
        # Total cost
        direct_costs = material_total + labor_cost + tooling_cost + subcontractor_cost + rework_cost
        total_quote = direct_costs * overhead_multiplier * profit_margin
        
        # Calculate statistics
        mean_cost = total_quote.mean()
        median_cost = np.percentile(total_quote, 50)
        p10 = np.percentile(total_quote, 10)
        p25 = np.percentile(total_quote, 25)
        p75 = np.percentile(total_quote, 75)
        p90 = np.percentile(total_quote, 90)
        
        # Store results
        results = {
            'mean': mean_cost,
            'median': median_cost,
            'p10': p10,
            'p25': p25,
            'p75': p75,
            'p90': p90,
            'avg_material': material_total.mean(),
            'avg_labor': labor_cost.mean(),
            'avg_rework': rework_cost.mean(),
            'avg_direct': direct_costs.mean()
        }
        
        params = {
            'material_cost': material_cost,
            'material_uncertainty': material_uncertainty,
            'waste_pct': waste_pct,
            'setup_hours': setup_hours,
            'machining_hours': machining_hours,
            'finishing_hours': finishing_hours,
            'labor_rate': labor_rate,
            'labor_uncertainty': labor_uncertainty,
            'tooling_cost': tooling_cost,
            'subcontractor_cost': subcontractor_cost,
            'rework_probability': rework_probability,
            'overhead_multiplier': overhead_multiplier,
            'profit_margin': profit_margin
        }
        
        st.session_state['results'] = results
        st.session_state['params'] = params
        st.session_state['total_quote'] = total_quote
        
    st.success("✅ Analysis Complete!")
    
    # Key Results
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
    
    # Distribution chart
    st.subheader("📈 Cost Distribution")

    # Create histogram bins
    hist_values, bin_edges = np.histogram(total_quote, bins=50)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Create dataframe for chart
    hist_df = pd.DataFrame({'Cost Range' : [f"${int(x):,}" for x in bin_centers],'Frequency': hist_values})

    st.bar_chart(hist_df.set_index('Cost Range')['Frequency'], height=400)

    # Add summary stats below chart
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Minimum", f"${total_quote.min():,.0f}")
    with col_b:
        st.metric("Average", f"${total_quote.mean():,.0f}")
    with col_c:
        st.metric("Maximum", f"${total_quote.max():,.0f}")
    
    # Recommendations
    st.subheader("💡 Quoting Recommendations")
    
    rec_col1, rec_col2 = st.columns(2)
    
    with rec_col1:
        st.info(f"🎯 COMPETITIVE QUOTE**\n\n### ${median_cost:,.0f}\n\n- 50% confidence level\n- Use for: Competitive bidding\n- Risk: 50/50 chance of overrun")
    
    with rec_col2:
        st.success(f"✅ CONSERVATIVE QUOTE**\n\n### ${p75:,.0f}\n\n- 75% confidence level\n- Use for: New customers, complex jobs\n- Risk premium: ${p75-median_cost:,.0f}")
    
    # Statistics table
    st.subheader("📋 Detailed Statistics")
    stats_df = pd.DataFrame({
        'Percentile': ['10th', '25th', '50th (Median)', '75th', '90th'],
        'Quote Price': [f"${p10:,.0f}", f"${p25:,.0f}", f"${median_cost:,.0f}", f"${p75:,.0f}", f"${p90:,.0f}"]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    # Cost Breakdown
    st.subheader("💵 Average Cost Breakdown")
    breakdown_df = pd.DataFrame({
        'Component': ['Material (w/ waste)', 'Labor', 'Tooling', 'Subcontractor', 'Rework', 'Total Direct'],
        'Cost': [
            f"${material_total.mean():,.0f}",
            f"${labor_cost.mean():,.0f}",
            f"${tooling_cost:,.0f}",
            f"${subcontractor_cost:,.0f}",
            f"${rework_cost.mean():,.0f}",
            f"${direct_costs.mean():,.0f}"
        ]
    })
    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
    
    # Text Report Download
    st.subheader("📄 Export Report")
    text_report = generate_text_report(job_name if job_name else "Untitled Job", results, params)
    
    st.download_button(
        label="⬇ Download Text Report",
        data=text_report,
        file_name=f"risk_analysis_{job_name.replace(' ', '') if job_name else 'report'}{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        type="primary"
    )

else:
    st.info("👈 *Adjust parameters in sidebar and click 'Run Risk Analysis'*")
    
    st.markdown("""
    ### How to Use:
    
    1. Enter your job parameters in the sidebar
    2. Optionally add a job name for the report
    3. Click 'Run Risk Analysis'
    4. Download detailed text report
    
    ### Features:
    - ✅ Monte Carlo simulation (10,000 iterations)
    - ✅ Multiple confidence levels (50%, 75%, 90%)
    - ✅ Detailed cost breakdown
    - ✅ Downloadable reports
    - ✅ Conservative & competitive quotes
    """)

st.markdown("---")
st.markdown("Manufacturing Quote Risk Analyzer v2.1 | Built with Monte Carlo simulation")







