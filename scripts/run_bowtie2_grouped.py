import argparse
import os
import sys
import pandas as pd


def find_fastq_files(rawdir: str, run_id: str):
    rawdir = os.path.abspath(str(rawdir).strip())
    run_id = str(run_id).strip()

    run_dir = os.path.join(rawdir, run_id)

    paired_1 = os.path.join(run_dir, f"{run_id}_1.fastq.gz")
    paired_2 = os.path.join(run_dir, f"{run_id}_2.fastq.gz")
    single = os.path.join(run_dir, f"{run_id}.fastq.gz")

    if os.path.exists(paired_1) and os.path.exists(paired_2):
        return ("paired", paired_1, paired_2)

    if os.path.exists(single):
        return ("single", single)

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--rawdir", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    df = pd.read_csv(args.samples, sep="\t", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    required = {"sample_id", "run_id", "condition"}
    if not required.issubset(set(df.columns)):
        print(
            f"Missing required columns in samples file. Found: {list(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(1)

    df["sample_id"] = df["sample_id"].astype(str).str.strip()
    df["run_id"] = df["run_id"].astype(str).str.strip()

    sample = str(args.sample).strip()
    row = df[df["sample_id"] == sample]

    if row.empty:
        print(f"Sample not found in samples file: {sample}", file=sys.stderr)
        sys.exit(1)

    run_id = row.iloc[0]["run_id"]

    result = find_fastq_files(args.rawdir, run_id)
    if result is None:
        print(f"Missing FASTQ for run: {run_id}", file=sys.stderr)
        print(
            f"Checked in: {os.path.join(os.path.abspath(args.rawdir), run_id)}",
            file=sys.stderr,
        )
        sys.exit(1)

    index = os.path.abspath(str(args.index).strip())

    common_flags = f'-p {args.threads} -k 100 --very-sensitive'

    if result[0] == "paired":
        _, fq1, fq2 = result
        cmd = (
            f'bowtie2 -x "{index}" '
            f'-1 "{fq1}" -2 "{fq2}" '
            f'{common_flags}'
        )
    else:
        _, fq = result
        cmd = (
            f'bowtie2 -x "{index}" '
            f'-U "{fq}" '
            f'{common_flags}'
        )

    print(cmd)


if __name__ == "__main__":
    main()
