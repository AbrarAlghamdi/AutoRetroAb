args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 5) {
  stop("Usage: Rscript extract_top_hits.R <de_csv> <alpha> <log2fc> <out_up> <out_down>")
}

de_file <- args[1]
alpha <- as.numeric(args[2])
log2fc <- as.numeric(args[3])
out_up <- args[4]
out_down <- args[5]

df <- read.csv(de_file, stringsAsFactors = FALSE)

required <- c("locus_id", "log2FoldChange", "padj")
missing <- setdiff(required, colnames(df))
if (length(missing) > 0) {
  stop(paste("Missing required columns:", paste(missing, collapse = ", ")))
}

sig <- df[!is.na(df$padj) & df$padj < alpha & abs(df$log2FoldChange) >= log2fc, ]

up <- sig[sig$log2FoldChange > 0, ]
down <- sig[sig$log2FoldChange < 0, ]

up <- up[order(-up$log2FoldChange), ]
down <- down[order(down$log2FoldChange), ]

write.csv(head(up, 10), out_up, row.names = FALSE)
write.csv(head(down, 10), out_down, row.names = FALSE)
