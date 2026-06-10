import streamlit as st
import pandas as pd
import os
from pathlib import Path

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoRetroAb",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1A237E 0%, #1565C0 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .step-box {
        background: #F8F9FF;
        border-left: 4px solid #1565C0;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #E8F5E9;
        border-left: 4px solid #2E7D32;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .info-box {
        background: #E3F2FD;
        border-left: 4px solid #1565C0;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── FIXED DEFAULT PARAMETERS ──────────────────────────────────────────────────
# To change these, edit this section directly in app.py
LOG2FC = 1.0
FDR = 0.05
MIN_COUNTS = 10
K_VALUE = 100
TOP_HITS = 10

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 AutoRetroAb")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Developer:** Abrar Alghamdi")
    st.markdown("**Institution:** University of Leicester")
    st.divider()
    st.markdown("### 📚 Resources")
    st.markdown("[📖 GitHub Repository](https://github.com/AbrarAlghamdi/AutoRetroAb)")
    st.markdown("[📄 Documentation](https://github.com/AbrarAlghamdi/AutoRetroAb#readme)")
    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
AutoRetroAb integrates nine analytical steps into a single reproducible workflow:
- Data acquisition from SRA/GEO
- Multi-mapping alignment (Bowtie2 -k 100)
- Locus-specific quantification (Telescope)
- Differential expression (DESeq2)
- Chromosomal enrichment analysis
- TE family enrichment analysis
- Volcano plots and reports
    """)
    st.divider()
    st.markdown("### ⚙️ Default Parameters")
    st.markdown(f"""
| Parameter | Value |
|-----------|-------|
| Log2FC threshold | {LOG2FC} |
| FDR threshold | {FDR} |
| Min count filter | {MIN_COUNTS} |
| Bowtie2 -k | {K_VALUE} |
| Top hits reported | {TOP_HITS} |
    """)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧬 AutoRetroAb</h1>
    <p style="font-size: 1.1rem; margin: 0;">
        Automated Locus-Specific Retrotransposon Transcriptomics Pipeline
    </p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.85;">
        HERV and LINE-1 differential expression analysis from bulk RNA-seq data
        · University of Leicester · Abrar Alghamdi
    </p>
</div>
""", unsafe_allow_html=True)

