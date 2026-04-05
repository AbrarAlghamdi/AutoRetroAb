args <- commandArgs(trailingOnly = TRUE)
out_txt <- args[1]

lines <- c(
  "TE RNA-seq Summary Report",
  "=========================",
  "",
  "Files:",
  "",
  "Differential Expression:",
  "  ../de/herv_deseq2_results.csv",
  "  ../de/l1_deseq2_results.csv",
  "",
  "Top Hits:",
  "  ../de/top10_herv_up.csv",
  "  ../de/top10_herv_down.csv",
  "  ../de/top10_l1_up.csv",
  "  ../de/top10_l1_down.csv",
  "",
  "Family Enrichment:",
  "  ../enrichment/herv_family_enrichment.csv",
  "  ../enrichment/l1_family_enrichment.csv",
  "",
  "Chromosomal Distribution:",
  "  ../chromosomal/herv_chromosomal_distribution.csv",
  "  ../chromosomal/l1_chromosomal_distribution.csv",
  "",
  "Plots:",
  "  ../plots/herv_volcano.png",
  "  ../plots/l1_volcano.png",
  ""
)

writeLines(lines, out_txt)
cat("Report created at:", out_txt, "\n")
