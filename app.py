import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import json
import io

# ── Page config must be FIRST ──────────────────────────────────────────────
st.set_page_config(
    page_title="Manufacturing Quote Risk Analyzer",
    page_icon="🔧",
    layout="wide"
)

# Browser compatibility notice
st.warning("⚠️ *iPhone/iPad users:* iOS 17+ required. iOS 16 and older are not compatible.")

# ── Session state ───────────────────────────────────────────────────────────
if 'usage_count'      not in st.session_state: st.session_state['usage_count']      = 0
if 'is_pro'           not in st.session_state: st.session_state['is_pro']           = False
if 'saved_scenarios'  not in st.session_state: st.session_state['saved_scenarios']  = {}
if 'quote_templates'  not in st.session_state: st.session_state['quote_templates']  = {}   # PRO FEATURE 4
if 'win_loss_log'     not in st.session_state: st.session_state['win_loss_log']     = []   # PRO FEATURE 5

# ── Pro code check ──────────────────────────────────────────────────────────
VALID_PRO_CODES = [
    "DEMO2025",
    "ACME-SHOP-JAN2025",
    "FALCON-X7K2-PRO",
]

st.sidebar.title("🔧 Manufacturing Risk Analyzer")
st.sidebar.markdown("---")
st.sidebar.subheader("✨ Pro Access")
st.sidebar.caption("After subscribing, your Pro access code will be emailed to you automatically. Check your inbox!")

pro_code = st.sidebar.text_input("Enter Pro Code:", type="password", key="pro_code_input")

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
    st.sidebar.success("**PRO USER** — Unlimited analyses")
    st.sidebar.markdown("---")
    st.sidebar.caption("Need to cancel or update your subscription?")
    st.sidebar.link_button("⚙️ Manage / Cancel Subscription",
        "https://billing.stripe.com/p/login/dRm4gz7DW7bmaFSche8k800",
        use_container_width=True)
    st.sidebar.caption("Questions? falconmanagementllc25@gmail.com")
else:
    remaining = max(0, 3 - st.session_state['usage_count'])
    if remaining > 0:
        st.sidebar.info(f"🆓 **Free Trial:** {remaining}/3 analyses remaining")
    else:
        st.sidebar.error("⚠ **Free limit reached!**")
        st.sidebar.markdown("**Upgrade to Pro — $49.99/mo**")
        st.sidebar.markdown("✅ Unlimited analyses")
        st.sidebar.markdown("✅ PDF reports with charts")
        st.sidebar.markdown("✅ Save & compare scenarios")
        st.sidebar.markdown("✅ Sensitivity tornado chart")
        st.sidebar.markdown("✅ Quote templates")
        st.sidebar.markdown("✅ Win/Loss tracker")
        st.sidebar.link_button("🚀 Subscribe Now →",
            "https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800",
            use_container_width=True)

st.sidebar.markdown("---")

# ── PRO FEATURE 4: Load Template in sidebar ─────────────────────────────────
template_defaults = {}
if is_pro and st.session_state['quote_templates']:
    st.sidebar.subheader("📋 Load Template")
    template_names = ["-- None --"] + list(st.session_state['quote_templates'].keys())
    selected_template = st.sidebar.selectbox("Select a template:", template_names, key="template_selector")
    if selected_template != "-- None --":
        template_defaults = st.session_state['quote_templates'][selected_template]
        st.sidebar.success(f"✅ Template '{selected_template}' loaded!")
    st.sidebar.markdown("---")

def tval(key, default):
    """Return template value if loaded, otherwise default."""
    return template_defaults.get(key, default)

# ── Sidebar inputs ──────────────────────────────────────────────────────────
st.sidebar.header("📊 Job Parameters")
job_name = st.sidebar.text_input("Job Name (optional)", placeholder="e.g., Bracket-2024-001")

st.sidebar.subheader("💰 Material Costs")
material_cost        = st.sidebar.number_input("Base Material Cost ($)",       min_value=100,  max_value=50000, value=tval('material_cost', 3500),        step=100)
material_uncertainty = st.sidebar.slider(      "Material Cost Uncertainty (%)", min_value=5,    max_value=40,    value=tval('material_uncertainty', 12))
waste_pct            = st.sidebar.slider(      "Expected Material Waste (%)",   min_value=5,    max_value=30,    value=tval('waste_pct', 10))

st.sidebar.subheader("⏱ Labor Estimates")
setup_hours     = st.sidebar.number_input("Setup Time (hours)",     min_value=0.5, max_value=40.0,  value=tval('setup_hours', 4.0),      step=0.5)
machining_hours = st.sidebar.number_input("Machining Time (hours)", min_value=1.0, max_value=500.0, value=tval('machining_hours', 35.0), step=1.0)
finishing_hours = st.sidebar.number_input("Finishing Time (hours)", min_value=0.5, max_value=40.0,  value=tval('finishing_hours', 5.0),  step=0.5)
labor_uncertainty = st.sidebar.slider(   "Labor Time Uncertainty (%)", min_value=10, max_value=50,  value=tval('labor_uncertainty', 20))
labor_rate       = st.sidebar.number_input("Labor Rate ($/hr)",    min_value=30,  max_value=200,   value=tval('labor_rate', 75),         step=5)

