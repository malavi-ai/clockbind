# Independent check of clockbind's weights plugin using established R packages.
#   PSweight     (Zhou, Tong & Li): multinomial PS + generalized overlap weights, arm means
#   clubSandwich (Pustejovsky):     CR2 cluster-robust covariance
# Usage: Rscript validate_weights.R data.csv treatment "x1,x2" outcome cluster py_weights.csv out.json
suppressPackageStartupMessages({library(PSweight); library(clubSandwich); library(jsonlite)})
a <- commandArgs(trailingOnly = TRUE)
d <- read.csv(a[1], stringsAsFactors = FALSE)
trt <- a[2]; covs <- strsplit(a[3], ",")[[1]]; y <- a[4]; cl <- a[5]
pyw <- read.csv(a[6])
d[[trt]] <- factor(d[[trt]], levels = sort(unique(as.character(d[[trt]]))))
f <- as.formula(paste(trt, "~", paste(covs, collapse = "+")))

ss <- SumStat(ps.formula = f, data = d, weight = "overlap")
ps <- ss$propensity
wcol <- ss$ps.weights[["overlap"]]
fitR <- PSweight(ps.formula = f, yname = y, data = d, weight = "overlap")

d$w_py <- pyw$weight
m <- lm(as.formula(paste(y, "~ 0 +", trt)), data = d, weights = w_py)
V <- as.matrix(vcovCR(m, cluster = d[[cl]], type = "CR2"))

out <- list(
  levels = levels(d[[trt]]),
  psweight_muhat = unname(as.numeric(fitR$muhat)),
  psweight_weights = as.numeric(wcol),
  psweight_ps = unname(as.matrix(ps)),
  club_coef = unname(coef(m)),
  club_vcov_cr2 = unname(V),
  versions = list(R = R.version.string,
                  PSweight = as.character(packageVersion("PSweight")),
                  clubSandwich = as.character(packageVersion("clubSandwich")))
)
write_json(out, a[7], digits = NA, auto_unbox = TRUE)
cat("R validation written to", a[7], "\n")
