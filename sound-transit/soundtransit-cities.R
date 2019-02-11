# Top 10 cities with largest absolute & % growth

curr.dir <- getwd()
this.dir <- dirname(rstudioapi::getSourceEditorContext()$path)
setwd(this.dir)
source("soundtransit-settings.R")

juris.col <- paste0("Juris", max(years))
cols <- c("COUNTYFP10", juris.col)
juris.part.cols <- c("Auburn", "Bothell", "Enumclaw", "Milton", "Pacific")

# find ST cities (based on block assignments)
setDT(blocks)
blocks[, GEOID10 := as.character(GEOID10)]
stdf <- unique(ofm[GEOID10 %in% blocks$GEOID10, ..cols])
# clean
stdf[, county_name := switch(COUNTYFP10, "033" = "King", "035" = "Kitsap", "053" = "Pierce", "061" = "Snohomish"), by = COUNTYFP10
     ][, (juris.col) := str_to_title(get(eval(juris.col)))]
stdf[get(eval(juris.col)) %in% juris.part.cols, (juris.col) := paste(get(eval(juris.col)), "(part)")]
stdf[get(eval(juris.col)) == "Seatac", (juris.col) := "SeaTac"]
stdf[get(eval(juris.col)) == "Dupont", (juris.col) := "DuPont"]
stdf[get(eval(juris.col)) %like% "Unincorporated", (juris.col) := paste(get(eval(juris.col)), "County")]
setnames(stdf, juris.col, "juris")

# read in april 1 pop ests
pofm <- read.xlsx("ofm_april1_population_final.xlsx", sheet = "Population", start = 5, colNames = TRUE)
setDT(pofm)
pop.cols <- colnames(pofm)[str_which(colnames(pofm), "Population")]
pofm <- pofm[Filter != ".",][, lapply(.SD, as.numeric), .SDcols = pop.cols, by = .(Filter, County, Jurisdiction)]
podt <- pofm[stdf, on = c("County" = "county_name", "Jurisdiction" = "juris")]
setnames(podt, pop.cols, yrs.cols)

# aggregate parts
ptdt <- podt[Jurisdiction %like% "(part)"
             ][, lapply(.SD, sum), .SDcols = yrs.cols, by = .(Filter, Jurisdiction)
               ][, Jurisdiction := str_replace(Jurisdiction, "\\(part\\)", "(all)")]

odt <- rbindlist(list(podt, ptdt), use.names = T, fill = T)

# calculate
cols1 <- rep(max(yrs.cols), 2)
cols2 <- c(yrs.cols[length(yrs.cols)-1],min(yrs.cols))
delta.cols <- paste0("delta_", cols1, "-", cols2)
share.cols <- paste0("share_", delta.cols)
odt[, (delta.cols) := mapply(function(x, y) .SD[[x]]-.SD[[y]], cols1, cols2, SIMPLIFY = F)]
odt[, (share.cols) := mapply(function(x, y) .SD[[x]]/.SD[[y]], delta.cols, cols2, SIMPLIFY = F)]
dt <- odt[!(Jurisdiction %like% "Uninc") & !(Jurisdiction %like% "part")]

# top 10 lists
sort.cols <- c(delta.cols, share.cols)
sel.cols1 <- c(cols2[1], cols1[1])
sel.cols2 <- c(cols2[2], cols1[2])
all.sel.cols <- rep(list(sel.cols1, sel.cols2), 2)
calc.cols1 <- c(delta.cols[1], share.cols[1])
calc.cols2 <- c(delta.cols[2], share.cols[2])
all.calc.cols <- rep(list(calc.cols1, calc.cols2), 2)

dts <- NULL
for (i in 1:length(sort.cols)) {
  t <- dt[order(-get(eval(sort.cols[i])))][1:10,]
  tcols <- c("Jurisdiction", "County", all.sel.cols[[i]], all.calc.cols[[i]])
  tt <- t[, ..tcols]
  setnames(tt, "Jurisdiction", "Municipality")
  dts[[i]] <- tt
}

write.xlsx(dts, "sound_transit_top10lists.xlsx")


