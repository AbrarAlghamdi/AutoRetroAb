import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import gzip

from autoretroab import __version__


GENCODE_PRIMARY_FASTA_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_49/"
    "GRCh38.primary_assembly.genome.fa.gz"
)


def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_command(cmd):
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def run_pipeline(config: str, cores=None, rerun_incomplete: bool = False,
                 profile=None, dry_run: bool = False):
    project_root = get_project_root()
    snakefile = os.path.join(project_root, "workflow", "Snakefile")

    cmd = [
        "snakemake",
        "-s", snakefile,
        "--configfile", config,
        "-p",
    ]

    if profile:
        # e.g. profiles/slurm: submits each rule as a SLURM job
        cmd += ["--profile", profile]
        if cores is not None:
            cmd += ["--cores", str(cores)]
    else:
        cmd += ["--cores", str(cores if cores is not None else 4)]

    if rerun_incomplete:
        cmd.append("--rerun-incomplete")
    if dry_run:
        cmd.append("--dry-run")

    print("Running:", " ".join(cmd))

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def parse_sample_entries(sample_entries):
    rows = []
    for entry in sample_entries:
        parts = entry.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid --sample value: {entry}\n"
                "Use format: sample_id:condition:SRR"
            )
        sample_id, condition, run_id = parts
        rows.append(
            {
                "sample_id": sample_id.strip(),
                "condition": condition.strip(),
                "run_id": run_id.strip(),
            }
        )
    return rows


def load_samples_from_csv(csv_path):
    """Read samples from CSV.

    Required columns: sample_id, condition, and either run_id (SRA accession)
    or r1 (local FASTQ; add r2 for paired-end). Each row must provide a
    run_id or an r1 path.
    """
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if not {"sample_id", "condition"}.issubset(fields) or not (
            "run_id" in fields or "r1" in fields
        ):
            raise ValueError(
                "CSV must contain columns: sample_id, condition, and run_id "
                "and/or r1 (plus r2 for paired-end local FASTQ)"
            )
        for line_no, row in enumerate(reader, start=2):
            entry = {
                "sample_id": (row.get("sample_id") or "").strip(),
                "condition": (row.get("condition") or "").strip(),
                "run_id": (row.get("run_id") or "").strip(),
                "r1": (row.get("r1") or "").strip(),
                "r2": (row.get("r2") or "").strip(),
            }
            if not entry["sample_id"] or not entry["condition"]:
                raise ValueError(f"Line {line_no}: sample_id and condition are required")
            if not entry["run_id"] and not entry["r1"]:
                raise ValueError(
                    f"Line {line_no} ({entry['sample_id']}): provide run_id or r1"
                )
            if entry["r2"] and not entry["r1"]:
                raise ValueError(
                    f"Line {line_no} ({entry['sample_id']}): r2 given without r1"
                )
            rows.append(entry)
    return rows


def link_local_fastqs(rows, raw_dir):
    """Symlink local FASTQ files into raw_dir using the names the pipeline
    expects (<id>_1/_2.fastq.gz or <id>.fastq.gz) and set run_id to sample_id.
    Returns the list of SRA run IDs that still need downloading."""
    sra_ids = []
    for row in rows:
        r1 = row.get("r1", "")
        if not r1:
            sra_ids.append(row["run_id"])
            continue

        r2 = row.get("r2", "")
        run_id = row["sample_id"]
        targets = [(r1, f"{run_id}_1.fastq.gz"), (r2, f"{run_id}_2.fastq.gz")] if r2 \
            else [(r1, f"{run_id}.fastq.gz")]

        for src, name in targets:
            src_abs = os.path.abspath(os.path.expanduser(src))
            if not src_abs.endswith(".gz"):
                raise ValueError(f"{row['sample_id']}: FASTQ must be gzipped (.gz): {src}")
            if not os.path.exists(src_abs):
                raise FileNotFoundError(f"{row['sample_id']}: FASTQ not found: {src_abs}")
            if os.path.getsize(src_abs) == 0:
                raise ValueError(f"{row['sample_id']}: FASTQ file is empty: {src_abs}")
            try:
                with gzip.open(src_abs, "rb") as _fh:
                    has_data = bool(_fh.read(1024))
            except OSError as _e:
                raise ValueError(
                    f"{row['sample_id']}: FASTQ is not a valid gzip file "
                    f"(possibly corrupt or truncated): {src_abs} ({_e})"
                )
            if not has_data:
                raise ValueError(f"{row['sample_id']}: FASTQ contains no reads: {src_abs}")
            dest = os.path.join(raw_dir, name)
            if os.path.lexists(dest):
                os.remove(dest)
            os.symlink(src_abs, dest)

        row["run_id"] = run_id
    return sra_ids


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download_file(url, out_path):
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, out_path)
    print(f"Saved to {out_path}")