st.sidebar.subheader("🔩 Other Costs")
tooling_cost       = st.sidebar.number_input("Tooling/Consumables ($)", min_value=50,  max_value=5000,  value=tval('tooling_cost', 400),       step=50)
subcontractor_cost = st.sidebar.number_input("Subcontractor Cost ($)",  min_value=0,   max_value=10000, value=tval('subcontractor_cost', 800), step=100)
rework_probability = st.sidebar.slider(     "Rework Probability (%)",   min_value=0,   max_value=50,    value=tval('rework_probability', 15))

st.sidebar.subheader("📈 Business Factors")
overhead_multiplier = st.sidebar.number_input("Overhead Multiplier",      min_value=1.0, max_value=3.0, value=tval('overhead_multiplier', 1.35), step=0.05)
profit_margin       = st.sidebar.number_input("Profit Margin Multiplier", min_value=1.0, max_value=2.0, value=tval('profit_margin', 1.15),       step=0.05)

n_simulations = 10_000

# ── Helpers ─────────────────────────────────────────────────────────────────

def run_simulation(mat_cost, mat_unc, waste_p, s_hrs, m_hrs, f_hrs, l_unc,
                   l_rate, tool, sub, rework_prob, ovhd, profit, n=10_000):
    mat_std   = mat_cost * (mat_unc / 100)
    raw_mat   = np.random.normal(mat_cost, mat_std, n)
    waste     = np.random.triangular(waste_p*0.5, waste_p, waste_p*2, n) / 100
    mat_total = raw_mat * (1 + waste)
    s_sim = np.random.normal(s_hrs, s_hrs*(l_unc/100), n)
    m_sim = np.random.normal(m_hrs, m_hrs*(l_unc/100), n)
    f_sim = np.random.normal(f_hrs, f_hrs*(l_unc/100), n)
    total_hrs = s_sim + m_sim + f_sim
    overtime  = np.random.random(n) < 0.10
    eff_rate  = np.where(overtime, l_rate*1.5, l_rate)
    labor     = total_hrs * eff_rate
    needs_rework = np.random.random(n) < (rework_prob/100)
    rework_hrs   = np.where(needs_rework, np.random.uniform(5, 15, n), 0)
    rework       = rework_hrs * l_rate
    direct = mat_total + labor + tool + sub + rework
    quote  = direct * ovhd * profit
    return quote, mat_total, labor, rework, direct


def build_results(quote, mat_total, labor, rework, direct):
    return {
        'mean':         quote.mean(),
        'median':       np.percentile(quote, 50),
        'p10':          np.percentile(quote, 10),
        'p25':          np.percentile(quote, 25),
        'p75':          np.percentile(quote, 75),
        'p90':          np.percentile(quote, 90),
        'min':          quote.min(),
        'max':          quote.max(),
        'avg_material': mat_total.mean(),
        'avg_labor':    labor.mean(),
        'avg_rework':   rework.mean(),
        'avg_direct':   direct.mean(),
    }


def risk_score(results):
    """
    PRO FEATURE 6 — Risk Score Badge
    Measures spread between p50 and p90 as % of median.
    Tight spread = low risk (A). Wide spread = high risk (D).
    """
    spread_pct = (results['p90'] - results['median']) / results['median'] * 100
    if spread_pct < 15:
        return 'A', '🟢', 'Low Risk', '#1e8449', 'Cost outcomes are tightly clustered. This is a predictable, well-defined job.'
    elif spread_pct < 25:
        return 'B', '🟡', 'Moderate Risk', '#d4ac0d', 'Some variability in outcomes. Use the conservative quote for new customers.'
    elif spread_pct < 40:
        return 'C', '🟠', 'High Risk', '#ca6f1e', 'Significant spread between best and worst case. Consider padding your quote.'
    else:
        return 'D', '🔴', 'Very High Risk', '#922b21', 'Wide cost range — this job has major uncertainty. Quote conservatively or walk away.'


def generate_text_report(jname, results, params):
    grade, _, label, _, _ = risk_score(results)
    return f"""
MANUFACTURING QUOTE RISK ANALYSIS REPORT
{'='*60}

Job Name: {jname if jname else 'Untitled Job'}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Risk Grade: {grade} — {label}

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

Risk Grade: {grade} — {label}

🎯 COMPETITIVE QUOTE (50%): ${results['median']:,.0f}
✅ CONSERVATIVE QUOTE (75%): ${results['p75']:,.0f}
   Risk Premium: ${results['p75'] - results['median']:,.0f}

{'='*60}
DETAILED STATISTICS
{'='*60}

10th Percentile: ${results['p10']:>12,.0f}
25th Percentile: ${results['p25']:>12,.0f}
50th Percentile: ${results['median']:>12,.0f}
75th Percentile: ${results['p75']:>12,.0f}
90th Percentile: ${results['p90']:>12,.0f}

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

Generated by Manufacturing Quote Risk Analyzer
Monte Carlo Simulation with 10,000 iterations
"""


# ══════════════════════════════════════════════════════════════════════════════
#  PAYWALL SCREEN
# ══════════════════════════════════════════════════════════════════════════════
can_run = is_pro or st.session_state['usage_count'] < 3

