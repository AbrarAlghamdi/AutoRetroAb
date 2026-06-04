import pandas as pd

de = pd.read_csv("deseq2_HERV_results.csv")

with open(
    "resources/qc/high_similarity_herv_loci.txt"
) as f:
    risky = set(
        line.strip()
        for line in f
    )

de["Similarity_Warning"] = de["transcript"].isin(risky)

de.to_csv(
    "deseq2_HERV_results_with_warnings.csv",
    index=False
)