def gunzip_file(gz_path, out_path):
    print(f"Decompressing {gz_path}")
    with gzip.open(gz_path, "rb") as fin, open(out_path, "wb") as fout:
        shutil.copyfileobj(fin, fout)
    print(f"Wrote {out_path}")


def setup_reference():
    project_root = get_project_root()
    ref_dir = os.path.join(project_root, "resources", "reference")
    bt2_dir = os.path.join(ref_dir, "hg38_bt2")
    fasta_path = os.path.join(ref_dir, "hg38.primary_assembly.fa")
    gz_path = fasta_path + ".gz"
    bt2_prefix = os.path.join(bt2_dir, "hg38")

    ensure_dir(ref_dir)
    ensure_dir(bt2_dir)

    if not os.path.exists(fasta_path):
        if not os.path.exists(gz_path):
            download_file(GENCODE_PRIMARY_FASTA_URL, gz_path)
        gunzip_file(gz_path, fasta_path)
    else:
        print(f"Found FASTA: {fasta_path}")

    expected_index_files = [
        bt2_prefix + ".1.bt2",
        bt2_prefix + ".2.bt2",
        bt2_prefix + ".3.bt2",
        bt2_prefix + ".4.bt2",
        bt2_prefix + ".rev.1.bt2",
        bt2_prefix + ".rev.2.bt2",
    ]

    if all(os.path.exists(p) for p in expected_index_files):
        print("Bowtie2 index already exists.")
    else:
        run_command(["bowtie2-build", fasta_path, bt2_prefix])

    print("Reference setup complete.")
    print(f"FASTA: {fasta_path}")
    print(f"Bowtie2 index prefix: {bt2_prefix}")


