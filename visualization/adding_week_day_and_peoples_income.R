library(dplyr)
library(lubridate)

data <- read.csv("people_paths_data/data/output.csv")

# Adding trip week day and weekend label
data <- data %>% 
  mutate(
    day.of.week = wday(ymd_hms(o.timestamp)),
    is.weekend = ifelse(day.of.week == 1 | day.of.week == 7, TRUE, FALSE)
  )

# Checking user social income

basic.salary <- 937

data <- data %>%
  mutate(
    low.income = o.income < 3 * basic.salary
  )

# Summarising data 
low.income.weekend.edges <- data %>%
  filter(low.income, is.weekend) %>%
  group_by(o.neigh.name, d.neigh.name) %>%
  summarise(
    origin.income = median(o.income),
    num.trips = n()
  )
low.income.weekend.nodes <- data.frame("nodes" = union(low.income.weekend.edges$o.neigh.name, low.income.weekend.edges$d.neigh.name))
write.csv(low.income.weekend.nodes, "low_income_weekend_nodes.csv", row.names = FALSE)
write.csv(low.income.weekend.edges, "low_income_weekend_edges.csv", row.names = FALSE)

low.income.not.weekend.edges <- data %>%
  filter(low.income, !is.weekend) %>%
  group_by(o.neigh.name, d.neigh.name) %>%
  summarise(
    origin.income = median(o.income),
    num.trips = n()
  )
low.income.not.weekend.nodes <- data.frame("nodes" = union(low.income.not.weekend.edges$o.neigh.name, low.income.not.weekend.edges$d.neigh.name))
write.csv(low.income.not.weekend.nodes, "low_income_not_weekend_nodes.csv", row.names = FALSE)
write.csv(low.income.not.weekend.edges, "low_income_not_weekend_edges.csv", row.names = FALSE)

high.income.weekend.edges <- data %>%
  filter(!low.income, is.weekend) %>%
  group_by(o.neigh.name, d.neigh.name) %>%
  summarise(
    origin.income = median(o.income),
    num.trips = n()
  )
high.income.weekend.nodes <- data.frame("nodes" = union(high.income.weekend.edges$o.neigh.name, high.income.weekend.edges$d.neigh.name))
write.csv(high.income.weekend.nodes, "high_income_weekend_nodes.csv", row.names = FALSE)
write.csv(high.income.weekend.edges, "high_income_weekend_edges.csv", row.names = FALSE)

high.income.not.weekend.edges <- data %>%
  filter(!low.income, !is.weekend) %>%
  group_by(o.neigh.name, d.neigh.name) %>%
  summarise(
    origin.income = median(o.income),
    num.trips = n()
  )
high.income.not.weekend.nodes <- data.frame("nodes" = union(high.income.not.weekend.edges$o.neigh.name, high.income.not.weekend.edges$d.neigh.name))
write.csv(high.income.not.weekend.nodes, "high_income_not_weekend_nodes.csv", row.names = FALSE)
write.csv(high.income.not.weekend.edges, "high_income_not_weekend_edges.csv", row.names = FALSE)
