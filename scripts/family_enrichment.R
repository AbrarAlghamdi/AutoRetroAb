args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 5) {
  stop("Usage: Rscript family_enrichment.R <de_csv> <metadata_tsv> <out_csv> <alpha> <log2fc>")
}

de_file <- args[1]
meta_file <- args[2]
out_file <- args[3]
alpha <- as.numeric(args[4])
log2fc <- as.numeric(args[5])

# Load data
de <- read.csv(de_file, stringsAsFactors = FALSE)
meta <- read.delim(meta_file, stringsAsFactors = FALSE)

# Fix column names if needed
if ("locus" %in% colnames(meta) && !"locus_id" %in% colnames(meta)) {
  meta$locus_id <- meta$locus
}

# Check required columns
if (!all(c("locus_id", "family") %in% colnames(meta))) {
  stop("Metadata must contain locus_id and family")
}

if (!"locus_id" %in% colnames(de)) {
  stop("DE results must contain locus_id")
}

# Merge all loci (not only significant!)
merged_all <- merge(de, meta[, c("locus_id", "family")], by = "locus_id")

# Define significant
merged_all$significant_flag <- ifelse(
  !is.na(merged_all$padj) &
  merged_all$padj < alpha &
  abs(merged_all$log2FoldChange) >= log2fc,
  "yes", "no"
)

families <- unique(merged_all$family)

results <- data.frame()

for (fam in families) {
  
  in_family <- merged_all$family == fam
  
  a <- sum(merged_all$significant_flag == "yes" & in_family)
  b <- sum(merged_all$significant_flag == "yes" & !in_family)
  c <- sum(merged_all$significant_flag == "no" & in_family)
  d <- sum(merged_all$significant_flag == "no" & !in_family)
  
  mat <- matrix(c(a, b, c, d), nrow = 2)
  
  ft <- fisher.test(mat)
  
  results <- rbind(results, data.frame(
    family = fam,
    significant_in_family = a,
    significant_outside = b,
    non_significant_in_family = c,
    non_significant_outside = d,
    odds_ratio = ft$estimate,
    pvalue = ft$p.value
  ))
}

# Adjust p-values
results$padj <- p.adjust(results$pvalue, method = "BH")

# Sort by significance
results <- results[order(results$padj), ]

# Save
out_dir <- dirname(out_file)
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE)
}

write.csv(results, out_file, row.names = FALSE)
