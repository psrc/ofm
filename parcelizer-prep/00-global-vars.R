library(foreign)
library(data.table)
library(openxlsx)
library(tidyverse)

base.dir <- "J:/OtherData/OFM/SAEP"
dir <- "SAEP Extract_2025-11-07"
data.dir <- file.path(dir, "original")
filename <- "block20.csv"

id.cols <- c("STATEFP", "COUNTYFP", "TRACTCE", "BLOCKCE", "GEOID20")
id_vars <- paste(c(id.cols, "VERSION"), collapse = " + ")
counties <- c("33", "35", "53", "61")
years <- c(as.character(2020:2025))
version <- 'November 7, 2025' # taken from OFM block metadata