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
    .warning-box {
        background: #FFF9C4;
        border-left: 4px solid #F57F17;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)



# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/AbrarAlghamdi/AutoRetroAb/main/docs/logo.png",
             use_container_width=True) if False else None
    st.markdown("## 🔬 AutoRetroAb")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Developer:** Abrar Alghamdi")
    st.markdown("**Institution:** University of Leicester")
    st.divider()
    st.markdown("### 📚 Resources")
    st.markdown("[📖 GitHub Repository](https://github.com/AbrarAlghamdi/AutoRetroAb)")
    st.markdown("[📄 Documentation](https://github.com/AbrarAlghamdi/AutoRetroAb#readme)")
    st.markdown("[🐳 Docker Image](https://hub.docker.com/r/abraralghamdi/autoretroab)")
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

# ── MAIN TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Run Pipeline",
    "📋 Input Format",
    "⚙️ Advanced Parameters",
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
    expression analysis.
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

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {"sample_id", "condition", "run_id"}
            if required_cols.issubset(df.columns):
                st.success(f"✅ Valid CSV — {len(df)} samples detected")
                st.dataframe(df, hide_index=True, use_container_width=True)

                # Show summary
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
    else:
        df = None

    st.divider()

    # ── STEP 2 ──
    st.markdown("### Step 2 — Configure your job")
    col_j1, col_j2, col_j3 = st.columns(3)
    with col_j1:
        job_name = st.text_input("Job name", value="my_analysis",
                                  help="A name for your analysis — no spaces")
    with col_j2:
        if df is not None and "condition" in df.columns:
            conditions_list = list(df["condition"].unique())
        else:
            conditions_list = ["control", "treated"]
        group1 = st.selectbox("Control group", conditions_list,
                               help="Select the control/reference condition")
    with col_j3:
        remaining = [c for c in conditions_list if c != group1]
        group2 = st.selectbox("Treatment group",
                               remaining if remaining else conditions_list,
                               help="Select the treatment/comparison condition")

    st.divider()

    # ── STEP 3 ──
    st.markdown("### Step 3 — Analysis type")
    analysis_type = st.radio(
        "Which retrotransposons to analyse?",
        ["HERV and LINE-1 (recommended)", "HERV only", "LINE-1 only"],
        horizontal=True
    )

    st.divider()

    # ── STEP 4 ──
    st.markdown("### Step 4 — Run the pipeline")

 

    if df is not None and job_name:
        # Generate the command
        cmd_parts = [
            f"autoretroab create-job-from-csv {job_name}",
            f"  --group1 {group1}",
            f"  --group2 {group2}",
            f"  --csv samples.csv"
        ]
        run_cmd = f"autoretroab run --config jobs/{job_name}/config.yaml --cores 4"

        st.markdown("**Your commands — copy and run these in your terminal:**")

        st.code("\n".join(cmd_parts), language="bash")
        st.code(run_cmd, language="bash")

        # Download config button
        config_content = f"""# AutoRetroAb Job Configuration
# Generated by AutoRetroAb Web Interface

job_name: {job_name}
group1: {group1}
group2: {group2}
analysis_type: {analysis_type}
samples_csv: samples.csv
"""
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Download job config YAML",
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
    else:
        st.info("👆 Upload a CSV file and enter a job name to generate your run command")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — INPUT FORMAT
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Input File Format")

    st.markdown("### Required CSV columns")
    format_df = pd.DataFrame({
        "Column": ["sample_id", "condition", "run_id"],
        "Type": ["String", "String", "String (SRA accession)"],
        "Description": [
            "Unique identifier for each biological sample",
            "Experimental group — must match group1 and group2 names exactly",
            "SRA run accession number (e.g. SRR2584863). For local files, provide the file path."
        ],
        "Example": ["ctrl_1", "control", "SRR2584863"]
    })
    st.dataframe(format_df, hide_index=True, use_container_width=True)

    st.markdown("### Example CSV files")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("**Two-condition comparison (e.g. treated vs control):**")
        ex1 = pd.DataFrame({
            "sample_id": ["ctrl_1","ctrl_2","ctrl_3","treat_1","treat_2","treat_3"],
            "condition": ["control","control","control","treated","treated","treated"],
            "run_id": ["SRR001","SRR002","SRR003","SRR004","SRR005","SRR006"]
        })
        st.dataframe(ex1, hide_index=True, use_container_width=True)

    with col_e2:
        st.markdown("**Clinical comparison (e.g. LN+ vs LN-):**")
        ex2 = pd.DataFrame({
            "sample_id": ["ln_pos_1","ln_pos_2","ln_pos_3","ln_neg_1","ln_neg_2","ln_neg_3"],
            "condition": ["LN_positive","LN_positive","LN_positive","LN_negative","LN_negative","LN_negative"],
            "run_id": ["SRR101","SRR102","SRR103","SRR104","SRR105","SRR106"]
        })
        st.dataframe(ex2, hide_index=True, use_container_width=True)

    st.markdown("### Notes")
    st.markdown("""
    - Each row represents one SRA run. If a sample has multiple runs, list each run on a separate row with the same **sample_id**
    - The pipeline automatically merges multiple runs belonging to the same sample before analysis
    - To use local FASTQ files instead of SRA accessions, provide the full file path in the **run_id** column
    - Minimum recommended: 3 biological replicates per condition
    """)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — ADVANCED PARAMETERS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Advanced Parameters")
    st.markdown("""
    <div class="step-box">
    AutoRetroAb uses validated default parameters for all analyses. Most users do not need
    to change anything. Advanced users can customise the parameters below.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("### Differential Expression")
        log2fc = st.slider(
            "Log2 fold change threshold",
            min_value=0.5, max_value=3.0, value=1.0, step=0.1,
            help="Minimum fold change for significance. Default 1.0 = twofold change"
        )
        fdr = st.select_slider(
            "FDR threshold",
            options=[0.01, 0.05, 0.10],
            value=0.05,
            help="Benjamini-Hochberg adjusted p-value threshold"
        )
        min_counts = st.slider(
            "Minimum read count filter",
            min_value=1, max_value=50, value=10, step=1,
            help="Minimum Telescope final counts to include a locus in analysis"
        )

    with col_p2:
        st.markdown("### Alignment and Annotation")
        k_value = st.select_slider(
            "Bowtie2 -k parameter",
            options=[100, 200, 300],
            value=100,
            help="Maximum alignments per read. 100 is validated and recommended."
        )
        proximity_window = st.select_slider(
            "Nearest gene proximity window (bp)",
            options=[5000, 10000, 25000, 50000],
            value=10000,
            help="Window size for nearest gene mapping"
        )
        top_hits = st.slider(
            "Top DE loci to report",
            min_value=5, max_value=50, value=10, step=5,
            help="Number of top up/down regulated loci in summary report"
        )

    st.divider()
    st.markdown("### Current parameter summary")
    params_df = pd.DataFrame({
        "Parameter": [
            "Log2 fold change threshold",
            "FDR threshold",
            "Minimum count filter",
            "Bowtie2 -k value",
            "Proximity window",
            "Top hits reported"
        ],
        "Your value": [log2fc, fdr, min_counts, k_value, f"{proximity_window:,} bp", top_hits],
        "Default": [1.0, 0.05, 10, 100, "10,000 bp", 10],
        "Status": [
            "✅ Default" if log2fc == 1.0 else "⚙️ Modified",
            "✅ Default" if fdr == 0.05 else "⚙️ Modified",
            "✅ Default" if min_counts == 10 else "⚙️ Modified",
            "✅ Default" if k_value == 100 else "⚙️ Modified",
            "✅ Default" if proximity_window == 10000 else "⚙️ Modified",
            "✅ Default" if top_hits == 10 else "⚙️ Modified",
        ]
    })
    st.dataframe(params_df, hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXAMPLE RESULTS
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Example Results")
    st.markdown("Examples of the outputs produced by AutoRetroAb from the four cancer datasets analysed in this thesis.")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### Bladder cancer — Cisplatin vs control")
        st.markdown("""
        | Output | Result |
        |--------|--------|
        | Significant HERV loci | 111 |
        | Upregulated | 67 |
        | Downregulated | 44 |
        | Top locus | HML2_19p12b |
        | Chr19 enrichment | p < 0.05 |
        | HML2 family enrichment | p < 0.05 |
        """)

    with col_r2:
        st.markdown("### Ovarian cancer — SOX2 knockdown")
        st.markdown("""
        | Output | Result |
        |--------|--------|
        | Significant HERV loci | 16 |
        | Upregulated | 2 |
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
    <a href="https://github.com/AbrarAlghamdi/AutoRetroAb" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
