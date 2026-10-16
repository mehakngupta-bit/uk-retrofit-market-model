# UK Home Retrofit: Market Sizing and Scenario Model

How much money would it take to bring England's homes up to EPC band C by 2035, how fast would it need to be spent, and how much of it can public funding cover?

This is a hypothesis-led market sizing and scenario analysis built in Python. It follows the structure of a consulting workstream: question, hypothesis, sourced inputs, flagged assumptions, three scenarios, sensitivity analysis and a one-page recommendation (see `memo/one_page_recommendation.md`).

## Hypothesis

England's retrofit market is worth tens of billions of pounds over ten years, but public funding covers less than half of it in a realistic scenario, and the size of the market depends most on owner-occupier uptake, which policy does not mandate.

## Headline results (base case, 2026 to 2035)

| Metric | Result |
|---|---|
| Homes below EPC C | 11.35m of 25.8m |
| Average cost to lift one below-C home to C | £5,818 (weighted) |
| Upgrading every below-C home (ceiling) | £66.0bn |
| Base case spend | £34.4bn on 5.9m homes |
| Peak annual spend | £6.05bn in 2030 |
| Public funding as share of base case | 44% (£15bn of £34.4bn) |
| Private capital needed | £19.4bn |

| Scenario | Homes upgraded | Total spend | Public funding share |
|---|---|---|---|
| Slow | 3.35m | £19.5bn | 77% |
| Base | 5.91m | £34.4bn | 44% |
| Accelerated | 8.23m | £47.9bn | 31% |

Base case spend by tenure: private rented £10.9bn, social £8.6bn, owner occupied £14.8bn.

Biggest sensitivities on the £34.4bn base: owner-occupier uptake (£25.9bn to £45.0bn) and the cost of upgrading a D-rated home (£27.3bn to £41.5bn). See `outputs/chart_sensitivity.png` and `outputs/two_way_table.csv`.

## Method

1. **Size the problem.** Homes by tenure (MHCLG) multiplied by the share rated below band C (English Housing Survey 2024 to 2025: 35% band D, 9% bands E to G).
2. **Cost it.** Average cost per home, weighted between D-rated homes (£5,000) and E to G homes (£9,000).
3. **Time it.** Each tenure reaches an assumed uptake by its deadline: private rented 2030 (Warm Homes Plan landlord deadline), social and owner occupied 2035 (assumptions). Cumulative uptake follows a quadratic curve, so annual deployment rises as installer capacity builds.
4. **Stress it.** Three uptake scenarios, one-at-a-time sensitivities and a two-way table of owner-occupier uptake against cost.

## What is sourced and what is assumed

Every input is in `data/inputs.csv` with a `type` column marking it as `sourced` or `assumption`.

Sourced: dwelling stock and tenure, EPC band shares, the £5,400 average private rented upgrade cost, the £10,000 landlord cost cap, the 2030 landlord deadline, the £15bn Warm Homes Plan.

Assumed (treat as judgement, not fact): cost per D-rated and E to G home, uptake rates in each scenario, the 2035 horizon for social and owner-occupied homes, and the shape of the deployment curve.

## Limitations

- The EPC band split is applied equally to every tenure. Private rented homes are likely to perform worse than average, so private rented demand is probably understated.
- The EPC split comes from a survey and is applied to the full stock as if it were a census.
- The £15bn public funding figure includes loans and measures beyond EPC C works (for example solar and smart technology), and comes from a plan that covers more than England's stock. The comparison with model spend is indicative, not exact.
- Costs are in current prices. There is no inflation, cost decline from scale or rebound effect.
- The model sizes the spend needed, not the share a given firm could win.

## Run it

```bash
pip install -r requirements.txt
python src/model.py
```

Outputs are written to `outputs/` (summary tables, by-year detail, sensitivity table and three charts).

## Talking points for interviews

- **Why these segments?** Private rented has a hard deadline and a cost cap, so demand is the most predictable. Owner occupied is the largest and least certain.
- **Why quadratic ramp-up?** Installer capacity and supply chains cannot reach full speed in year one, so spend peaks near the deadline.
- **What would change my answer?** A confirmed social housing standard, evidence that private rented homes sit well below the national EPC average, or a measured cost per home by band.
- **What would I do next?** Replace the cost assumptions with regional cost data, split the EPC bands by tenure, and add a financing layer (loan sizes, returns, default risk).

## References

Knight Frank (2026) *Warm Homes Plan: implications for real estate and the private rented sector*. Available at: https://www.knightfrank.co.uk/research/article/2026/1/warm-homes-plan-implications-for-real-estate-and-the-private-rented-sector2 (Accessed: 15 October 2026).

Ministry of Housing, Communities and Local Government (2025) *Dwelling stock estimates, England: 31 March 2025*. Available at: https://www.gov.uk/government/statistics/dwelling-stock-estimates-in-england-2025/dwelling-stock-estimates-england-31-march-2025 (Accessed: 15 October 2026).

Ministry of Housing, Communities and Local Government (2026) *English Housing Survey 2024 to 2025: headline findings on housing quality and energy efficiency*. Available at: https://www.gov.uk/government/statistics/chapters-for-english-housing-survey-2024-to-2025-headline-findings-on-housing-quality-and-energy-efficiency/introduction-and-key-findings (Accessed: 15 October 2026).

Mortgage Solutions (2026) 'Warm Homes Plan confirms 2030 deadline for landlords to reach EPC C', 21 January. Available at: https://www.mortgagesolutions.co.uk/green/2026/01/21/warm-homes-plan-confirms-2030-deadline-for-landlords-to-reach-epc-c/ (Accessed: 15 October 2026).

Resolution Foundation (n.d.) Analysis of the Warm Homes Plan [CHECK TITLE AND DATE]. Available at: https://www.resolutionfoundation.org/?p=45046 (Accessed: 15 October 2026).
