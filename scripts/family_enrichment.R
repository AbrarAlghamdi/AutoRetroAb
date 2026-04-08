args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 5) {
  stop("Usage: Rscript family_enrichment.R <de_csv> <metadata_tsv> <out_csv> <alpha> <log2fc>")
}

de_file <- args[1]
meta_file <- args[2]
out_file <- args[3]
alpha <- as.numeric(args[4])
log2fc <- as.numeric(args[5])

de <- read.csv(de_file, stringsAsFactors = FALSE)
meta <- read.delim(meta_file, stringsAsFactors = FALSE)

if (!"locus_id" %in% colnames(de)) {
  stop("DE results must contain locus_id")
}

if ("locus" %in% colnames(meta) && !"locus_id" %in% colnames(meta)) {
  meta$locus_id <- meta$locus
}

required_meta <- c("locus_id", "family")
missing_meta <- setdiff(required_meta, colnames(meta))
if (length(missing_meta) > 0) {
  stop(paste("Metadata must contain", paste(required_meta, collapse = ", ")))
}

sig <- de[!is.na(de$padj) & de$padj < alpha & abs(de$log2FoldChange) >= log2fc, ]

merged <- merge(sig, meta[, c("locus_id", "family")], by = "locus_id")

if (nrow(merged) == 0) {
  write.csv(data.frame(), out_file, row.names = FALSE)
  quit(save = "no")
}

res <- as.data.frame(table(merged$family), stringsAsFactors = FALSE)
colnames(res) <- c("family", "count")
res <- res[order(-res$count), ]

write.csv(res, out_file, row.names = FALSE)
