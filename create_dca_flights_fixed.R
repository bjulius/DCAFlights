# DCA Flight Performance Dataset - Fixed Version
# Creates a realistic simulated dataset based on BTS patterns
# Date: 2025-01-27

library(dplyr)
library(tidyr)
library(lubridate)
library(purrr)

set.seed(42)  # For reproducibility

cat("Creating DCA flight performance dataset...\n\n")

# Define realistic parameters based on DCA operations
airlines <- c("AA", "DL", "UA", "WN", "B6", "AS", "NK", "F9")
airline_names <- c("American", "Delta", "United", "Southwest", 
                  "JetBlue", "Alaska", "Spirit", "Frontier")

# Major continental US destinations from DCA (realistic routes)
destinations <- c(
  # Major hubs
  "ATL", "ORD", "DFW", "DEN", "LAX", "PHX", "CLT", "LAS", "MCO", "SEA",
  # Northeast
  "BOS", "LGA", "JFK", "EWR", "PHL", "BDL", "PVD", "BUF", "ROC", "SYR",
  # Southeast  
  "MIA", "FLL", "TPA", "JAX", "RDU", "GSP", "CHS", "SAV", "RSW", "PBI",
  # Midwest
  "DTW", "MSP", "STL", "MCI", "MKE", "CLE", "CMH", "IND", "DSM", "OMA",
  # South/Southwest
  "IAH", "AUS", "SAN", "DAL", "HOU", "SAT", "ELP", "MSY", "BNA", "MEM",
  # West
  "SFO", "PDX", "SLC", "SMF", "SJC", "RNO", "BOI", "GEG", "TUS", "ABQ"
)
# Create date range
start_date <- as.Date("2019-01-01")
end_date <- as.Date("2024-12-31")
all_dates <- seq(start_date, end_date, by = "day")

# Sample 2500 dates
n_flights <- 2500
sample_dates <- sample(all_dates, n_flights, replace = TRUE)

# Build the dataset
dca_flights <- data.frame(
  date = sample_dates,
  flight_id = 1:n_flights
) %>%
  mutate(
    # Extract date components
    year = year(date),
    month = month(date),
    day = day(date),
    day_of_week = wday(date, label = TRUE),
    day_of_week_num = wday(date),
    month_name = month(date, label = TRUE),
    
    # Assign airlines with realistic market share
    carrier = sample(airlines, n(), replace = TRUE, 
                    prob = c(0.30, 0.20, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04)),
    
    # Assign destinations
    dest = sample(destinations, n(), replace = TRUE),
    
    # Generate flight numbers
    flight = paste0(carrier, sample(100:9999, n(), replace = TRUE)),
    
    # Scheduled departure times (realistic distribution)
    sched_dep_hour = sample(c(6:9, 10:14, 15:19, 20:22), n(), replace = TRUE,
                           prob = c(rep(0.08, 4), rep(0.06, 5), rep(0.07, 5), rep(0.03, 3))),
    sched_dep_min = sample(0:59, n(), replace = TRUE),
    sched_dep_time = sched_dep_hour * 100 + sched_dep_min
  )

