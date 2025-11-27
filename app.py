import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

st.set_page_config(page_title="Manufacturing Quote Risk Analyzer", page_icon="🔧", layout="wide")

st.title("🔧 Manufacturing Quote Risk Analyzer")
st.markdown("*Get data-driven confidence intervals for your manufacturing quotes*")
st.markdown("---")

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

# Function to generate PDF
def generate_pdf(job_name, results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>Manufacturing Quote Risk Analysis Report</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Job info
    if job_name:
        job_info = Paragraph(f"<b>Job Name:</b> {job_name}", styles['Normal'])
        elements.append(job_info)
    
    date_info = Paragraph(f"<b>Date Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
    elements.append(date_info)
    elements.append(Spacer(1, 20))
    
    # Key Results
    heading = Paragraph("<b>Key Results</b>", styles['Heading2'])
    elements.append(heading)
    elements.append(Spacer(1, 12))
    
    data = [
        ['Metric', 'Value'],
        ['Expected Cost', f"${results['mean']:,.0f}"],
        ['Median (50%)', f"${results['median']:,.0f}"],
        ['Conservative (75%)', f"${results['p75']:,.0f}"],
        ['High Confidence (90%)', f"${results['p90']:,.0f}"],
    ]
    
    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Recommendations
    heading = Paragraph("<b>Quoting Recommendations</b>", styles['Heading2'])
    elements.append(heading)
    elements.append(Spacer(1, 12))
    
    comp_rec = Paragraph(f"<b>Competitive Quote (50% confidence):</b> ${results['median']:,.0f}<br/>Use for competitive bidding and repeat customers.", styles['Normal'])
    elements.append(comp_rec)
    elements.append(Spacer(1, 12))
    
    cons_rec = Paragraph(f"<b>Conservative Quote (75% confidence):</b> ${results['p75']:,.0f}<br/>Use for new customers and complex jobs. Risk premium: ${results['p75'] - results['median']:,.0f}", styles['Normal'])
    elements.append(cons_rec)
    elements.append(Spacer(1, 20))
    
    # Detailed stats
    heading = Paragraph("<b>Detailed Statistics</b>", styles['Heading2'])
    elements.append(heading)
    elements.append(Spacer(1, 12))
    
    stats_data = [
        ['Percentile', 'Quote Price'],
        ['10th', f"${results['p10']:,.0f}"],
        ['25th', f"${results['p25']:,.0f}"],
        ['50th (Median)', f"${results['median']:,.0f}"],
        ['75th', f"${results['p75']:,.0f}"],
        ['90th', f"${results['p90']:,.0f}"],
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 150])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer = Paragraph("<i>Generated by Manufacturing Quote Risk Analyzer - Monte Carlo simulation with 10,000 iterations</i>", styles['Normal'])
    elements.append(footer)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main app logic
if st.sidebar.button("🚀 Run Risk Analysis", type="primary"):
    
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
        
        # Store results for PDF
        results = {
            'mean': mean_cost,
            'median': median_cost,
            'p10': p10,
            'p25': p25,
            'p75': p75,
            'p90': p90
        }
        
        # Store in session state
        st.session_state['results'] = results
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
    chart_df = pd.DataFrame({'Quote Price': total_quote})
    st.bar_chart(chart_df['Quote Price'].value_counts().sort_index().head(50), height=400)
    
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
    
    # PDF Download Button
    st.subheader("📄 Export Report")
    pdf_buffer = generate_pdf(job_name if job_name else "Untitled Job", results)
    st.download_button(
        label="⬇ Download PDF Report",
        data=pdf_buffer,
        file_name=f"risk_analysis_{job_name if job_name else 'report'}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary"
    )

else:
    st.info("👈 *Adjust parameters in sidebar and click 'Run Risk Analysis'*")
    
    st.markdown("""
    ### How to Use:
    
    1. Enter job parameters in sidebar
    2. Optionally add a job name for the report
    3. Click 'Run Risk Analysis'
    4. Review results and download PDF report
    """)

st.markdown("---")
st.markdown("Monte Carlo simulation with 10,000 iterations")