if not can_run:
    st.markdown("""
    <style>
    .pro-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin: 1.5rem 0 2rem; }
    .pro-card { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1.6rem; }
    .pro-card-accent-orange { border-top: 3px solid #FF6B35; }
    .pro-card-accent-green  { border-top: 3px solid #00C9A7; }
    .pro-card-accent-purple { border-top: 3px solid #8B7CF6; }
    .pro-card-accent-blue   { border-top: 3px solid #3B9EE8; }
    .pro-card-accent-gold   { border-top: 3px solid #F4C430; }
    .pro-tag { display: inline-block; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; padding: 2px 10px; border-radius: 20px; margin-bottom: 0.75rem; }
    .tag-orange { background: rgba(255,107,53,0.15); color: #FF6B35; }
    .tag-green  { background: rgba(0,201,167,0.15);  color: #00C9A7; }
    .tag-purple { background: rgba(139,124,246,0.15);color: #8B7CF6; }
    .tag-blue   { background: rgba(59,158,232,0.15); color: #3B9EE8; }
    .tag-gold   { background: rgba(244,196,48,0.15); color: #c9a400; }
    .pro-card h4 { font-size: 1.05rem; margin: 0 0 0.5rem; color: #f0f0f0; }
    .pro-card p  { font-size: 0.84rem; color: #aaa; line-height: 1.6; margin: 0 0 0.8rem; }
    .pro-card ul { padding-left: 1rem; margin: 0; }
    .pro-card ul li { font-size: 0.81rem; color: #ccc; margin-bottom: 4px; }
    .price-row { display: grid; gap: 1rem; margin: 1.5rem 0; }
    .price-card { border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1.4rem; text-align: center; background: rgba(255,255,255,0.02); }
    .price-card.hot { border: 1.5px solid #FF6B35; background: rgba(255,107,53,0.06); }
    .price-card .plan-name  { font-size: 0.7rem; letter-spacing: 0.12em; color: #888; margin-bottom: 4px; }
    .price-card .plan-price { font-size: 2rem; font-weight: 800; margin: 0; }
    .price-card .plan-desc  { font-size: 0.75rem; color: #888; margin-bottom: 0.8rem; }
    .price-card ul { list-style: none; padding: 0; margin: 0; text-align: left; }
    .price-card ul li { font-size: 0.8rem; color: #bbb; padding: 3px 0; }
    .price-card ul li::before { content: "✓ "; color: #00C9A7; }
    .hot-badge { display: inline-block; background: #FF6B35; color: #fff; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; padding: 2px 12px; border-radius: 20px; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔧 Manufacturing Quote Risk Analyzer")
    st.markdown("---")
    col_lock, col_txt = st.columns([1, 5])
    with col_lock:
        st.markdown("## 🔒")
    with col_txt:
        st.markdown("## You've used all 3 free analyses")
        st.markdown("Upgrade to **Pro** to keep analyzing — plus unlock five powerful features below.")
    st.markdown("---")

    st.markdown("### 🚀 What You Get with Pro")
    st.markdown("""
    <div class="pro-grid">
      <div class="pro-card pro-card-accent-orange">
        <span class="pro-tag tag-orange">✦ PRO FEATURE 1</span>
        <h4>📄 PDF Reports with Charts</h4>
        <p>Branded, print-ready PDF after every analysis with cost distribution histogram, percentile table, and quoting recommendations.</p>
        <ul><li>Cost distribution chart included</li><li>Branded header with job name & date</li><li>One-click download, every time</li></ul>
      </div>
      <div class="pro-card pro-card-accent-green">
        <span class="pro-tag tag-green">✦ PRO FEATURE 2</span>
        <h4>💾 Save & Compare Scenarios</h4>
        <p>Save multiple job scenarios and compare them side-by-side. See which quote is highest-risk and how they stack up on every percentile.</p>
        <ul><li>Save unlimited named scenarios</li><li>Side-by-side comparison table</li><li>Export all scenarios to CSV</li></ul>
      </div>
      <div class="pro-card pro-card-accent-purple">
        <span class="pro-tag tag-purple">✦ PRO FEATURE 3</span>
        <h4>📊 Sensitivity Analysis</h4>
        <p>A tornado chart ranks every variable — material, labor, rework, overtime — by its impact on your final quote range.</p>
        <ul><li>Tornado chart (ranked by impact)</li><li>% contribution per cost driver</li><li>Actionable insight into your biggest risks</li></ul>
      </div>
      <div class="pro-card pro-card-accent-blue">
        <span class="pro-tag tag-blue">✦ PRO FEATURE 4</span>
        <h4>📋 Quote Templates</h4>
        <p>Save any job's parameters as a reusable template. Load it in one click instead of re-entering everything from scratch.</p>
        <ul><li>Save unlimited named templates</li><li>Load from sidebar instantly</li><li>Perfect for repeat job types</li></ul>
      </div>
      <div class="pro-card pro-card-accent-gold">
        <span class="pro-tag tag-gold">✦ PRO FEATURE 5</span>
        <h4>🏆 Win/Loss Tracker + Risk Score</h4>
        <p>Mark each quote as Won or Lost. Every job gets an A–D risk grade. See your win rate and which risk levels you win most often.</p>
        <ul><li>A–D risk grade on every analysis</li><li>Win/Loss log with quote prices</li><li>Win rate by risk grade</li></ul>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💳 Choose Your Plan")
    st.markdown("""
    <div class="price-row" style="grid-template-columns: 1fr 1fr; max-width: 700px; margin: 1.5rem auto;">
      <div class="price-card">
        <div class="plan-name">STARTER FREE</div>
        <div class="plan-price">$0</div>
        <div class="plan-desc">Try it out</div>
        <ul>
          <li>3 analyses / month</li>
          <li>Text report download</li>
          <li>All input parameters</li>
        </ul>
      </div>
      <div class="price-card hot">
        <div class="hot-badge">UPGRADE</div>
        <div class="plan-name">PRO</div>
        <div class="plan-price">$49.99<span style="font-size:1rem;font-weight:400">/mo</span></div>
        <div class="plan-desc">For active shops</div>
        <ul>
          <li>Unlimited analyses</li>
          <li>PDF reports with charts</li>
          <li>Save & compare scenarios</li>
          <li>Sensitivity / tornado chart</li>
          <li>Quote templates</li>
          <li>Win/Loss tracker + Risk score</li>
          <li>Priority email support</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        st.link_button("🚀 Subscribe to Pro — $49.99/mo",
                       "https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800",
                       type="primary", use_container_width=True)
    with col_info:
        st.markdown("After subscribing, email **falconmanagementllc25@gmail.com** for your access code, then enter it in the sidebar to unlock Pro instantly.")

    st.markdown("---")
    st.markdown("<center><small>Manufacturing Quote Risk Analyzer v2.2 &nbsp;|&nbsp; Built with Monte Carlo simulation &nbsp;|&nbsp; Questions? falconmanagementllc25@gmail.com</small></center>", unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
st.title("🔧 Manufacturing Quote Risk Analyzer")
st.markdown("*Get data-driven confidence intervals for your manufacturing quotes*")
st.markdown("---")

if is_pro:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Saved Scenarios")
    if st.session_state['saved_scenarios']:
        st.sidebar.caption(f"{len(st.session_state['saved_scenarios'])} scenario(s) saved")
    else:
        st.sidebar.caption("No scenarios saved yet.")

run_clicked = st.sidebar.button("🚀 Run Risk Analysis", type="primary")

if run_clicked:
    if not is_pro:
        st.session_state['usage_count'] += 1

    with st.spinner("Running Monte Carlo simulation…"):
        quote, mat_total, labor, rework, direct = run_simulation(
            material_cost, material_uncertainty, waste_pct,
            setup_hours, machining_hours, finishing_hours,
            labor_uncertainty, labor_rate,
            tooling_cost, subcontractor_cost, rework_probability,
            overhead_multiplier, profit_margin
        )
        results = build_results(quote, mat_total, labor, rework, direct)
        params  = dict(
            material_cost=material_cost, material_uncertainty=material_uncertainty,
            waste_pct=waste_pct, setup_hours=setup_hours, machining_hours=machining_hours,
            finishing_hours=finishing_hours, labor_rate=labor_rate,
            labor_uncertainty=labor_uncertainty, tooling_cost=tooling_cost,
            subcontractor_cost=subcontractor_cost, rework_probability=rework_probability,
            overhead_multiplier=overhead_multiplier, profit_margin=profit_margin,
        )
        st.session_state['results']     = results
        st.session_state['params']      = params
        st.session_state['total_quote'] = quote
        st.session_state['job_name']    = job_name

    st.success("✅ Analysis Complete!")

# ── Display results ──────────────────────────────────────────────────────────
if 'results' in st.session_state:
    results = st.session_state['results']
    params  = st.session_state['params']
    quote   = st.session_state['total_quote']
    j_name  = st.session_state.get('job_name', '')

    # ── PRO FEATURE 6: Risk Score Badge ────────────────────────────────────
    if is_pro:
        grade, emoji, label, color, advice = risk_score(results)
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:16px; background:{color}18;
                    border:2px solid {color}; border-radius:12px; padding:14px 20px; margin-bottom:16px;">
          <div style="font-size:2.8rem; line-height:1;">{emoji}</div>
          <div>
            <div style="font-size:0.7rem; font-weight:700; letter-spacing:0.12em; color:{color}; margin-bottom:2px;">RISK GRADE</div>
            <div style="font-size:1.6rem; font-weight:800; color:{color}; line-height:1.1;">
              Grade {grade} &nbsp;<span style="font-size:1rem; font-weight:600;">{label}</span>
            </div>
            <div style="font-size:0.83rem; color:#555; margin-top:4px;">{advice}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Key metrics
    st.subheader("📊 Key Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected Cost",         f"${results['mean']:,.0f}")
    c2.metric("Median (50%)",          f"${results['median']:,.0f}")
    c3.metric("Conservative (75%)",    f"${results['p75']:,.0f}", delta=f"+${results['p75']-results['median']:,.0f}")
    c4.metric("High Confidence (90%)", f"${results['p90']:,.0f}", delta=f"+${results['p90']-results['median']:,.0f}")

    # Distribution chart
    st.subheader("📈 Cost Distribution")
    hist_values, bin_edges = np.histogram(quote, bins=50)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    hist_df = pd.DataFrame({'Cost Range': [f"${int(x):,}" for x in bin_centers], 'Frequency': hist_values})
    st.bar_chart(hist_df.set_index('Cost Range')['Frequency'], height=400)

    ca, cb, cc = st.columns(3)
    ca.metric("Minimum", f"${results['min']:,.0f}")
    cb.metric("Average",  f"${results['mean']:,.0f}")
    cc.metric("Maximum", f"${results['max']:,.0f}")

    # Recommendations
    st.subheader("💡 Quoting Recommendations")
    r1, r2 = st.columns(2)
    r1.info(f"🎯 **COMPETITIVE QUOTE**\n\n### ${results['median']:,.0f}\n\n- 50% confidence level\n- Use for: Competitive bidding\n- Risk: 50/50 chance of overrun")
    r2.success(f"✅ **CONSERVATIVE QUOTE**\n\n### ${results['p75']:,.0f}\n\n- 75% confidence level\n- Use for: New customers, complex jobs\n- Risk premium: ${results['p75']-results['median']:,.0f}")

    # Stats table
    st.subheader("📋 Detailed Statistics")
    stats_df = pd.DataFrame({
        'Percentile': ['10th','25th','50th (Median)','75th','90th'],
        'Quote Price': [f"${results[k]:,.0f}" for k in ['p10','p25','median','p75','p90']]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    # Cost breakdown
    st.subheader("💵 Average Cost Breakdown")
    bd_df = pd.DataFrame({
        'Component': ['Material (w/ waste)','Labor','Tooling','Subcontractor','Rework','Total Direct'],
        'Cost': [
            f"${results['avg_material']:,.0f}", f"${results['avg_labor']:,.0f}",
            f"${params['tooling_cost']:,.0f}",  f"${params['subcontractor_cost']:,.0f}",
            f"${results['avg_rework']:,.0f}",   f"${results['avg_direct']:,.0f}",
        ]
    })
    st.dataframe(bd_df, use_container_width=True, hide_index=True)

    # ── Export ──────────────────────────────────────────────────────────────
    st.subheader("📄 Export Report")
    if is_pro:
        tab1, tab2 = st.tabs(["📄 Text Report", "🖨️ Print / PDF Report"])
        with tab1:
            text_report = generate_text_report(j_name, results, params)
            st.download_button("⬇ Download Text Report", data=text_report,
                file_name=f"risk_analysis_{(j_name or 'report').replace(' ','')}{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain", type="primary")
        with tab2:
            grade, _, label, _, _ = risk_score(results)
            st.markdown("**Pro PDF Report** — download and open in browser, then Print → Save as PDF.")
            html_report = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Risk Report — {j_name or 'Untitled'}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 820px; margin: 40px auto; color: #222; }}
  h1 {{ color: #2c3e50; border-bottom: 2px solid #FF6B35; padding-bottom: 8px; }}
  h2 {{ color: #34495e; margin-top: 28px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th {{ background: #2c3e50; color: #fff; padding: 8px 12px; text-align: left; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) td {{ background: #f9f9f9; }}
  .badge {{ display:inline-block; padding:4px 14px; border-radius:20px; font-weight:bold; }}
  .comp {{ background:#ebf5fb; color:#1a6fa8; }}
  .cons {{ background:#eafaf1; color:#1e8449; }}
  .grade {{ display:inline-block; padding:6px 18px; border-radius:8px; font-size:1.1rem; font-weight:800; background:#fff3e0; color:#e65100; border:1.5px solid #e65100; }}
  .footer {{ margin-top:40px; font-size:0.8rem; color:#999; border-top:1px solid #eee; padding-top:12px; }}
</style></head><body>
<h1>🔧 Manufacturing Quote Risk Analysis</h1>
<p><strong>Job:</strong> {j_name or 'Untitled'} &nbsp;&nbsp; <strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p>Risk Grade: <span class="grade">Grade {grade} — {label}</span></p>
<h2>Key Results</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Expected (Mean) Cost</td><td>${results['mean']:,.0f}</td></tr>
  <tr><td>Median (50th pct)</td><td>${results['median']:,.0f}</td></tr>
  <tr><td>Conservative (75th pct)</td><td>${results['p75']:,.0f}</td></tr>
  <tr><td>High Confidence (90th pct)</td><td>${results['p90']:,.0f}</td></tr>
</table>
<h2>Quoting Recommendations</h2>
<p><span class="badge comp">🎯 Competitive: ${results['median']:,.0f}</span> &nbsp;
   <span class="badge cons">✅ Conservative: ${results['p75']:,.0f}</span></p>
<h2>Full Percentile Table</h2>
<table>
  <tr><th>Percentile</th><th>Quote Price</th></tr>
  <tr><td>10th</td><td>${results['p10']:,.0f}</td></tr>
  <tr><td>25th</td><td>${results['p25']:,.0f}</td></tr>
  <tr><td>50th (Median)</td><td>${results['median']:,.0f}</td></tr>
  <tr><td>75th</td><td>${results['p75']:,.0f}</td></tr>
  <tr><td>90th</td><td>${results['p90']:,.0f}</td></tr>
</table>
<h2>Average Cost Breakdown</h2>
<table>
  <tr><th>Component</th><th>Cost</th></tr>
  <tr><td>Material (with waste)</td><td>${results['avg_material']:,.0f}</td></tr>
  <tr><td>Labor</td><td>${results['avg_labor']:,.0f}</td></tr>
  <tr><td>Tooling / Consumables</td><td>${params['tooling_cost']:,.0f}</td></tr>
  <tr><td>Subcontractor</td><td>${params['subcontractor_cost']:,.0f}</td></tr>
  <tr><td>Rework</td><td>${results['avg_rework']:,.0f}</td></tr>
  <tr><td><strong>Direct Costs</strong></td><td><strong>${results['avg_direct']:,.0f}</strong></td></tr>
  <tr><td><strong>After Overhead & Profit</strong></td><td><strong>${results['mean']:,.0f}</strong></td></tr>
</table>
<div class="footer">Generated by Manufacturing Quote Risk Analyzer v2.2 &nbsp;|&nbsp; Monte Carlo (10,000 iterations) &nbsp;|&nbsp; falconmanagementllc25@gmail.com</div>
</body></html>"""
            st.download_button("⬇ Download Print-Ready HTML Report", data=html_report,
                file_name=f"risk_report_{(j_name or 'report').replace(' ','')}{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html", type="primary")
            st.caption("Open in any browser → Ctrl+P (Cmd+P on Mac) → Save as PDF.")
    else:
        text_report = generate_text_report(j_name, results, params)
        st.download_button("⬇ Download Text Report", data=text_report,
            file_name=f"risk_analysis_{(j_name or 'report').replace(' ','')}{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain", type="primary")
        st.info("🔒 **Pro Feature:** PDF reports with charts available with Pro subscription.")

    # ── PRO FEATURE 2: Save & Compare Scenarios ─────────────────────────────
    if is_pro:
        st.markdown("---")
        st.subheader("💾 Save & Compare Scenarios")
        save_col, _ = st.columns([1, 2])
        with save_col:
            scenario_label = st.text_input("Scenario name (to save)",
                value=j_name or f"Scenario {len(st.session_state['saved_scenarios'])+1}")
            if st.button("💾 Save This Scenario"):
                grade, _, label, _, _ = risk_score(results)
                st.session_state['saved_scenarios'][scenario_label] = {
                    'median': results['median'], 'p75': results['p75'],
                    'p90': results['p90'], 'mean': results['mean'],
                    'avg_material': results['avg_material'], 'avg_labor': results['avg_labor'],
                    'avg_rework': results['avg_rework'],
                    'risk_grade': f"{grade} — {label}",
                    'saved_at': datetime.now().strftime('%H:%M')
                }
                st.success(f"✅ Saved as '{scenario_label}'")

        if st.session_state['saved_scenarios']:
            comp_rows = []
            for name, s in st.session_state['saved_scenarios'].items():
                comp_rows.append({
                    'Scenario': name,
                    'Risk Grade': s.get('risk_grade', '—'),
                    'Competitive (50%)': f"${s['median']:,.0f}",
                    'Conservative (75%)': f"${s['p75']:,.0f}",
                    'High Conf. (90%)': f"${s['p90']:,.0f}",
                    'Expected': f"${s['mean']:,.0f}",
                    'Saved': s['saved_at'],
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
            csv_rows = [{'Scenario': n, **{k: v for k, v in s.items() if k != 'saved_at'}}
                        for n, s in st.session_state['saved_scenarios'].items()]
            st.download_button("⬇ Export All Scenarios (CSV)",
                pd.DataFrame(csv_rows).to_csv(index=False), "scenarios.csv", "text/csv")
            if st.button("🗑 Clear All Saved Scenarios"):
                st.session_state['saved_scenarios'] = {}
                st.rerun()
    else:
        st.info("🔒 **Pro Feature:** Save & compare multiple job scenarios — available with Pro subscription.")

    # ── PRO FEATURE 3: Sensitivity Analysis ─────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Sensitivity Analysis")
    if is_pro:
        st.markdown("Which input drives your cost risk the most? Each variable is shocked ±20% while others stay fixed.")
        shock = 0.20
        def _mean(mc,mu,wp,sh,mh,fh,lu,lr,tc,sc,rp,om,pm):
            q,*_ = run_simulation(mc,mu,wp,sh,mh,fh,lu,lr,tc,sc,rp,om,pm,n=3000)
            return q.mean()
        cases = {
            "Material Cost":       lambda d: _mean(material_cost*(1+d),material_uncertainty,waste_pct,setup_hours,machining_hours,finishing_hours,labor_uncertainty,labor_rate,tooling_cost,subcontractor_cost,rework_probability,overhead_multiplier,profit_margin),
            "Labor Rate":          lambda d: _mean(material_cost,material_uncertainty,waste_pct,setup_hours,machining_hours,finishing_hours,labor_uncertainty,labor_rate*(1+d),tooling_cost,subcontractor_cost,rework_probability,overhead_multiplier,profit_margin),
            "Machining Hours":     lambda d: _mean(material_cost,material_uncertainty,waste_pct,setup_hours,machining_hours*(1+d),finishing_hours,labor_uncertainty,labor_rate,tooling_cost,subcontractor_cost,rework_probability,overhead_multiplier,profit_margin),
            "Rework Probability":  lambda d: _mean(material_cost,material_uncertainty,waste_pct,setup_hours,machining_hours,finishing_hours,labor_uncertainty,labor_rate,tooling_cost,subcontractor_cost,min(100,rework_probability*(1+d)),overhead_multiplier,profit_margin),
            "Overhead Multiplier": lambda d: _mean(material_cost,material_uncertainty,waste_pct,setup_hours,machining_hours,finishing_hours,labor_uncertainty,labor_rate,tooling_cost,subcontractor_cost,rework_probability,overhead_multiplier*(1+d),profit_margin),
            "Material Uncertainty":lambda d: _mean(material_cost,min(40,material_uncertainty*(1+d)),waste_pct,setup_hours,machining_hours,finishing_hours,labor_uncertainty,labor_rate,tooling_cost,subcontractor_cost,rework_probability,overhead_multiplier,profit_margin),
        }
        sensitivities = {label: abs(fn(shock) - fn(-shock)) for label, fn in cases.items()}
        sens_df = pd.DataFrame.from_dict(sensitivities, orient='index', columns=['Impact ($)']).sort_values('Impact ($)', ascending=True)
        st.bar_chart(sens_df, height=320)
        st.caption("Bar length = total swing in expected quote when input is raised/lowered 20%. Longer = bigger risk driver.")
        sens_pct = sens_df.copy()
        sens_pct['% of Total Swing'] = (sens_pct['Impact ($)'] / sens_pct['Impact ($)'].sum() * 100).round(1)
        sens_pct['Impact ($)'] = sens_pct['Impact ($)'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(sens_pct.sort_values('% of Total Swing', ascending=False), use_container_width=True)
    else:
        st.info("🔒 **Pro Feature:** Sensitivity / tornado chart — available with Pro subscription.")
        st.markdown("[**Upgrade to Pro →**](https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800)")

    # ── PRO FEATURE 4: Quote Templates ──────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Quote Templates")
    if is_pro:
        st.markdown("Save the current job parameters as a reusable template — load it from the sidebar next time.")
        t_col1, t_col2 = st.columns([1, 2])
        with t_col1:
            template_name = st.text_input("Template name", placeholder="e.g., Steel Bracket Job")
            if st.button("💾 Save as Template"):
                if template_name.strip():
                    st.session_state['quote_templates'][template_name.strip()] = {
                        'material_cost': material_cost, 'material_uncertainty': material_uncertainty,
                        'waste_pct': waste_pct, 'setup_hours': setup_hours,
                        'machining_hours': machining_hours, 'finishing_hours': finishing_hours,
                        'labor_uncertainty': labor_uncertainty, 'labor_rate': labor_rate,
                        'tooling_cost': tooling_cost, 'subcontractor_cost': subcontractor_cost,
                        'rework_probability': rework_probability,
                        'overhead_multiplier': overhead_multiplier, 'profit_margin': profit_margin,
                    }
                    st.success(f"✅ Template '{template_name.strip()}' saved! Load it from the sidebar.")
                else:
                    st.warning("Please enter a template name first.")

        if st.session_state['quote_templates']:
            st.markdown(f"**{len(st.session_state['quote_templates'])} saved template(s):** " +
                        " · ".join([f"`{k}`" for k in st.session_state['quote_templates'].keys()]))
            del_name = st.selectbox("Delete a template:", ["-- Select --"] + list(st.session_state['quote_templates'].keys()), key="del_template")
            if del_name != "-- Select --" and st.button("🗑 Delete Selected Template"):
                del st.session_state['quote_templates'][del_name]
                st.success(f"Deleted '{del_name}'")
                st.rerun()
    else:
        st.info("🔒 **Pro Feature:** Quote templates — save and reuse job parameters. Available with Pro subscription.")

    # ── PRO FEATURE 5: Win/Loss Tracker ─────────────────────────────────────
    st.markdown("---")
    st.subheader("🏆 Win/Loss Tracker")
    if is_pro:
        st.markdown("Did you send this quote? Mark the outcome to track your win rate over time.")
        grade, emoji, label, color, _ = risk_score(results)

        wl_col1, wl_col2, wl_col3 = st.columns(3)
        with wl_col1:
            quote_sent = st.number_input("Quote price sent to customer ($)",
                min_value=0, value=int(results['p75']), step=100)
        with wl_col2:
            customer = st.text_input("Customer name (optional)", placeholder="e.g., Acme Corp")
        with wl_col3:
            st.markdown("<br>", unsafe_allow_html=True)
            w_col, l_col = st.columns(2)
            with w_col:
                if st.button("✅ Won", use_container_width=True):
                    st.session_state['win_loss_log'].append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'job': j_name or 'Untitled',
                        'customer': customer or '—',
                        'quote_sent': quote_sent,
                        'median': results['median'],
                        'p75': results['p75'],
                        'risk_grade': f"{grade} — {label}",
                        'outcome': 'Won',
                    })
                    st.success("🎉 Marked as Won!")
            with l_col:
                if st.button("❌ Lost", use_container_width=True):
                    st.session_state['win_loss_log'].append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'job': j_name or 'Untitled',
                        'customer': customer or '—',
                        'quote_sent': quote_sent,
                        'median': results['median'],
                        'p75': results['p75'],
                        'risk_grade': f"{grade} — {label}",
                        'outcome': 'Lost',
                    })
                    st.warning("📝 Marked as Lost.")

        if st.session_state['win_loss_log']:
            st.markdown("---")
            log_df = pd.DataFrame(st.session_state['win_loss_log'])

            # Summary stats
            total   = len(log_df)
            wins    = (log_df['outcome'] == 'Won').sum()
            win_rate = wins / total * 100

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Quotes Logged", total)
            m2.metric("Won", wins)
            m3.metric("Win Rate", f"{win_rate:.0f}%")

            # Win rate by risk grade
            if len(log_df['risk_grade'].unique()) > 1:
                st.markdown("**Win Rate by Risk Grade**")
                grade_summary = log_df.groupby('risk_grade').apply(
                    lambda x: pd.Series({
                        'Total': len(x),
                        'Won': (x['outcome'] == 'Won').sum(),
                        'Win Rate': f"{(x['outcome']=='Won').sum()/len(x)*100:.0f}%"
                    })
                ).reset_index()
                st.dataframe(grade_summary, use_container_width=True, hide_index=True)

            # Full log
            st.markdown("**Full Quote Log**")
            display_df = log_df.copy()
            display_df['quote_sent'] = display_df['quote_sent'].apply(lambda x: f"${x:,.0f}")
            display_df['median']     = display_df['median'].apply(lambda x: f"${x:,.0f}")
            display_df['p75']        = display_df['p75'].apply(lambda x: f"${x:,.0f}")
            display_df.columns = ['Date','Job','Customer','Quote Sent','50th pct','75th pct','Risk Grade','Outcome']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_log = pd.DataFrame(st.session_state['win_loss_log']).to_csv(index=False)
            st.download_button("⬇ Export Win/Loss Log (CSV)", csv_log, "win_loss_log.csv", "text/csv")

            if st.button("🗑 Clear Win/Loss Log"):
                st.session_state['win_loss_log'] = []
                st.rerun()
    else:
        st.info("🔒 **Pro Feature:** Win/Loss tracker — log outcomes and see your win rate. Available with Pro subscription.")

else:
    st.info("👈 *Adjust parameters in the sidebar and click 'Run Risk Analysis'*")
    st.markdown("""
### How to Use:
1. Enter your job parameters in the sidebar
2. Optionally add a job name for the report
3. Click **Run Risk Analysis**
4. Download your detailed report

### Features:
- ✅ Monte Carlo simulation (10,000 iterations)
- ✅ Multiple confidence levels (50%, 75%, 90%)
- ✅ Detailed cost breakdown
- ✅ Downloadable reports
- ✅ Conservative & competitive quotes
""")

# ── Pro teaser banner ────────────────────────────────────────────────────────
if not is_pro:
    st.markdown("---")
    st.markdown("""
<div style="background: linear-gradient(90deg, #fff8f5 0%, #f0f4ff 100%);
            border: 1.5px solid #FF6B35; border-radius: 12px; padding: 20px 24px; margin-top: 8px;">
  <h4 style="margin: 0 0 6px; color: #c0410a;">⭐ Unlock More with Pro — $49.99/month</h4>
  <p style="margin: 0 0 12px; color: #555; font-size: 0.9rem;">
    You are on the free tier (3 analyses). Subscribe to Pro and get five powerful upgrades:
  </p>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-bottom: 14px;">
    <div style="background:white;border-radius:8px;padding:10px;border:1px solid #ffe0d0;">
      <strong style="color:#c0410a;">📄 PDF Reports</strong><br>
      <span style="font-size:0.8rem;color:#666;">Branded PDFs with charts</span>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;border:1px solid #d0eaff;">
      <strong style="color:#1a5fa8;">💾 Save & Compare</strong><br>
      <span style="font-size:0.8rem;color:#666;">Side-by-side scenario comparison</span>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;border:1px solid #e0d8ff;">
      <strong style="color:#5b3fc4;">📊 Sensitivity Chart</strong><br>
      <span style="font-size:0.8rem;color:#666;">Find your biggest cost risks</span>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;border:1px solid #d0f0ff;">
      <strong style="color:#0e7490;">📋 Templates</strong><br>
      <span style="font-size:0.8rem;color:#666;">Save & reuse job parameters</span>
    </div>
    <div style="background:white;border-radius:8px;padding:10px;border:1px solid #fef3c7;">
      <strong style="color:#92400e;">🏆 Win/Loss Tracker</strong><br>
      <span style="font-size:0.8rem;color:#666;">A–D risk grade + win rate stats</span>
    </div>
  </div>
  <a href="https://buy.stripe.com/dRm4gz7DW7bmaFSche8k800" target="_blank"
     style="display:inline-block;background:#FF6B35;color:white;font-weight:700;
            padding:9px 22px;border-radius:8px;text-decoration:none;font-size:0.9rem;">
    🚀 Subscribe to Pro →
  </a>
  <span style="margin-left:14px;font-size:0.8rem;color:#999;">Cancel anytime · Your access code is emailed automatically after subscribing</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("Manufacturing Quote Risk Analyzer v2.2 | Built with Monte Carlo simulation")
