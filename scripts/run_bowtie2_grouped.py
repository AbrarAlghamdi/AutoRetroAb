import argparse
import os
import sys
import pandas as pd


def find_fastq_files(rawdir: str, run_id: str):
    run_dir = os.path.join(rawdir, run_id)

    paired_1 = os.path.join(run_dir, f"{run_id}_1.fastq.gz")
    paired_2 = os.path.join(run_dir, f"{run_id}_2.fastq.gz")
    single = os.path.join(run_dir, f"{run_id}.fastq.gz")

    if os.path.exists(paired_1) and os.path.exists(paired_2):
        return "paired", paired_1, paired_2

    if os.path.exists(single):
        return "single", single

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--rawdir", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    df = pd.read_csv(args.samples, sep="\t")

    row = df[df["sample_id"] == args.sample]
    if row.empty:
        print(f"Sample not found in samples file: {args.sample}", file=sys.stderr)
        sys.exit(1)

    run_id = row.iloc[0]["run_id"]

    result = find_fastq_files(args.rawdir, run_id)
    if result is None:
        print(f"Missing FASTQ for run: {run_id}", file=sys.stderr)
        sys.exit(1)

    if result[0] == "paired":
        _, fq1, fq2 = result
        cmd = (
            f"bowtie2 -x {args.index} "
            f"-1 {fq1} -2 {fq2} "
            f"-p {args.threads}"
        )
    else:
        _, fq = result
        cmd = (
            f"bowtie2 -x {args.index} "
            f"-U {fq} "
            f"-p {args.threads}"
        )

    print(cmd)


if __name__ == "__main__":
    main()
