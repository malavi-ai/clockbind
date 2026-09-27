# Reference values from established R packages for ClockBind's validation suite.
# Usage: Rscript reference_all.R validation_data.csv conjoint.csv out.json
suppressMessages({library(jsonlite); library(psych); library(lavaan); library(irr); library(irrCAC); library(nnet); library(MASS); library(sandwich); library(clubSandwich); library(pwr)})
a <- commandArgs(TRUE); d <- read.csv(a[1]); cj <- read.csv(a[2]); R <- list()
ver <- function(p) as.character(packageVersion(p))
R$versions <- list(R = paste(R.version$major, R.version$minor, sep = "."), psych = ver("psych"), lavaan = ver("lavaan"), irr = ver("irr"), irrCAC = ver("irrCAC"),
                   nnet = ver("nnet"), MASS = ver("MASS"), sandwich = ver("sandwich"), clubSandwich = ver("clubSandwich"), pwr = ver("pwr"))
d$g2 <- factor(d$g2); d$g3 <- factor(d$g3)

ds <- psych::describe(d$y, type = 2); R$desc <- list(mean = mean(d$y), sd = sd(d$y), skew = ds$skew, kurt = ds$kurtosis, median = median(d$y), q1 = unname(quantile(d$y, .25)))
s <- t.test(y ~ g2, d, var.equal = TRUE); w <- t.test(y ~ g2, d)
lev <- anova(lm(abs(d$y - ave(d$y, d$g2)) ~ d$g2))
R$t_ind <- list(t = unname(s$statistic), p = s$p.value, wt = unname(w$statistic), wdf = unname(w$parameter), wp = w$p.value, levF = lev$`F value`[1], levp = lev$`Pr(>F)`[1])
tp <- t.test(d$pre, d$post, paired = TRUE); R$t_paired <- list(t = unname(tp$statistic), p = tp$p.value)
to <- t.test(d$x1, mu = 0); R$t_one <- list(t = unname(to$statistic), p = to$p.value)
av <- summary(aov(y ~ g3, d))[[1]]; wa <- oneway.test(y ~ g3, d, var.equal = FALSE); tk <- TukeyHSD(aov(y ~ g3, d))$g3
lev3 <- anova(lm(abs(d$y - ave(d$y, d$g3)) ~ d$g3))
R$anova <- list(F = av$`F value`[1], p = av$`Pr(>F)`[1], wF = unname(wa$statistic), wdf2 = unname(wa$parameter[2]), wp = wa$p.value, levF = lev3$`F value`[1],
                tukey = list(names = rownames(tk), diff = unname(tk[, "diff"]), p = unname(tk[, "p adj"])))
ct <- chisq.test(table(d$g2, d$ycat), correct = FALSE); ct2 <- chisq.test(table(d$g2, d$x3), correct = TRUE); fi <- fisher.test(table(d$g2, d$x3))
R$chisq <- list(x2 = unname(ct$statistic), p = ct$p.value, yates = unname(ct2$statistic), yp = ct2$p.value, fisher_p = fi$p.value)
mw <- wilcox.test(y ~ g2, d, exact = FALSE, correct = TRUE); R$mw <- list(W = unname(mw$statistic), p = mw$p.value)
wx <- wilcox.test(d$pre, d$post, paired = TRUE, exact = FALSE, correct = TRUE); R$wilcox <- list(V = unname(wx$statistic), p = wx$p.value)
kw <- kruskal.test(y ~ g3, d); R$kw <- list(H = unname(kw$statistic), p = kw$p.value)
cc <- complete.cases(d$x1, d$x2)
R$cor <- list(pearson = unname(cor.test(d$x1, d$y)$estimate), pearson_p = cor.test(d$x1, d$y)$p.value,
              spearman = unname(cor.test(d$x1, d$y, method = "spearman", exact = FALSE)$estimate), spearman_p = cor.test(d$x1, d$y, method = "spearman", exact = FALSE)$p.value,
              kendall = unname(cor.test(d$x1, d$y, method = "kendall", exact = FALSE)$estimate))
