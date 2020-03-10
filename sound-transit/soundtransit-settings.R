library(tidyverse)
library(foreign)
library(openxlsx)
library(data.table)

dirname <- "SAEP Extract_2019-10-15"
dir <- file.path("J:/OtherData/OFM/SAEP/", dirname, "/requests/soundtransit")
setwd(dir)

blocks <- read.dbf("blk10ST.dbf")
ofm <- read_rds("../../ofm_saep.rds")

years <- 2010:2019
yrs.cols <- paste0("POP", years) 