# ── MAIN TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🚀 Run Pipeline",
    "📋 Input Format",
    "📊 Example Results"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — RUN PIPELINE
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Run AutoRetroAb")
    st.markdown("""
    <div class="step-box">
    Follow the steps below. The pipeline will automatically download your RNA-seq data,
    align reads, quantify HERV and LINE-1 expression, and produce a complete differential
    expression analysis using validated default parameters.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # ── STEP 1 ──
    st.markdown("### Step 1 — Upload your sample CSV file")
    st.markdown("Your CSV must have three columns: **sample_id**, **condition**, **run_id**")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="CSV with columns: sample_id, condition, run_id"
        )
    with col2:
        st.markdown("**Example format:**")
        example_df = pd.DataFrame({
            "sample_id": ["ctrl_1", "ctrl_2", "treat_1", "treat_2"],
            "condition": ["control", "control", "treated", "treated"],
            "run_id": ["SRR123456", "SRR123457", "SRR123458", "SRR123459"]
        })
        st.dataframe(example_df, hide_index=True, use_container_width=True)

    df = None
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {"sample_id", "condition", "run_id"}
            if required_cols.issubset(df.columns):
                st.success(f"✅ Valid CSV — {len(df)} samples detected")
                st.dataframe(df, hide_index=True, use_container_width=True)
                conditions = df["condition"].unique()
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total samples", len(df))
                with col_b:
                    st.metric("Conditions", len(conditions))
                with col_c:
                    st.metric("SRR accessions", df["run_id"].nunique())
            else:
                missing = required_cols - set(df.columns)
                st.error(f"❌ Missing columns: {missing}")
                df = None
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            df = None

    st.divider()

    # ── STEP 2 ──
    st.markdown("### Step 2 — Configure your job")
    col_j1, col_j2, col_j3 = st.columns(3)
    with col_j1:
        job_name = st.text_input(
            "Job name", value="my_analysis",
            help="A name for your analysis — no spaces or special characters"
        )
    with col_j2:
        if df is not None and "condition" in df.columns:
            conditions_list = list(df["condition"].unique())
        else:
            conditions_list = ["control", "treated"]
        group1 = st.selectbox(
            "Control group", conditions_list,
            help="Select the control or reference condition"
        )
    with col_j3:
        remaining = [c for c in conditions_list if c != group1]
        group2 = st.selectbox(
            "Treatment group",
            remaining if remaining else conditions_list,
            help="Select the treatment or comparison condition"
        )

    st.divider()

    # ── STEP 3 ──
    st.markdown("### Step 3 — Analysis type")
    analysis_type = st.radio(
        "Which retrotransposons to analyse?",
        ["HERV and LINE-1 (recommended)", "HERV only", "LINE-1 only"],
        horizontal=True,
        help="HERV and LINE-1 analyses run separately using their respective annotation files"
    )

    analysis_flag_map = {
        "HERV and LINE-1 (recommended)": "--analysis both",
        "HERV only": "--analysis herv",
        "LINE-1 only": "--analysis l1"
    }
    analysis_flag = analysis_flag_map[analysis_type]

    if analysis_type == "HERV and LINE-1 (recommended)":
        st.success("✅ Both HERV (14,968 loci, 60 families) and LINE-1 loci will be analysed")
    elif analysis_type == "HERV only":
        st.info("🔬 HERV analysis only — 14,968 loci across 60 families (HERV_rmsk.hg38.v2.2.gtf)")
    else:
        st.info("🔬 LINE-1 analysis only — full L1 annotation and L1HS subset")

    st.divider()

    # ── STEP 4 ──
    st.markdown("### Step 4 — Run the pipeline")

    if df is not None and job_name:

        # Build create-job command
        cmd_parts = [
            f"autoretroab create-job-from-csv {job_name} \\",
            f"  --group1 {group1} \\",
            f"  --group2 {group2} \\",
            f"  --csv samples.csv \\",
            f"  {analysis_flag}"
        ]

        run_cmd = f"autoretroab run \\\n  --config jobs/{job_name}/config.yaml \\\n  --cores 4"

        st.markdown("**Step 4a — Create your job:**")
        st.code("\n".join(cmd_parts), language="bash")

        st.markdown("**Step 4b — Run the pipeline:**")
        st.code(run_cmd, language="bash")

        # Download buttons
        config_content = f"""# AutoRetroAb Job Configuration
# Generated by AutoRetroAb Web Interface
# https://autoretroab.streamlit.app

job_name: {job_name}
group1: {group1}
group2: {group2}
analysis_type: {analysis_type}
samples_csv: samples.csv
"""
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Download job config",
                data=config_content,
                file_name=f"{job_name}_config.yaml",
                mime="text/yaml"
            )
        with col_dl2:
            if uploaded_file:
                uploaded_file.seek(0)
                st.download_button(
                    label="📥 Download your CSV",
                    data=uploaded_file.getvalue(),
                    file_name=f"{job_name}_samples.csv",
                    mime="text/csv"
                )

        # Expected outputs
        st.divider()
        st.markdown("### Expected outputs")
        st.markdown(f"Results will be saved to: `results/{job_name}/`")

        output_items = []
        if "HERV" in analysis_type or "recommended" in analysis_type:
            output_items += [
                "results/{}/de/herv_deseq2_results.csv".format(job_name),
                "results/{}/enrichment/herv_family_enrichment.csv".format(job_name),
                "results/{}/chromosomal/herv_chromosomal_distribution.csv".format(job_name),
                "results/{}/plots/herv_volcano.png".format(job_name),
            ]
        if "LINE-1" in analysis_type or "recommended" in analysis_type:
            output_items += [
                "results/{}/de/l1_deseq2_results.csv".format(job_name),
                "results/{}/enrichment/l1_family_enrichment.csv".format(job_name),
                "results/{}/chromosomal/l1_chromosomal_distribution.csv".format(job_name),
                "results/{}/plots/l1_volcano.png".format(job_name),
            ]
        output_items.append("results/{}/reports/summary_report.txt".format(job_name))

        for item in output_items:
            st.markdown(f"- `{item}`")

    else:
        st.info("👆 Upload a CSV file and enter a job name to generate your run commands")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — INPUT FORMAT
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📋 Input File Format")

    st.markdown("### Required CSV columns")
    format_df = pd.DataFrame({
        "Column": ["sample_id", "condition", "run_id"],
        "Type": ["String", "String", "String"],
        "Description": [
            "Unique identifier for each biological sample",
            "Experimental group — must match the group1 and group2 names exactly",
            "SRA run accession (e.g. SRR2584863) or path to local FASTQ file"
        ],
        "Example": ["ctrl_1", "control", "SRR2584863"]
    })
    st.dataframe(format_df, hide_index=True, use_container_width=True)

    st.markdown("### Example CSV files")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("**Two-condition comparison:**")
        ex1 = pd.DataFrame({
            "sample_id": ["ctrl_1","ctrl_2","ctrl_3","treat_1","treat_2","treat_3"],
            "condition": ["control","control","control","treated","treated","treated"],
            "run_id": ["SRR001","SRR002","SRR003","SRR004","SRR005","SRR006"]
        })
        st.dataframe(ex1, hide_index=True, use_container_width=True)

    with col_e2:
        st.markdown("**Clinical comparison (LN+ vs LN-):**")
        ex2 = pd.DataFrame({
            "sample_id": ["ln_pos_1","ln_pos_2","ln_pos_3","ln_neg_1","ln_neg_2","ln_neg_3"],
            "condition": ["LN_positive","LN_positive","LN_positive","LN_negative","LN_negative","LN_negative"],
            "run_id": ["SRR101","SRR102","SRR103","SRR104","SRR105","SRR106"]
        })
        st.dataframe(ex2, hide_index=True, use_container_width=True)

    st.markdown("### Important notes")
    st.markdown("""
- Each row represents one SRA run accession
- If a sample has multiple runs, list each on a separate row with the same **sample_id** — the pipeline merges them automatically
- To use local FASTQ files, provide the full file path in the **run_id** column
- Minimum recommended: **3 biological replicates per condition**
- The pipeline requires at least **2 conditions** to perform differential expression analysis
    """)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — EXAMPLE RESULTS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📊 Example Results")
    st.markdown("Results from the four cancer datasets analysed in this thesis using AutoRetroAb.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### 🔵 Melanoma — Serum starvation")
        st.markdown("""
| Output | Result |
|--------|--------|
| Cell lines | SK-MEL-5, SK-MEL-28 |
| Key locus | HML2_7q22.2 |
| Conserved stress locus | MER4_3q29f |
| Novel framework | Distance-to-normal |
        """)

        st.markdown("### 🟠 Bladder cancer — Cisplatin vs control")
        st.markdown("""
| Output | Result |
|--------|--------|
| Significant HERV loci | 111 |
| Upregulated | 67 |
| Downregulated | 44 |
| Concordance with carboplatin | 91.9% |
| Chr19 enrichment | p < 0.05 |
        """)

    with col_r2:
        st.markdown("### 🟢 Breast cancer — Lymph node metastasis")
        st.markdown("""
| Output | Result |
|--------|--------|
| Significant HERV loci | 4 |
| All downregulated | 100% |
| Xq13.2 enrichment p | 0.00153 |
| Xq13.2 enrichment OR | 37.56 |
| FTX co-suppressed L1 loci | 3 |
        """)

        st.markdown("### 🟣 Ovarian cancer — SOX2 knockdown")
        st.markdown("""
| Output | Result |
|--------|--------|
| Significant HERV loci | 16 |
| Downregulated | 14 |
| HML2 enrichment OR | 14.6 |
| HML2 enrichment p | 0.0039 |
| SOX2 motifs in DE loci | 14 of 16 |
        """)

    st.divider()
    st.markdown("### Pipeline output structure")
    st.code("""
results/my_analysis/
├── counts/
│   ├── merged_herv_counts.tsv
│   └── merged_l1_counts.tsv
├── filtered/
│   ├── filtered_herv_counts.tsv
│   └── filtered_l1_counts.tsv
├── de/
│   ├── herv_deseq2_results.csv
│   ├── l1_deseq2_results.csv
│   ├── top10_herv_up.csv
│   └── top10_herv_down.csv
├── enrichment/
│   ├── herv_family_enrichment.csv
│   └── l1_family_enrichment.csv
├── chromosomal/
│   ├── herv_chromosomal_distribution.csv
│   └── l1_chromosomal_distribution.csv
├── plots/
│   ├── herv_volcano.png
│   └── l1_volcano.png
└── reports/
    └── summary_report.txt
    """, language="bash")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.85rem; padding: 1rem;">
    AutoRetroAb v1.0.0 · Abrar Alghamdi · University of Leicester ·
    <a href="https://github.com/AbrarAlghamdi/AutoRetroAb" target="_blank">GitHub</a> ·
    <a href="https://autoretroab.streamlit.app" target="_blank">Web Interface</a>
</div>
""", unsafe_allow_html=True)
