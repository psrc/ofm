source(here::here("parcelizer-prep/00-global-vars.R"))

read.published.ofm.data <- function() {
  pub.dir <- file.path(base.dir, dir, "quality_check/published")
  counties <- c("King", "Kitsap", "Pierce", "Snohomish")
  filter <- 1
  
  hu <- read.xlsx(file.path(pub.dir, "ofm_april1_housing.xlsx"), sheet = "Housing Units", startRow = 4) %>% as.data.table
  hudt <- hu[County %in% counties & Filter %in% filter, ]
  hucols <- grep("Total\\.Housing\\.Units.*$", colnames(hudt), value = T)
  all.hucols <- c("County", hucols)
  h <- hudt[, all.hucols, with = F]
  hmelt <- melt.data.table(h, id.vars = "County", measure.vars = hucols, variable.name = "variable", value.name = "HU")
  hmelt[, variable := as.character(variable)][, year := str_extract(variable, "[[:digit:]]+")][, variable := NULL]
  
  pop <- read.xlsx(file.path(pub.dir, "ofm_april1_population_final.xlsx"), sheet = "Population", startRow = 5) %>% as.data.table
  pdt <- pop[County %in% counties & Filter %in% filter, ]
  pcols <- grep("^\\d+", colnames(pdt), value = T)
  all.pcols <- c("County", pcols)
  p <- pdt[, all.pcols, with = F]
  pmelt <- melt.data.table(p, id.vars = "County", measure.vars = pcols, variable.name = "variable", value.name = "POP")
  pmelt[, variable := as.character(variable)][, year := str_extract(variable, "[[:digit:]]+")][, variable := NULL]
  
  pmelt[hmelt, on = c("County", "year"), HU := i.HU]
  setnames(pmelt, c("POP", "HU"), c("POP_pub", "HU_pub"))
  new.cols <- c("POP_pub", "HU_pub")
  dt <- pmelt[, (new.cols) := lapply(.SD, as.numeric), .SDcols = new.cols]
  return(dt)
}

qc.rds <- function(years) {
  
  ofm <- readRDS(file.path(base.dir, dir, "ofm_saep.rds")) %>% as.data.table()
  attributes <- c("POP", "HHP","GQ", "HU", "OHU")
  cols <- apply(expand.grid(attributes, years), 1, function(x) paste0(x[1], x[2]))
  allcols <- c("COUNTYFP", cols)
  odt <- ofm[, allcols, with = F]
  
  dt <- melt.data.table(odt, id.vars = "COUNTYFP", measure.vars = cols, variable.name = "variable", value.name = "estimate")
  dt[, `:=` (attribute = str_extract(variable, "[[:alpha:]]+"), YEAR = str_extract(variable, "[[:digit:]]+"))]
  dtsum <- dt[, lapply(.SD, sum), .SDcols = "estimate", by = .(COUNTY = COUNTYFP, attribute, YEAR)]
  dtcast <- dcast.data.table(dtsum, COUNTY + YEAR ~ attribute, value.var = "estimate")
  setcolorder(dtcast, c("COUNTY", "YEAR", attributes))
  d <- dtcast[order(YEAR, COUNTY)][, COUNTYNAME := switch(COUNTY, "33" = "King", "35" = "Kitsap", "53" = "Pierce", "61" = "Snohomish"), by = COUNTY]
  
  pdata <- read.published.ofm.data()
  p <- pdata[year %in% years, ]
  d[p, on = c("COUNTYNAME" = "County", "YEAR" = "year"), `:=`(POP_pub = i.POP_pub, HU_pub = i.HU_pub)]
  d[, `:=`(POP_diff = (POP - POP_pub), HU_diff = (HU - HU_pub))]
  setcolorder(d, c("COUNTY", "COUNTYNAME", "YEAR", attributes, "POP_pub", "HU_pub", "POP_diff", "HU_diff"))
  rm(ofm)
  return(d)
}


# QC ----

# df <- readRDS(file.path(base.dir, dir, "ofm_saep.rds"))
df_saep_apr <- qc.rds(years)


# write.xlsx(dt, file.path(base.dir, dir, "quality_check", paste0("ofm_saep_qc_", Sys.Date(), ".xlsx")))