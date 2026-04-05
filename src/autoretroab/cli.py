import argparse
import csv
import json
import os
import subprocess
import sys


def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_pipeline(config: str, cores: str, rerun_incomplete: bool = False):
    project_root = get_project_root()
    snakefile = os.path.join(project_root, "workflow", "Snakefile")

    cmd = [
        "snakemake",
        "-s", snakefile,
        "--configfile", config,
        "--cores", str(cores),
        "-p",
    ]

    if rerun_incomplete:
        cmd.append("--rerun-incomplete")

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
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        required = {"sample_id", "condition", "run_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"CSV must contain columns: {', '.join(sorted(required))}"
            )
        for row in reader:
            rows.append(
                {
                    "sample_id": row["sample_id"].strip(),
                    "condition": row["condition"].strip(),
                    "run_id": row["run_id"].strip(),
                }
            )
    return rows


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

    srr_ids = [row["run_id"] for row in rows]
    input_json = {
        "job_id": 1,
        "user_id": 1,
        "job_name": job_name,
        "db_type": "sra",
        "ids": srr_ids,
        "output_dir": os.path.join(results_dir, "raw"),
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
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run the pipeline")
    run.add_argument("--config", required=True)
    run.add_argument("--cores", default="4")
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

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args.config, args.cores, args.rerun_incomplete)
    elif args.command == "create-job":
        create_job(args.name, args.group1, args.group2, args.sample)
    elif args.command == "create-job-from-csv":
        create_job_from_csv(args.name, args.group1, args.group2, args.csv)
    elif args.command == "init-csv":
        init_csv(args.path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
