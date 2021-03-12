# This script compiles OFM GMA 201X population by age projections and computes an estimate of the 
# 15-17 age cohort based on the share of persons age 15-17 and 18-19 in X from the OFM State Projections

library(openxlsx)
library(data.table)
library(here)
library(stringr)


# functions ---------------------------------------------------------------


append.worksheet <- function(table, workbook, sheetName){
  # function to append worksheet
  addWorksheet(workbook, sheetName)
  writeData(workbook, sheet = sheetName, x = table, colNames = TRUE)
  saveWorkbook(workbook, here('youth-pop-cmp', 'results', out.filename), overwrite = TRUE )
}


# input -------------------------------------------------------------------


data.dir <- here('youth-pop-cmp', 'data')
out.filename <- paste0("pop_projections_", Sys.Date(),".xlsx")

ofm.state.proj <- "stfc_population_by_age_and_sex.xlsx"
ofm.file <- "gma_2017_age_sex_med_2050.xlsx"

gma.years <- seq(2010, 2050, by = 5)
state.years <- c(seq(2010, 2035, by = 5), rep(2040, 3))

look.up <- data.table(gma = paste0("Total_", gma.years), 
                      state = paste0("Total_", state.years))

# unique id for each unique year
look.up[, id := .GRP, by = state]


# state forecast ----------------------------------------------------------


## clean state forecast ----
osp <- read.xlsx(file.path(data.dir, ofm.state.proj), sheet = 'Single Year', startRow = 9)
setDT(osp)

state.yr.cols <- paste0("Total.", state.years)
state.cols <- c("Age", state.yr.cols)
state.age <- seq(15,19)

## filter state forecast ----

osp <- osp[Age %in% state.age, ..state.cols]
colnames(osp) <- str_replace_all(colnames(osp), "\\.", "_")

# inspect colnames, remove duplicate column
osp <- osp[, .SD, .SDcols = unique(names(osp))]

osp.dt <- dcast(melt(osp, id.vars = 'Age'), variable ~ Age)
setnames(osp.dt, colnames(osp.dt), c("year", paste0("pop_", 15:19)))
osp.dt1 <- osp.dt[, pop_15_19 := rowSums(.SD), .SDcols = 2:6
                  ][, pop_15_17 := rowSums(.SD), .SDcols = 2:4
                    ][, pop_18_19:= rowSums(.SD), .SDcols = 5:6
                      ][, share_pop15_17 := pop_15_17/pop_15_19
                      ][, share_pop18_19 := pop_18_19/pop_15_19
                        ]


# GMA county forecast ----------------------------------------------------

## clean county forecast ----

gma <- read.xlsx(here(data.dir, ofm.file), startRow = 4, colNames = FALSE, fillMergedCells = TRUE)
setDT(gma)
keep.cols <- colnames(gma)[which(!is.na(gma[2, ]))]

gma <- gma[, ..keep.cols]

# create new column headers
r1 <- as.character(gma[1, 3:ncol(gma)])
r2 <- as.character(gma[2, 3:ncol(gma)])
new.gma.cols <- c("County", "Age", paste(r2, r1, sep = "_"))

setnames(gma, colnames(gma), new.gma.cols)

## filter county forecast ----

region <- gma[County %in% c("King", "Kitsap", "Pierce", "Snohomish")]
region <- region[, lapply(.SD, as.numeric), .SDcols = str_subset(colnames(region), "\\d+$"), by = c("Age", "County")]

# isolate only 15-19 cohort
ry.m <- melt(region, id.vars = c("Age", "County"), measure.vars = str_subset(colnames(region), "^Total"))
ry.m.select <- ry.m[Age == "15-19" & variable %in% paste("Total", gma.years, sep = "_"),]

## join ----

# apply id to both gma and state youth tables
ry.m.select <- ry.m.select[look.up[, .(gma, id)], on = c("variable" = "gma")]
osp.dt1 <- osp.dt1[look.up[, .(state, id)], on = c("year" = "state")]

# 'join' on years and apply shares creating two new fields in ry.m.select 
setkey(ry.m.select, id)
setkey(osp.dt1, id)
ry.m.select[osp.dt1, ':=' (pop15_17 = round(value*share_pop15_17, 0), pop18_19 = round(value*share_pop18_19, 0))]

youth <- ry.m.select[,.(Age = "15-17", County, variable, value = pop15_17),]
post.youth <- ry.m.select[, .(Age = "18-19", County, variable, value = pop18_19),]


# prep final table --------------------------------------------------------


dts <- list(ry.m[variable %in% as.character(look.up$gma)], youth, post.youth)
region.pop.dt <- rbindlist(dts, use.names = TRUE, fill = TRUE)
format.region.pop.dt <- dcast(region.pop.dt, Age + County ~ variable)

youth.age <- c('5-9', '10-14', '15-17')
post.youth.age <- c('18-19', '20-24','25-29', '30-34', '35-39', '40-44','45-49', '50-54','55-59','60-64')
seniors <- c('65-69', '70-74', '75-79', '80-84')
age.factor <- c('0-4', youth.age, post.youth.age, seniors, '85+')
category.factor <- c('0-4', '5-17', '18-64', '65-84', '85+')

# create new column, populate with new cohort labels
format.region.pop.dt2 <- format.region.pop.dt[, category := fcase(Age == '0-4', "0-4",
                                                                  Age %in% youth.age, "5-17",
                                                                  Age %in% post.youth.age, "18-64",
                                                                  Age %in% seniors, "65-84",
                                                                  Age == '85+', "85+")]
## QC ----

format.region.pop.dt2[!is.na(category), 
                      lapply(.SD, sum), 
                      .SDcols = str_subset(colnames(format.region.pop.dt2), "^Total"), 
                      by = County]

## munge tables ----

# filter where category is not NA
dt0 <- format.region.pop.dt2[!is.na(category), 
                             ][, category := factor(category, levels = category.factor, labels = category.factor)]

# aggregate by county & category
cnty.dt <- dt0[, lapply(.SD, sum), by = .(category, County), .SDcols = str_subset(colnames(dt0), "^Total")]

# aggregate by category (region)
region.dt <- dt0[, lapply(.SD, sum), by = category, .SDcols = str_subset(colnames(dt0), "^Total")
                 ][, County := 'Central Puget Sound Region']

# bind cnty.dt and region.dt
alldt <- rbindlist(list(cnty.dt, region.dt), use.names = TRUE, fill = TRUE)

# write cnty.dt to workbook
wb <- createWorkbook(here('youth-pop-cmp', out.filename))
modifyBaseFont(wb, fontSize = 10, fontColour = "black", fontName = "Segoe UI")
addWorksheet(wb, "County Region All Cohorts")
writeData(wb, sheet = "County Region All Cohorts", x = alldt, colNames = TRUE)
print("exported County/Region All cohorts")

# append GMA forecast to workbook
append.worksheet(region, wb, "source OFM 2017 proj for CPS")
print("exported regional OFM projections")

# append State forecast for Youth to workbook
append.worksheet(osp.dt, wb, "source OFM 2020 State proj")
print("exported OFM State projections for youth")
