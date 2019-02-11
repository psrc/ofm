# Fastest growing counties in the state (top 10)

curr.dir <- getwd()
this.dir <- dirname(rstudioapi::getSourceEditorContext()$path)
setwd(this.dir)
source("soundtransit-settings.R")

pofm <- read.xlsx("ofm_april1_population_final.xlsx", sheet = "Population", start = 5, colNames = TRUE)
setDT(pofm)
pop.cols <- colnames(pofm)[str_which(colnames(pofm), "Population")]
pofm <- pofm[Filter == 1,][, lapply(.SD, as.numeric), .SDcols = pop.cols, by = .(Filter, County, Jurisdiction)]
setnames(pofm, pop.cols, yrs.cols)

cols1 <- max(yrs.cols)
cols2 <- yrs.cols[length(yrs.cols)-1]
delta.cols <- paste0("delta_", cols1, "-", cols2)
share.cols <- paste0("share_", delta.cols)
pofm[, (delta.cols) := mapply(function(x, y) .SD[[x]]-.SD[[y]], cols1, cols2, SIMPLIFY = F)]
pofm[, (share.cols) := mapply(function(x, y) .SD[[x]]/.SD[[y]], delta.cols, cols2, SIMPLIFY = F) ]
t <- pofm[order(-get(eval(share.cols[1])))][1:10,]
sel.cols <- c("Jurisdiction", "County", cols2, cols1, delta.cols, share.cols)
tt <- t[, ..sel.cols]

write.xlsx(tt, "sound_transit_top10cnty.xlsx")
