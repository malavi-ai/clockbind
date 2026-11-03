BRIDGE STUDY — PROTOCOL 4.0 (STUDY 2a: PREREGISTERED SECONDARY RE-ANALYSIS OF PREVIOUSLY EXAMINED ARCHIVAL DATA)
Principal investigator: Seyed Mehdi Alavi, Doctoral School of Regional and Business Administration Sciences, Széchenyi István University.
Status: DRAFT FOR TIMESTAMPING. Becomes binding when its SHA-256 checksum is published (Zenodo) before any Study 2a coding.
Software: ClockBind 2.0.0 (`clockbind p4 ...`). The v3.4 engine remains unchanged inside the same release (`clockbind binding run`).
Revision note: revised on 3 November 2026 before timestamping, following methodological review (knowledge/feasibility/execution separated in rule 5.2; secondary re-analysis disclosure; claim-specific evidence priority; pre-specified process-tracing tests; stopping rules; disagreement tables; registration scope).

0. RELATIONSHIP TO EARLIER RECORDS
0.1 Protocol v3.4, Data Lock 1 (incl. Amendments B and C) and Lock Note 2 (Amendments D and E) constitute Study 1. They are not edited. Study 1 results are reported exactly as locked.
0.2 Protocol 4.0 governs Study 2a only: a blind re-analysis of the same archive under the extended rules below. No new data are collected (USER DECISION, 3 Nov 2026).
0.3 Every difference between Study 1 and Study 2a verdicts is reported in a concordance table and traced to the Protocol 4.0 rule that produced it (§9).
0.4 Disclosure of prior knowledge. The principal investigator designed Protocol 4.0 after examining the same archive and knowing the Study 1 verdicts. Preregistration and blind coding reduce, but do not remove, the influence of that knowledge: they make the execution of the new rules independent, not their design. Study 2a is therefore reported as a preregistered secondary re-analysis of previously examined data, not as an independent confirmation of Study 1.
0.5 No prospective component. No new data are collected (USER DECISION, 3 Nov 2026). A prospective validation with contemporaneous recording is a separate future study requiring its own approvals.

1. RESEARCH QUESTIONS
RQ1 (unchanged) When can retrospective archival evidence credibly attribute a time-critical operational constraint to finance?
RQ2 Does adding an institutional clock and a rule for requirements revealed during the process change attribution, and in which direction?
RQ3 Which constraint layers are documented as active when a delay appears financing-related? (descriptive)
RQ4 Can official public indicators discriminate between rival layers at episode level? (descriptive; expected answer: rarely)

2. UNITS AND SAMPLE
2.1 Unit: the episode as defined in Data Lock 1 (organisation, required event R, action window tW). Episode identities, merges and splits are taken from Data Lock 1 and are not re-adjudicated.
2.2 Sample: all 29 screened episodes. Screening gates and levels are re-coded blind (§7). Binding analysis is run for every episode that reaches Level 3 under Protocol 4.0 coding.
2.3 New post-lock evidence (Amendment E) enters Study 2a only through the coder packet (§7.3) and is flagged as post-lock in every output.

3. CLOCKS (six)
C1 Finance — funds usable for the transaction (not merely approved or available).
C2 Payment — transfer executed and accepted by the counterparty.
C3 Fulfilment — production, stock, reservation and dispatch preparation by the supplier.
C4 Logistics — physical transport and delivery, including carrier handling.
C5 Institutional — documentary and regulatory steps required by an authority or by law: tariff classification, movement certificates, proof of origin, product-safety or conformity control, duty and tax assessment, release. (In v3.4 customs was coded under logistics; in 4.0 it is a separate clock.)
C6 Operational readiness — installation, commissioning, training, first use.
Rule 3.1 Each step belongs to exactly one clock. Where a step mixes clocks, it is split into steps at documented boundaries; if no boundary is documented, the step keeps the clock of its documented purpose and a flag is recorded.

4. EX-ANTE STATUS OF EACH STEP
Each step receives one status:
S-D Documented ex ante — an expected duration appears in a document dated before the outcome (unchanged v3.4 rule, including the zero-duration rule of 4 Oct 2026).
S-R Revealed in process — the requirement was first documented after the process had started; the date of first documentation is recorded as revealed_at.
S-U Undocumented — neither applies.
Rule 4.1 revealed_at must come from a dated document (message, letter, declaration). Recollection is not admissible.
Rule 4.2 A step cannot be both S-D and S-R; if an ex-ante document exists, S-D prevails.

