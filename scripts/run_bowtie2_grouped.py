import argparse
import os
import pandas as pd
import sys


def find_fastq_files(rawdir, run_id):
    candidates = {
        "single": [
            os.path.join(rawdir, f"{run_id}.fastq.gz"),
            os.path.join(rawdir, f"{run_id}.fastq"),
        ],
        "paired": [
            (
                os.path.join(rawdir, f"{run_id}_1.fastq.gz"),
                os.path.join(rawdir, f"{run_id}_2.fastq.gz"),
            ),
            (
                os.path.join(rawdir, f"{run_id}_1.fastq"),
                os.path.join(rawdir, f"{run_id}_2.fastq"),
            ),
        ],
    }

    for r1, r2 in candidates["paired"]:
        if os.path.exists(r1) and os.path.exists(r2):
            return ("paired", r1, r2)

    for f in candidates["single"]:
        if os.path.exists(f):
            return ("single", f)

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--rawdir", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--threads", required=True, type=int)
    args = parser.parse_args()

    samples = pd.read_csv(args.samples, sep="\t")
    row = samples.loc[samples["sample_id"] == args.sample]

    if row.empty:
        sys.stderr.write(f"Sample not found: {args.sample}\n")
        sys.exit(1)

    run_id = row.iloc[0]["run_id"]
    found = find_fastq_files(args.rawdir, run_id)

    if found is None:
        sys.stderr.write(f"Missing FASTQ for run: {run_id}\n")
        sys.exit(1)

    if found[0] == "paired":
        _, r1, r2 = found
        cmd = (
            f"bowtie2 -x {args.index} "
            f"-1 {r1} -2 {r2} "
            f"-p {args.threads}"
        )
    else:
        _, f = found
        cmd = (
            f"bowtie2 -x {args.index} "
            f"-U {f} "
            f"-p {args.threads}"
        )

    print(cmd)


if __name__ == "__main__":
    main()
