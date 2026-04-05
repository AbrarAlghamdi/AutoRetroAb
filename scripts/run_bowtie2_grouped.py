import argparse
import os
import sys
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Build the Bowtie2 command for one biological sample."
    )
    parser.add_argument("--sample", required=True, help="Sample ID to align")
    parser.add_argument("--samples", required=True, help="Path to samples.tsv")
    parser.add_argument("--rawdir", required=True, help="Directory containing FASTQ files")
    parser.add_argument("--index", required=True, help="Bowtie2 index base path")
    parser.add_argument("--threads", type=int, default=4, help="Bowtie2 threads")
    args = parser.parse_args()

    df = pd.read_csv(args.samples, sep="\t")

    if "sample_id" not in df.columns or "run_id" not in df.columns:
        print("samples.tsv must contain columns: sample_id, run_id", file=sys.stderr)
        sys.exit(1)

    sub = df[df["sample_id"] == args.sample]
    if sub.empty:
        print(f"No rows found for sample: {args.sample}", file=sys.stderr)
        sys.exit(1)

    r1_files = []
    r2_files = []
    single_files = []

    for run_id in sub["run_id"]:
        r1 = os.path.join(args.rawdir, f"{run_id}_1.fastq.gz")
        r2 = os.path.join(args.rawdir, f"{run_id}_2.fastq.gz")

        if os.path.exists(r1) and os.path.exists(r2):
            r1_files.append(r1)
            r2_files.append(r2)
        elif os.path.exists(r1):
            single_files.append(r1)
        else:
            print(f"Missing FASTQ for run: {run_id}", file=sys.stderr)
            sys.exit(1)

    if r1_files and r2_files and not single_files:
        cmd = [
            "bowtie2",
            "--very-sensitive-local",
            "-k", "100",
            "-p", str(args.threads),
            "-x", args.index,
            "-1", ",".join(r1_files),
            "-2", ",".join(r2_files)
        ]
        print("Detected paired-end mode", file=sys.stderr)
    elif single_files and not r1_files and not r2_files:
        cmd = [
            "bowtie2",
            "--very-sensitive-local",
            "-k", "100",
            "-p", str(args.threads),
            "-x", args.index,
            "-U", ",".join(single_files)
        ]
        print("Detected single-end mode", file=sys.stderr)
    else:
        print("Mixed single-end and paired-end files detected for the same sample.", file=sys.stderr)
        sys.exit(1)

    print(" ".join(cmd))


if __name__ == "__main__":
    main()