5. BINDING RULE (extends v3.4)
5.1 Core rule unchanged: a clock binds if R would have occurred by tW had that clock met its ex-ante expected duration, other clocks as documented; sign-stability across earliest and latest bounds; jointly binding, multiple-sufficient, window-infeasible and missing-inputs as in v3.4.
5.2 Revealed-in-process steps have no ex-ante duration. Knowledge, feasibility and execution are modelled separately:
  - revealed_at: date of the first dated document showing the requirement (knowledge, observed).
  - actionable_from: earliest date at which the required action could have started, supported by a dated document (feasibility; e.g. the goods, invoice or shipment that the action requires already existed). If no document supports it, actionable_from is Unknown.
  - execution time: finish − max(ready, revealed_at), the time the step took once it was known.
  Worst case (requirement unknowable in advance): the step has no ex-ante duration (untestable).
  Best case (requirement known from the start): computed only if actionable_from is documented; the step starts at max(ready, actionable_from) and takes its execution time. No hypothetical 'earliest knowable date' is used.
  If actionable_from is Unknown, the best case is not computed and the worst-case verdict is reported (normally Indeterminate). If both bounds are computed and agree, that verdict stands; if they differ, the verdict is Indeterminate with reason revelation-sensitive.
5.2a Assumption stated explicitly: the best case assumes the observed execution time would not have changed had the requirement been known earlier. This assumption is reported with every revelation-sensitive result.
5.3 Verdict categories (nine): Finance-binding; Payment-binding; Fulfilment-binding; Logistics-binding; Institution-binding; Operational-readiness-binding; Jointly binding; Non-binding; Indeterminate. Indeterminate always carries exactly one reason: window-infeasible | multiple-sufficient | sign-unstable | missing-inputs | revelation-sensitive. Revelation-sensitive is a sub-type of Indeterminate, not a causal verdict.
5.4 Finance actionability (finance usable in time) is reported separately, as in v3.4.
5.5 The fragile flag (|decisive slack| ≤ 1 day) is retained and never changes a verdict.
5.6 Pre-specified process-tracing tests. Before coding, a Tests sheet records, for each rival clock or layer, a generic test that applies to any episode reaching Level 3 under Protocol 4.0 coding, and, for the four Study 1 Level-3 episodes, episode-specific tests: the hypothesis; the observation expected if it is true; the observation expected if it is false; the test type (straw-in-the-wind, hoop, smoking-gun, doubly decisive); and the inference each outcome permits (e.g. hoop failed → rival eliminated; hoop passed → rival remains plausible, not confirmed). Tests cannot be added or changed after coding starts except by dated amendment. Test outcomes inform interpretation and claim language; they do not override the counterfactual verdict.

6. EVIDENCE TIERS AND CLAIM CEILING
6.1 Every step records source_class: internal (created by the focal firm) | counterparty (buyer or supplier) | third-party (carrier, bank, broker) | public-authority (customs, chamber, ministry); and contemporaneity: contemporaneous | retrospective.
6.2 Claim-specific evidence priority. A source's weight depends on what it directly records. A customs declaration is strong evidence of the timing of release, a bank confirmation of payment execution, a carrier scan of transit; none of them is direct evidence of when a manager or customer learned something or decided something. For each step, direct_record = Yes only if the cited source records that step's own timing. In date conflicts about the same event, a direct record prevails over an indirect one; among direct records, contemporaneous prevails over retrospective. Source class alone does not decide.
6.3 Claim ceiling extension: a positive binding verdict (single clock or jointly binding) may be stated above "is consistent with a binding constraint" only if at least one step of each binding clock is supported by a non-internal source that directly records that step (direct_record = Yes). Otherwise the claim is capped at "consistent with" and the cap is reported. The verdict itself is not changed.
6.4 Related-party flag: an episode is related-party if the researcher controls both buyer and seller. Mandatory sensitivity analysis excludes these episodes (§10).

