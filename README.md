# AutoRetroAb

**AutoRetroAb** is an automated RNA-seq pipeline for retrotransposon transcriptomics, focusing on **HERV (Human Endogenous Retroviruses)** and **LINE-1 (L1)** locus-level quantification.

The pipeline enables reproducible analysis of public RNA-seq datasets, from raw data download to differential expression and downstream interpretation.

---

##  Features

* Create analysis jobs from **SRR IDs** or **CSV input**
* Automatically download RNA-seq data from SRA
* Automatically download the **hg38 reference genome** (if missing)
* Automatically build **Bowtie2 index**
* Align reads to hg38
* Quantify retrotransposon loci using Telescope
* Perform differential expression analysis using DESeq2
* Generate:

  * volcano plots
  * top up/down regulated loci
  * family enrichment analysis
  * chromosomal distribution
  * summary report

---

## Project Structure

```bash
AutoRetroAb/
├── src/autoretroab/        # Python package and CLI
├── workflow/               # Snakemake workflow
├── scripts/                # Python and R helper scripts
├── resources/
│   ├── annotations/        # GTF files (HERV, L1)
│   └── metadata/           # locus metadata tables
├── jobs/                   # generated job configurations
├── results/                # pipeline outputs
├── environment.yml         # conda environment
├── pyproject.toml          # package configuration
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AbrarAlghamdi/AutoRetroAb.git
cd AutoRetroAb
```

---

### 2. Create the conda environment

```bash
conda env create -f environment.yml
conda activate autoretroab
```

---

### 3. Install the pipeline

```bash
pip install -e .
```

---

### 4. Test installation

```bash
autoretroab --help
```

---

##  Usage

### Option 1: Create a job from CSV

Create a CSV file:

```csv
sample_id,condition,run_id
ctrl_1,control,SRR2584863
ctrl_2,control,SRR2584864
treat_1,treated,SRR2584865
treat_2,treated,SRR2584866
```

Run:

```bash
autoretroab create-job-from-csv myjob \
  --group1 control \
  --group2 treated \
  --csv samples.csv
```

---

### Option 2: Create a job from SRR IDs

```bash
autoretroab create-job myjob \
  --group1 control \
  --group2 treated \
  --sample ctrl_1:control:SRR2584863 \
  --sample ctrl_2:control:SRR2584864 \
  --sample treat_1:treated:SRR2584865 \
  --sample treat_2:treated:SRR2584866
```

---

### Run the pipeline

```bash
autoretroab run --config jobs/myjob/config.yaml --cores 4
```

---

##  What happens automatically

The pipeline performs:

1. Download RNA-seq FASTQ files from SRA
2. Download the hg38 genome (if missing)
3. Build Bowtie2 index (if missing)
4. Align reads to the genome
5. Quantify HERV and LINE-1 loci using Telescope
6. Merge locus-level counts
7. Filter low-expression loci
8. Run DESeq2 differential expression analysis
9. Extract top upregulated and downregulated loci
10. Perform **family enrichment analysis**
11. Generate **chromosomal distribution summaries**
12. Create volcano plots and a final summary report

---

##  Output

All results are stored in:

```bash
results/<job_name>/
```

### Counts

```bash
results/<job>/counts/
```

* `merged_herv_counts.tsv`
* `merged_l1_counts.tsv`

---

### Filtered counts

```bash
results/<job>/filtered/
```

* `filtered_herv_counts.tsv`
* `filtered_l1_counts.tsv`

---

### Differential expression

```bash
results/<job>/de/
```

* `herv_deseq2_results.csv`
* `l1_deseq2_results.csv`
* `top10_herv_up.csv`
* `top10_herv_down.csv`
* `top10_l1_up.csv`
* `top10_l1_down.csv`

---

### Family enrichment

```bash
results/<job>/enrichment/
```

* `herv_family_enrichment.csv`
* `l1_family_enrichment.csv`

---

### Chromosomal distribution

```bash
results/<job>/chromosomal/
```

* `herv_chromosomal_distribution.csv`
* `l1_chromosomal_distribution.csv`

---

### Plots

```bash
results/<job>/plots/
```

* `herv_volcano.png`
* `l1_volcano.png`

---

### Final report

```bash
results/<job>/reports/
```

* `summary_report.txt`

---

## input format

CSV must contain:

```csv
sample_id,condition,run_id
```

Example:

```csv
ctrl_1,control,SRR2584863
ctrl_2,control,SRR2584864
treat_1,treated,SRR2584865
treat_2,treated,SRR2584866
```

---

## Supported Platforms

Recommended:

* Linux (Ubuntu or similar)
* Windows via WSL2

Possible:

* macOS (not fully tested)

---

## Notes

* Ensure sufficient disk space (10–50 GB depending on dataset)

---

## Requirements

* Python 3.10
* Snakemake
* Bowtie2
* Samtools
* SRA Toolkit (`fasterq-dump`)
* R + DESeq2
* Telescope

(All handled automatically via `environment.yml`)

---


## 

Abrar Alghamdi
PhD in Bioinformatics
University of Leicester

---


