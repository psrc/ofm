# This script compiles OFM 201X population by age projections and computes an estimate of the 
# 15-17 age cohort based on the share of persons age 15-17 in X

library(openxlsx)
library(dplyr)
library(data.table)

# function to assemble OFM tables for each geography
assemble.juris.table <- function(jurisdiction, start.row){
  master.file <- file.path(indir2, ofm.file)
  section1 <- read.xlsx(master.file, sheet = 1, startRow = as.integer(start.row), colNames = TRUE, rowNames = FALSE, rows = c(as.integer(start.row):as.integer(start.row + 20)), cols = NULL)
  section2 <- read.xlsx(master.file, sheet = 1, startRow = as.integer(start.row + 22), colNames = TRUE, rowNames = FALSE, rows = c(as.integer(start.row + 22): as.integer(start.row + 42)), cols = NULL)
  section3 <- read.xlsx(master.file, sheet = 1, startRow = as.integer(start.row + 44), colNames = TRUE, rowNames = FALSE, rows = c(as.integer(start.row + 44): as.integer(start.row + 64)), cols = c(1:2))
  table <- bind_cols(section1, section2, section3)
  colnames(table)[1] <- "agegroups"
  select.cols <- (colnames(table)[grepl(paste0("groups|\\d+{4}"), names(table))])
  table <- table[,colnames(table) %in% select.cols]
  colnames(table)[2:ncol(table)] <- paste0("tot", select.cols[2:length(select.cols)])
  table <- table[-c(1), ]
  table$jurisdiction <- jurisdiction
  table %>% mutate_each(funs(as.numeric), starts_with("tot"))
} 

# function to append worksheet
append.worksheet <- function(table, workbook, sheetName){
  addWorksheet(workbook, sheetName)
  writeData(workbook, sheet = sheetName, x = table, colNames = TRUE)
  saveWorkbook(workbook, file.path(indir, my.filename), overwrite = TRUE )
}

indir <- "J:/Staff/Christy/OFM/forecasts/requests/jean"
indir2 <- "J:/Staff/Christy/OFM/forecasts"
my.filename <- "pop_projections_rev_2017_09_07_3.xlsx"

ofm.state.proj <- "stfc_2016.xlsx"
ofm.file <- "gma2012_cntyage_med.xlsx"

#read state forecast
osp <- read.xlsx(file.path(indir2, ofm.state.proj), sheet = 'Single_Year', startRow = 9, colNames = TRUE)
forecast.years <- c(2010, 2015, 2025, 2040)
yr.cols <- paste0("Total.", forecast.years)
yr.colnames <- paste0("tot", forecast.years)
age <- c(seq(15,19))

# filter state forecast
osp.select <- osp %>% 
  filter(Age %in% age) %>% 
  select(Age, one_of(yr.cols)) %>% as.data.table()

setnames(osp.select, yr.cols, paste0("tot", forecast.years))
osp.dt <- dcast.data.table(melt(osp.select, id.vars = 'Age'), variable ~ Age)
setnames(osp.dt, colnames(osp.dt), c("year", paste0("pop_", 15:19)))
osp.dt1 <- osp.dt[, pop_15_19 := rowSums(.SD), .SDcols = 2:6
                  ][, pop_15_17 := rowSums(.SD), .SDcols = 2:4
                    ][, pop_18_19:= rowSums(.SD), .SDcols = 5:6
                      ][, share_pop15_17 := pop_15_17/pop_15_19
                      ][, share_pop18_19 := pop_18_19/pop_15_19
                        ]

# assemble regional GMA county forecasts
king <- assemble.juris.table("King County", 1176)
kitsap <- assemble.juris.table("Kitsap County", 1245)
pierce <- assemble.juris.table("Pierce County", 1866)
snohomish <- assemble.juris.table("Snohomish County", 2142)
region <- bind_rows(king, kitsap, pierce, snohomish)

# isolate only 15-19 cohort
region.youth <- as.data.table(region)
ry.m <- melt(region.youth, id.vars = c("agegroups", "jurisdiction"), measure.vars = c("tot2010", "tot2015", "tot2020",  "tot2025", "tot2030", "tot2035","tot2040"))
ry.m.select <- ry.m[agegroups == "15-19" & variable %in% paste0("tot", forecast.years),]

# 'join' on years and apply shares creating two new fields in ry.m.select 
setkey(ry.m.select, variable)[osp.dt1, `:=` (pop15_17 = round(value*share_pop15_17, 0), pop18_19 = round(value*share_pop18_19, 0))]
youth <- ry.m.select[,.(agegroups = "15-17", jurisdiction, variable, value = pop15_17),]
post.youth <- ry.m.select[, .(agegroups = "18-19", jurisdiction, variable, value = pop18_19),]

dts <- list(ry.m, youth, post.youth)
region.pop.dt <- rbindlist(dts, use.names = TRUE, fill = TRUE)
format.region.pop.dt <- dcast.data.table(region.pop.dt, agegroups + jurisdiction ~ variable)

youth.age <- c('5-9', '10-14', '15-17')
post.youth.age <- c('18-19', '20-24','25-29', '30-34', '35-39', '40-44','45-49', '50-54','55-59','60-64')
seniors <- c('65-69', '70-74', '75-79', '80-84')

# create new column, populate with new cohort labels
format.region.pop.dt2 <- format.region.pop.dt[agegroups == '0-4', category := "0-4",
                                               ][agegroups %in% youth.age, category := "5-17",
                                                 ][agegroups %in% post.youth.age, category := "18-64",
                                                   ][agegroups %in% seniors, category := "65-84",
                                                     ][agegroups == '85+', category := "85+",]

# filter where category is not na and only forecast years
dt0 <- format.region.pop.dt2[!is.na(category), .(category, jurisdiction, tot2010, tot2015, tot2025, tot2040)]
# dt0 <- format.region.pop.dt2[!is.na(category), .(category, jurisdiction, get(eval(yr.colnames)))]

# aggregate by county & category
cnty.dt <- dt0[, lapply(.SD, sum), by = list(category, jurisdiction), .SDcols = c(paste0("tot", forecast.years))]

# aggregate by category (region)
region.dt <- dt0[, lapply(.SD, sum), by = category, .SDcols = c(paste0("tot", forecast.years))][, jurisdiction := 'Central Puget Sound Region']

# bind cnty.dt and region.dt
alldt <- rbindlist(list(cnty.dt, region.dt), use.names = TRUE, fill = TRUE)

# write cnty.dt to workbook
wb <- createWorkbook(file.path(indir, my.filename))
modifyBaseFont(wb, fontSize = 10, fontColour = "black", fontName = "Segoe UI")
addWorksheet(wb, "County Region All Cohorts")
writeData(wb, sheet = "County Region All Cohorts", x = alldt, colNames = TRUE)
print("exported County/Region All cohorts")

# # append region.dt to workbook
# append.worksheet(region.dt, wb, "Region All Cohorts")
# print("exported Region All cohorts")

# append raw region to workbook
append.worksheet(region, wb, "OFM 2012 proj for CPS")
print("exported regional OFM projections")

# append censusdt.select to workbook
append.worksheet(osp.dt1, wb, "OFM 2016 State proj")
print("exported OFM State projections for youth")