# Generate delays separately with proper logic
dca_flights <- dca_flights %>%
  mutate(
    # Base delay probability varies by time of day and day of week
    delay_prob = case_when(
      sched_dep_hour >= 15 & sched_dep_hour <= 19 ~ 0.35,
      sched_dep_hour >= 6 & sched_dep_hour <= 9 ~ 0.25,
      day_of_week %in% c("Mon", "Fri") ~ 0.30,
      TRUE ~ 0.20
    ),
    
    # Weather impact (higher in winter/summer months)
    weather_factor = ifelse(month %in% c(12, 1, 2, 6, 7, 8), 1.2, 1.0),
    
    # Adjust delay probability
    final_delay_prob = pmin(delay_prob * weather_factor, 0.45),
    
    # Determine if flight has delay
    has_delay = runif(n()) < final_delay_prob,
    
    # Generate delay magnitudes
    delay_magnitude = runif(n()),
    
    # Calculate departure delays based on conditions
    dep_delay = case_when(
      !has_delay ~ round(rnorm(n(), mean = -2, sd = 3)),
      has_delay & delay_magnitude < 0.6 ~ round(runif(n(), 1, 15)),
      has_delay & delay_magnitude < 0.9 ~ round(runif(n(), 16, 60)),
      has_delay ~ round(runif(n(), 61, 120))
    ),
    
    # Ensure minimum bounds
    dep_delay = pmax(dep_delay, -10),
    
    # Actual departure time
    dep_time = sched_dep_time + (dep_delay %/% 60) * 100 + (dep_delay %% 60),
    
    # Arrival delays correlate with departure delays
    arr_delay = dep_delay + round(rnorm(n(), mean = 0, sd = 5))
  ) %>%
  mutate(
    # Calculate distances (approximate based on destination)
    distance = case_when(
      dest %in% c("LAX", "SFO", "SEA", "PDX", "SAN") ~ round(runif(n(), 2200, 2600)),
      dest %in% c("DEN", "PHX", "LAS", "SLC") ~ round(runif(n(), 1400, 1800)),
      dest %in% c("ORD", "DFW", "IAH", "MSP") ~ round(runif(n(), 900, 1300)),
      dest %in% c("ATL", "CLT", "MCO", "MIA") ~ round(runif(n(), 600, 900)),
      dest %in% c("BOS", "LGA", "JFK") ~ round(runif(n(), 350, 450)),
      TRUE ~ round(runif(n(), 200, 800))
    ),
    
    # Air time (rough approximation)
    air_time = round(distance / 8),
    
    # Scheduled arrival time
    sched_arr_time = sched_dep_time + (air_time %/% 60) * 100 + (air_time %% 60),
    
    # Actual arrival time  
    arr_time = sched_arr_time + (arr_delay %/% 60) * 100 + (arr_delay %% 60),
    
    # Performance metrics
    on_time = ifelse(arr_delay <= 15, 1, 0),
    dep_delay_flag = ifelse(dep_delay > 15, 1, 0),
    arr_delay_flag = ifelse(arr_delay > 15, 1, 0),
    
    # Delay categories
    delay_category = case_when(
      arr_delay <= 0 ~ "Early/On-Time",
      arr_delay > 0 & arr_delay <= 15 ~ "Slightly Late",
      arr_delay > 15 & arr_delay <= 60 ~ "Delayed",
      arr_delay > 60 ~ "Severely Delayed"
    ),
    
    # Time period
    time_period = case_when(
      sched_dep_hour >= 5 & sched_dep_hour < 9 ~ "Early Morning",
      sched_dep_hour >= 9 & sched_dep_hour < 12 ~ "Morning",
      sched_dep_hour >= 12 & sched_dep_hour < 17 ~ "Afternoon",
      sched_dep_hour >= 17 & sched_dep_hour < 21 ~ "Evening",
      TRUE ~ "Night"
    ),
    
    # Add airline names
    airline_name = airline_names[match(carrier, airlines)],
    
    # Add origin
    origin = "DCA",
    
    # Generate tail numbers
    tailnum = paste0("N", sample(10000:99999, n(), replace = TRUE))
  ) %>%
  # Select final columns
  select(
    year, month, month_name, day, date, day_of_week, day_of_week_num,
    carrier, airline_name, flight, tailnum, origin, dest,
    sched_dep_time, dep_time, dep_delay, dep_delay_flag,
    sched_arr_time, arr_time, arr_delay, arr_delay_flag,
    on_time, delay_category, air_time, distance, time_period
  )

# Summary statistics
cat(strrep("=", 50), "\n")
cat("         DCA FLIGHT DATASET SUMMARY\n")
cat(strrep("=", 50), "\n")
cat(paste("✓ Total flights:", nrow(dca_flights), "\n"))
cat(paste("✓ Date range:", min(dca_flights$date), "to", max(dca_flights$date), "\n"))
cat(paste("✓ Unique destinations:", n_distinct(dca_flights$dest), "\n"))
cat(paste("✓ Airlines:", n_distinct(dca_flights$carrier), "\n\n"))

# Performance metrics
cat("ON-TIME PERFORMANCE:\n")
cat(paste("  • On-time rate:", round(mean(dca_flights$on_time) * 100, 1), "%\n"))
cat(paste("  • Avg departure delay:", round(mean(dca_flights$dep_delay), 1), "min\n"))
cat(paste("  • Avg arrival delay:", round(mean(dca_flights$arr_delay), 1), "min\n\n"))
# Distribution by year
cat("FLIGHTS BY YEAR:\n")
year_dist <- table(dca_flights$year)
for(i in 1:length(year_dist)) {
  cat(paste("  •", names(year_dist)[i], ":", year_dist[i], "flights\n"))
}

# Top airlines
cat("\nTOP 5 AIRLINES:\n")
top_airlines <- dca_flights %>%
  count(carrier, airline_name) %>%
  arrange(desc(n)) %>%
  head(5)
for(i in 1:nrow(top_airlines)) {
  cat(paste("  •", top_airlines$airline_name[i], 
            "(", top_airlines$carrier[i], "):",
            top_airlines$n[i], "flights\n"))
}

# Top destinations
cat("\nTOP 10 DESTINATIONS:\n")
top_dest <- dca_flights %>%
  count(dest) %>%
  arrange(desc(n)) %>%
  head(10)
for(i in 1:nrow(top_dest)) {
  cat(paste("  •", top_dest$dest[i], ":", top_dest$n[i], "flights\n"))
}

# Save the dataset
output_file <- "dca_flights_dataset.csv"
write.csv(dca_flights, output_file, row.names = FALSE)
cat(paste("\n✓ Dataset saved as:", output_file, "\n"))

# Also save as RDS
rds_file <- "dca_flights_dataset.rds"
saveRDS(dca_flights, rds_file)
cat(paste("✓ RDS file saved as:", rds_file, "\n"))

cat("\n", strrep("=", 50), "\n")
cat("Dataset ready for on-time performance analysis!\n")
cat(strrep("=", 50), "\n")