dd <- d[complete.cases(d[, c("y", "x1", "x2", "x3", "g2")]), ]
m <- lm(y ~ x1 + x2 + x3 + g2, dd); sm <- summary(m)
R$lm <- list(b = unname(coef(m)), se = unname(sm$coefficients[, 2]), r2 = sm$r.squared, F = unname(sm$fstatistic[1]),
             hc3 = unname(sqrt(diag(vcovHC(m, type = "HC3")))), cr2 = unname(sqrt(diag(as.matrix(vcovCR(m, cluster = dd$firm, type = "CR2"))))),
             cr1 = unname(sqrt(diag(as.matrix(vcovCR(m, cluster = dd$firm, type = "CR1S"))))))
g <- glm(ybin ~ x1 + x3, binomial, d); R$logit <- list(b = unname(coef(g)), se = unname(summary(g)$coefficients[, 2]), dev = deviance(g))
d$ycat <- relevel(factor(d$ycat), ref = "stay"); mn <- multinom(ycat ~ x1 + x3, d, trace = FALSE, reltol = 1e-12, maxit = 1000)
R$multinom <- list(rows = rownames(coef(mn)), b = coef(mn), se = summary(mn)$standard.errors)
po <- polr(factor(yord) ~ x1 + x3, d, Hess = TRUE); R$polr <- list(b = unname(coef(po)), zeta = unname(po$zeta), se = unname(sqrt(diag(vcov(po)))[1:2]))
al <- psych::alpha(d[, c("q1", "q2", "q3")]); R$alpha <- list(raw = al$total$raw_alpha, std = al$total$std.alpha, r_drop = unname(al$item.stats$r.drop), alpha_drop = unname(al$alpha.drop$raw_alpha))
f1 <- cfa("F =~ q1 + q2 + q3", d, std.lv = TRUE); lam <- standardizedSolution(f1); lam <- lam[lam$op == "=~", "est.std"]
R$omega <- sum(lam)^2 / (sum(lam)^2 + sum(1 - lam^2))
R$kappa <- list(unweighted = kappa2(d[, c("rater1", "rater2")])$value, linear = kappa2(d[, c("rater1", "rater2")], "equal")$value, quadratic = kappa2(d[, c("rater1", "rater2")], "squared")$value,
                ac1 = gwet.ac1.raw(d[, c("rater1", "rater2")], categ.labels = 1:4)$est$coeff.val)
ic <- psych::ICC(d[, c("icc1", "icc2", "icc3")], lmer = FALSE)$results; R$icc <- list(type = ic$type, icc = ic$ICC)
fa2 <- psych::fa(d[, paste0("q", 1:6)], nfactors = 2, fm = "ml", rotate = "varimax"); R$efa <- list(loadings = unclass(fa2$loadings), communality = unname(fa2$communality))
R$kmo <- psych::KMO(d[, paste0("q", 1:6)])$MSA; R$bartlett <- psych::cortest.bartlett(cor(d[, paste0("q", 1:6)]), n = nrow(d))$chisq
fc <- cfa("F1 =~ q1 + q2 + q3\nF2 =~ q4 + q5 + q6", d); R$cfa <- as.list(fitMeasures(fc, c("chisq", "df", "cfi", "tli", "rmsea", "srmr")))
R$power <- list(t = pwr.t.test(d = .5, power = .8)$n, anova = pwr.anova.test(k = 3, f = .25, power = .8)$n * 3, r = pwr.r.test(r = .3, power = .8)$n, chisq = pwr.chisq.test(w = .3, df = 2, power = .8)$N)
# conjoint AMCE = OLS on dummies with CR2 by respondent
cj$standards_compliance <- relevel(factor(cj$standards_compliance), ref = sort(unique(cj$standards_compliance))[1])
for (v in c("track_record", "capital_commitment", "local_network")) cj[[v]] <- relevel(factor(cj[[v]]), ref = sort(unique(cj[[v]]))[1])
mc <- lm(chosen ~ standards_compliance + track_record + capital_commitment + local_network, cj)
R$amce <- list(names = names(coef(mc)), b = unname(coef(mc)), cr2 = unname(sqrt(diag(as.matrix(vcovCR(mc, cluster = cj$respondent, type = "CR2"))))))
cat(toJSON(R, digits = NA, auto_unbox = TRUE))