7. BLIND CODING
7.1 Coders: two independent coders who have not seen Study 1 materials (verdicts, levels, narratives, manuscript). Earlier Study 1 coders are not eligible.
7.2 Training: fictional calibration cases only; a calibration check (raw agreement ≥ 0.80 on the calibration set) must be passed before live coding. Results of calibration are reported.
7.2a Stopping rules. Live coding does not start, or is paused, if calibration fails (retraining on new fictional cases, then a second check). Within an episode, coding stops at the first failed gate as in v3.4; binding inputs are coded only for episodes that reach Level 3 under the coder's own gate coding. Coding of the archive ends when every screened episode has a level or an S0 status.
7.3 Coder packet: produced by `clockbind p4 blind-packet`; contains Episodes, Steps and Layers inputs and source extracts, with every verdict, level, gate result, claim tier, reason, flag and researcher note removed. Episode codes are re-labelled with random packet codes; the key is held by the principal investigator.
7.4 Each coder independently codes: gates and levels (v3.4 gate definitions, unchanged), step clock, ex-ante status, revealed_at, actionable_from, source_class, direct_record, contemporaneity, and layer states (§8).
7.5 Reliability: Krippendorff's alpha (nominal) per item family (clock, ex-ante status, source class, direct record, layer state, level, verdict) with raw agreement and a full disagreement table for each family; bootstrap 95% intervals where n permits. Categories with very few observations are interpreted separately, because alpha is unstable for rare categories. Independent codes are locked before adjudication, and pre-adjudication values are always reported.
7.6 Adjudication: disagreements are resolved by discussion between the two coders with the principal investigator as recorder; every resolution is logged with reason and date. The principal investigator does not override coder consensus.

8. CONSTRAINT LAYERS (descriptive, interpretive)
8.1 Layers: L1 focal firm (finance, payment, readiness); L2 counterparty (production, stock); L3 intermediary (carrier); L4 institutional (customs, origin, classification, product control); L5 environmental (market conditions, calendar).
8.2 States per episode and layer: Activated (a dated, episode-linked record shows the layer acting within the episode) | Exposed (layer structurally present, no activation documented; e.g. non-EU border crossing without customs record; public indicator at or above the 80th percentile) | Not present (structurally absent) | Unknown.
8.3 Exposure is never reported as cause. Layer states are reported as descriptive frequencies only, with no inference beyond the archive. No configurational (QCA) analysis is planned.

9. CONCORDANCE WITH STUDY 1
9.1 `clockbind p4 concordance` cross-tabulates Study 1 (v3.4) and Study 2a (4.0) verdicts by episode.
9.2 Each changed verdict is attributed to one of: institutional clock separated from logistics; revealed-in-process rule; re-coded ex-ante status; re-coded dates or source classes; re-coded gates or levels.
9.3 Study 1 results remain the registered results for the Bridge paper; Study 2a is reported as an extension.

10. ANALYSIS AND SENSITIVITY
10.1 Primary: verdicts under Protocol 4.0 for all 29 screened episodes, re-coded from the start (not only the four Study 1 Level-3 episodes); concordance with Study 1; reliability.
10.2 Sensitivity (all reported, none replaces the primary result): (a) excluding related-party episodes; (b) excluding episodes whose binding clocks rest only on internal sources; (c) institutional steps re-merged into logistics (reproduces the v3.4 clock set); (d) zero-duration rule relaxed (as in v3.4 sensitivity).
10.3 External triangulation follows Lock Note 2 rules R1–R9, with indicators linked to the country and dates of each leg (not of the episode as a whole). It never changes a verdict.

11. DATA PROTECTION AND ETHICS
11.1 Existing archive only; covered by approval SZE/ETT-144/2026. No new participants or data sources.
11.2 Records are business-to-business transaction documents. Names and contact details of individuals are not extracted; quotations are attributed by role only. Türkiye-origin material is used only in de-identified form until the transfer gate is closed.
11.3 Coders sign the existing confidentiality and independence declaration. Coder access is limited to the de-identified coder packet; the episode key stays with the principal investigator.
11.4 Public registration is not data publication. Only this protocol, the coding manual, blank forms and the software are published. No episode-level data, documents, dates, countries or the identity crosswalk are published or uploaded to any registry.

12. INTEGRITY
12.1 This protocol, the coding manual, blank coding forms, the pre-specified Tests sheet and the ClockBind 2.0.0 release are frozen by SHA-256 checksums and published on Zenodo before any Study 2a coding begins, under the title 'Preregistered secondary re-analysis of previously examined archival data'.
12.2 Data Lock 2 (Study 2a coding) follows the Data Lock 1 procedure (`clockbind lock`), with a manifest and append-only register.
12.3 Any change after timestamping requires a dated amendment with reason; earlier versions are kept.

13. CLAIM LANGUAGE
Use: "was binding under the specified decision rule" (only at the highest tier); "is consistent with"; "could not be determined"; "in this archive".
Avoid: "caused"; "proved"; "finance was not a constraint"; population-level statements.

14. OUTPUTS
Study 2a results feed a separate paper (Bridge 2.0). The Bridge paper (Study 1) is not delayed by Study 2a.
