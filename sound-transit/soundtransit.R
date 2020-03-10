# Current Pop of ST districts
# Growth in pop over several years
# % of total state pop that ST represents

curr.dir <- getwd()
this.dir <- dirname(rstudioapi::getSourceEditorContext()$path)
setwd(this.dir)
source("soundtransit-settings.R")

# ST district -------------------------------------------------------------

# filter
stdf <- ofm %>% 
  semi_join(blocks, by = c("GEOID10"))

# edit
st.juris <- stdf %>%
  select(COUNTYFP10, Juris2019) %>%
  distinct() %>%
  arrange(COUNTYFP10, Juris2019)

stdf.pop <- stdf %>%
  select_(.dots = yrs.cols)

sum.st.pop <- stdf.pop %>%
  summarise_all(funs(sum)) %>%
  mutate(Jurisdiction = "Sound Transit District") %>%
  select(Jurisdiction, everything())


# State -------------------------------------------------------------------

state.ofm.raw <- read.xlsx("ofm_april1_population_final.xlsx", sheet = "Population", start = 5, colNames = TRUE)

state.ofm <- state.ofm.raw %>%
  filter(County != '.') %>%
  mutate_at(vars(contains("Population")), funs(as.numeric)) %>%
  rename_at(vars(contains("Population")), funs(paste0("POP", years)))

sum.state.pop <- state.ofm %>%
  filter(Filter == 100) %>%
  select(-Line:-County)
  
  
# bind with st district
combine.df <- sum.st.pop %>%
  bind_rows(sum.state.pop) 

tidy.combine.df <- combine.df %>% 
  gather(attribute, estimate, -Jurisdiction) %>%
  arrange(Jurisdiction, attribute) %>%
  group_by(Jurisdiction) %>%
  mutate(delta = c(NA, diff(estimate)))
  
tidy.st.df1 <- tidy.combine.df %>%
  select(everything(), -delta) %>%
  spread(attribute, estimate) %>%
  mutate(type = "estimate")

tidy.st.df2 <- tidy.combine.df %>%
  select(everything(), -estimate) %>%
  spread(attribute, delta) %>%
  mutate(type = "delta")

combine.tidy.st.df <- tidy.st.df1 %>%
  bind_rows(tidy.st.df2) %>%
  select(Jurisdiction, type, everything())

# calc shares
setDT(combine.tidy.st.df)
dtm <- melt.data.table(combine.tidy.st.df, id.vars = c("Jurisdiction", "type"), measure.vars = yrs.cols, variable.name = "year")
dtc <- dcast.data.table(dtm, type + year ~ Jurisdiction, value.var = "value")
dtc[, share_of_state := `Sound Transit District`/`State Total`]

melt.cols <- colnames(dtc)[3:5]
dtm2 <- melt.data.table(dtc, id.vars = c("type", "year"), measure.vars = melt.cols, variable.name = "Jurisdiction")
dtc2 <- dcast.data.table(dtm2, Jurisdiction + type ~ year, value.var = "value")
tt <- dtc2[order(-type)]

write.xlsx(tt, "sound_transit_stats.xlsx")


  