def write_job_files(job_name: str, group1: str, group2: str, rows):
    project_root = get_project_root()

    job_dir = os.path.join(project_root, "jobs", job_name)
    results_dir = os.path.join(project_root, "results", job_name)

    resources_dir = os.path.join(project_root, "resources")
    bowtie_index_base = os.path.join(resources_dir, "reference", "hg38_bt2", "hg38")
    genome_fasta = os.path.join(resources_dir, "reference", "hg38.primary_assembly.fa")

    herv_gtf = os.path.join(resources_dir, "annotations", "HERV_rmsk.hg38.v2.2.gtf")
    l1_gtf = os.path.join(resources_dir, "annotations", "L1.cleaned.gtf")

    herv_meta = os.path.join(resources_dir, "metadata", "herv_locus_metadata.tsv")
    l1_meta = os.path.join(resources_dir, "metadata", "l1_locus_metadata.tsv")

    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    raw_dir = os.path.join(results_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    srr_ids = link_local_fastqs(rows, raw_dir)

    samples_path = os.path.join(job_dir, "samples.tsv")
    comparison_path = os.path.join(job_dir, "comparison.tsv")
    input_json_path = os.path.join(job_dir, "input.json")
    config_path = os.path.join(job_dir, "config.yaml")

    with open(samples_path, "w") as f:
        f.write("sample_id\trun_id\tcondition\n")
        for row in rows:
            f.write(f"{row['sample_id']}\t{row['run_id']}\t{row['condition']}\n")

    with open(comparison_path, "w") as f:
        f.write("comparison\tgroup1\tgroup2\n")
        f.write(f"main\t{group1}\t{group2}\n")

    input_json = {
        "job_id": 1,
        "user_id": 1,
        "job_name": job_name,
        "db_type": "sra",
        "ids": srr_ids,
        "output_dir": raw_dir,
        "max_concurrent": 4,
    }

    with open(input_json_path, "w") as f:
        json.dump(input_json, f, indent=4)

    config_text = f"""job_name: {job_name}
reference: hg38

genome_fasta: {genome_fasta}
bowtie2_index: {bowtie_index_base}

herv_gtf: {herv_gtf}
l1_gtf: {l1_gtf}

samples_file: {samples_path}
comparison_file: {comparison_path}
input_json: {input_json_path}

herv_locus_metadata: {herv_meta}
l1_locus_metadata: {l1_meta}

output_root: {results_dir}

threads: 4
min_count: 10
alpha: 0.05
log2fc_threshold: 1

telescope_bin: telescope
"""

    with open(config_path, "w") as f:
        f.write(config_text)

    print(f"Job '{job_name}' created.")
    print(f"Config: {config_path}")
    print("Run with:")
    print(f"  autoretroab run --config {config_path} --cores 4")


def create_job(job_name: str, group1: str, group2: str, sample_entries):
    rows = parse_sample_entries(sample_entries)
    write_job_files(job_name, group1, group2, rows)


def create_job_from_csv(job_name: str, group1: str, group2: str, csv_path: str):
    rows = load_samples_from_csv(csv_path)
    write_job_files(job_name, group1, group2, rows)


def init_csv(path: str):
    with open(path, "w") as f:
        f.write("sample_id,condition,run_id\n")
        f.write("sample1,control,SRRXXXX\n")
        f.write("sample2,treated,SRRYYYY\n")

    print(f"Template CSV created: {path}")
    print("Edit this file with your real samples.")


def main():
    parser = argparse.ArgumentParser(prog="autoretroab")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run the pipeline")
    run.add_argument("--config", required=True)
    run.add_argument("--cores", default=None,
                     help="CPU cores (default 4 when running locally)")
    run.add_argument("--profile", default=None,
                     help="Snakemake profile directory, e.g. profiles/slurm")
    run.add_argument("--dry-run", action="store_true",
                     help="Show the jobs that would run without running them")
    run.add_argument("--rerun-incomplete", action="store_true")

    create = sub.add_parser("create-job", help="Create a job directly from --sample entries")
    create.add_argument("name", help="Job name")
    create.add_argument("--group1", required=True)
    create.add_argument("--group2", required=True)
    create.add_argument(
        "--sample",
        action="append",
        required=True,
        help="sample_id:condition:SRR",
    )

    create_csv = sub.add_parser("create-job-from-csv", help="Create a job from CSV")
    create_csv.add_argument("name", help="Job name")
    create_csv.add_argument("--group1", required=True)
    create_csv.add_argument("--group2", required=True)
    create_csv.add_argument("--csv", required=True)

    init = sub.add_parser("init-csv", help="Create a template CSV file")
    init.add_argument("path")

    setup = sub.add_parser("setup-reference", help="Download hg38 FASTA and build Bowtie2 index")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args.config, args.cores, args.rerun_incomplete,
                     args.profile, args.dry_run)
    elif args.command == "create-job":
        create_job(args.name, args.group1, args.group2, args.sample)
    elif args.command == "create-job-from-csv":
        create_job_from_csv(args.name, args.group1, args.group2, args.csv)
    elif args.command == "init-csv":
        init_csv(args.path)
    elif args.command == "setup-reference":
        setup_reference()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
