# AutoRetroAb

Automated RNA-seq pipeline for retrotransposon analysis from public RNA-seq data, with support for HERV and LINE-1 locus-level quantification.

## Features

- Create jobs from SRR IDs or CSV input
- Download RNA-seq data from SRA
- Align reads to hg38 using Bowtie2
- Quantify retrotransposon loci
- Run differential expression analysis with DESeq2
- Produce summary outputs for downstream analysis

## Project structure

```bash
src/autoretroab/        # Python package and CLI
workflow/               # Snakemake workflow
scripts/                # Python and R helper scripts
resources/annotations/  # GTF annotations
resources/metadata/     # locus metadata tables
jobs/                   # generated job configurations
results/                # pipeline outputs


## Quick start

1. Clone the repository
2. Create the conda environment
3. Install the package
4. Create a job
5. Run the pipeline


## Installation

Clone the repository:

```bash
git clone https://github.com/AbrarAlghamdi/AutoRetroAb.git
cd AutoRetroAb
conda env create -f environment.yml
conda activate autoretroab
pip install -e .

autoretroab --help

---

## Usage

```md
## Usage

### Create a job from a CSV file

Prepare a CSV file with the following columns:

```csv
sample_id,condition,run_id
ctrl_1,control,SRR2584863
ctrl_2,control,SRR2584864
treat_1,treated,SRR2584865
treat_2,treated,SRR2584866


Create a job:
autoretroab create-job-from-csv small_test \
  --group1 control \
  --group2 treated \
  --csv small_dataset.csv


Run the pipeline:
autoretroab run --config jobs/small_test/config.yaml --cores 4

Create a job directly from SRR IDs

autoretroab create-job test_run \
  --group1 control \
  --group2 treated \
  --sample ctrl_1:control:SRR2584863 \
  --sample ctrl_2:control:SRR2584864 \
  --sample treat_1:treated:SRR2584865 \
  --sample treat_2:treated:SRR2584866


Run:

autoretroab run --config jobs/test_run/config.yaml --cores 4
