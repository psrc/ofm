library(odbc)
library(DBI)
library(data.table)
library(stringr)

estimate.year <- '2019'
out.dir <- "T:/2021March/Stefan"

# SQL connection ----------------------------------------------------------

# latest & greatest vintage is publication_dim_id 3

query <- paste(
"SELECT a.publication_dim_id, c.publication_name, a.geography_dim_id, b.block_geoid, a.estimate_year, 
a.housing_units, a.occupied_housing_units, a.group_quarters_population, a.household_population
FROM ofm.estimate_facts AS a 
    LEFT JOIN census.geography_dim AS b ON a.geography_dim_id = b.geography_dim_id
    JOIN ofm.publication_dim AS c ON a.publication_dim_id = c.publication_dim_id
WHERE a.estimate_year =", estimate.year, "AND a.publication_dim_id = 3;"
)

elmer_connection <- dbConnect(odbc(),
                              driver = "SQL Server",
                              server = "AWS-PROD-SQL\\Sockeye",
                              database = "Elmer",
                              trusted_connection = "yes"
                              ) 

# read in a queried table
df <- dbGetQuery(elmer_connection, SQL(query))

dbDisconnect(elmer_connection)


# Wrangle -----------------------------------------------------------------


setDT(df)

sum.cols <- str_subset(colnames(df), "_(pop|uni).*$") 

# query and sum for block groups
new.df <- df[, lapply(.SD, sum), .SDcols = sum.cols, by = .(publication_name, estimate_year, block_group_geoid = str_extract(block_geoid, "^\\d{12}"))]

fwrite(new.df, file.path(out.dir, paste0("ofm_saep_", estimate.year, "_vintage_2020.csv")))
