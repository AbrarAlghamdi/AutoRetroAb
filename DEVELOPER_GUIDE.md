# AutoRetroAb — Developer Guide

This guide documents the internal architecture of AutoRetroAb for developers and
advanced users who wish to understand, maintain, or extend the pipeline. For
installation and standard usage, see [`README.md`](README.md).

---

## 1. Architecture overview

AutoRetroAb is organised into three layers:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Interface layer** | `src/autoretroab/cli.py`, `app.py` | User-facing entry points. The CLI validates input, generates a per-job `config.yaml`, and launches the workflow. `app.py` provides an equivalent Streamlit web interface. |
| **Workflow layer** | `workflow/Snakefile` | A Snakemake workflow that defines all computational steps, their input/output file dependencies, and their execution order. Snakemake resolves the dependency graph and schedules steps in parallel up to `--cores`. |
| **Analysis layer** | `scripts/` | Standalone Python, Bash, and R scripts invoked by individual Snakemake rules. Each performs one well-defined task (alignment, quantification, filtering, statistics, reporting). |

The interface layer never calls the analysis scripts directly: it only generates a
configuration file and invokes Snakemake, which in turn calls the scripts. This
separation keeps the user-facing logic independent of the computational steps.

---

## 2. Repository layout

```
autoretroab/
├── src/autoretroab/cli.py      # CLI: input validation, config generation, run command
├── app.py                      # Streamlit web interface (prototype)
├── workflow/Snakefile          # Snakemake workflow (all computational rules)
├── scripts/                    # Analysis scripts called by the workflow
├── resources/
│   ├── annotations/            # Telescope-compatible GTF annotations (HERV, LINE-1)
│   ├── metadata/               # Per-locus metadata (family, chromosome)
│   └── qc/                     # Sequence-similarity QC locus lists
├── profiles/slurm/config.yaml  # SLURM/HPC execution profile
├── environment.yml             # Conda environment specification
└── samples.csv                 # Example sample sheet
```

---

## 3. Workflow modules

The workflow is divided into four sequential modules (A–D). The table below maps
each module to its Snakemake rules. HERV and LINE-1 are processed by parallel
rule pairs, since the two retrotransposon classes are quantified independently
against separate annotations.

### Module A — Data acquisition and reference preparation
| Rule | Tool | Function |
|------|------|----------|
| `download_genome_fasta` | wget | Retrieve the GRCh38/hg38 reference genome |
| `build_bowtie2_index` | bowtie2-build | Build the Bowtie2 index from the genome |
| `download_data` | SRA Toolkit (`downloader.py`) | Download FASTQ reads for each accession |

### Module B — Alignment and locus-specific quantification
| Rule | Tool | Function |
|------|------|----------|
| `align_to_bam` | Bowtie2 (`run_bowtie2_grouped.py`) | Align reads, retaining multi-mappers (`-k 100 --very-sensitive`) |
| `sort_bam_by_name` | SAMtools | Name-sort the BAM (required by Telescope) |
| `quantify_herv` / `quantify_l1` | Telescope | EM-based locus-level quantification |
| `merge_herv_counts` / `merge_l1_counts` | `merge_telescope_counts.py` | Assemble per-sample reports into a count matrix |

### Module C — Filtering and differential expression
| Rule | Tool | Function |
|------|------|----------|
| `filter_herv_counts` / `filter_l1_counts` | `filter_counts.R` | Remove low-count loci (`min_count`) |
| `run_deseq2_herv` / `run_deseq2_l1` | DESeq2 (`run_deseq2_generic.R`) | Differential expression (`alpha`, `log2fc_threshold`) |
| `extract_herv_top_hits` / `extract_l1_top_hits` | `extract_top_hits.R` | Extract the top differentially expressed loci |

### Module D — Enrichment analysis and reporting
| Rule | Tool | Function |
|------|------|----------|
| `herv_family_enrichment` / `l1_family_enrichment` | `family_enrichment.R` | Fisher's exact test for family-level enrichment |
| `herv_chromosomal_distribution` / `l1_chromosomal_distribution` | `chromosomal_distribution.R` | Fisher's exact test for chromosomal enrichment |
| `make_report` | `make_report.R` | Compile the final summary report |

`rule all` (top of the Snakefile) defines the final output targets that drive the
whole dependency graph.

---

## 4. Configurable parameters and their locations

Parameters fall into two groups: **user-tunable defaults** exposed in the job
configuration file, and **core method parameters** fixed in the analysis scripts.

### 4.1 User-tunable parameters — `config.yaml`
These are written into each job's `config.yaml` by the CLI (see `cli.py`) and can
be edited without touching any source code:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `min_count` | 10 | Minimum final count for a locus to be retained in filtering |
| `alpha` | 0.05 | DESeq2 adjusted-p significance threshold |
| `log2fc_threshold` | 1 | log₂ fold-change cut-off |
| `threads` | 4 | CPU threads budget |
| `genome_fasta`, `bowtie2_index` | — | Reference genome and index paths |
| `herv_gtf`, `l1_gtf` | — | Annotation paths (see §5 to extend) |
| `telescope_bin` | `telescope` | Telescope executable |

### 4.2 Core method parameters — fixed in scripts
These are intentionally **not** user-exposed, because changing them would
compromise the validity of locus-specific quantification:

| Parameter | Value | Location |
|-----------|-------|----------|
| Bowtie2 reporting / sensitivity | `-k 100 --very-sensitive` | `scripts/run_bowtie2_grouped.py` |

> **Design note:** `-k 100` retains up to 100 alignments per read. This is
> essential for recovering the multi-mapping reads on which transposable-element
> quantification depends, and is therefore fixed by design rather than exposed as
> a tunable option. If this value is ever changed, the change must be made in one
> place (`run_bowtie2_grouped.py`) and re-validated.

---

## 5. Extending the pipeline

### Adding new retrotransposon families
AutoRetroAb is annotation-driven. To quantify families beyond the bundled HERV
and LINE-1 sets:

1. Prepare a **Telescope-compatible GTF** for the new family (same format as
   `resources/annotations/HERV_rmsk.hg38.v2.2.gtf`, built on the matching
   GRCh38/hg38 assembly with UCSC `chr`-style chromosome names).
2. Place it in `resources/annotations/`.
3. Point the relevant `*_gtf` entry in `config.yaml` to the new file.

No change to the workflow logic is required: the quantification rules read the
annotation path from the configuration.

### Annotation–genome consistency
The annotation GTF and the genome FASTA **must** share the same assembly build
and chromosome-naming convention (UCSC `chr1…` here). A mismatch produces zero
counts rather than an error, so consistency should be verified before a run.

---

## 6. Dependencies

All software dependencies are pinned in [`environment.yml`](environment.yml)
(conda) and [`requirements.txt`](requirements.txt) (web interface). Core tools:
Snakemake, Bowtie2, SAMtools, Telescope, DESeq2 (Bioconductor), and the Python/R
libraries used by the analysis scripts.

---

## 7. Execution model

Snakemake builds a directed acyclic graph (DAG) of rules from their declared
input/output files and executes independent steps in parallel, up to the
`--cores` budget. `--cores` is an upper scheduling limit, not a hard requirement:
if more cores are requested than are physically available, the operating system
time-shares the workload across the available cores, which may reduce throughput
but does not affect correctness. Partial runs can be resumed, since Snakemake
only re-executes steps whose outputs are missing or out of date.
