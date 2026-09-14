# v0.7 frozen experiment specification

Recorded before the first matrix campaign. No result-based parameter changes or retries.

- Base ccbfce6, AAV one_hot, cold HD<=2 (10433), pool HD>2 (27832), existing gate HD<=4 and mean BLOSUM62>=0, existing EpistasisRidge defaults (3 bootstrap variance members), budget 48x6=288.
- Acquisition seeds 42/0/7 for mean, alternating, full, semi. Fixed cold-start, model split and bootstrap seeds. LLM randomness is not controlled by these seeds.
- Pure mean reference: predicted_mean every round. Alternating: mean/diverse on odd/even one-based rounds; exact old diverse score and RNG consumption.
- FULL: predicted-mean default; LLM freely chooses when/how much exploration, including late rounds. SEMI: two consecutive non-improving newly measured cumulative maxima require a full exploratory batch each round until improvement; LLM chooses its method.
- Exploration methods: diverse = mean+3*sqrt(var)+U(0,1), uncertainty = variance ordering, spread = shortlist top 10*n UCB followed by greedy normalized-UCB plus minimum fractional Hamming distance to measured top10 and selected batch. All are gate-filtered, unmeasured-only, without hard geometric exclusion. No beta/distance tuning.
- Numeric ceiling/peak and target sequence are absent from the LLM prompt and policy. This intentionally uses the contract's general surrogate underestimation hypothesis without revealing oracle-derived 7.8 or rank/sequence hints.
- C+A retained: safe tools and exact staged batch testing, live surrogate CV. v0.5 B exploitation floors retained only in legacy mode; v0.7 default pure mean with free exploration proportions.
- Default actual backend resolved through llm.py: claude-sonnet-5 at configured OpenAI-compatible gateway. Provider/API failures, fallback and skipped tests count separately; no fallback-only trial called an LLM success.
- Online audit logs every selected candidate's pre-measurement mean, variance and eligible mean rank, plus exact measured labels and progress. Target peak/rank analyzed only after trials.
- Real AAV cold label-shuffle CV control, rising/plateau unit tests, consumer tests only. No full suite.
- origin/main be62937 has no common ancestor with task base; safe rebase blocked. No forced history graft.
