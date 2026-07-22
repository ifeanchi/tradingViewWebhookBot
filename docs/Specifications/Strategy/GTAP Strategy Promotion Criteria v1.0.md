# GTAP Strategy Promotion Criteria v1.0

> **Document Version:** 1.0  
> **Project:** GTAP (Greedy Trading Automation Platform)  
> **Status:** Active  
> **Purpose:** Define the objective criteria required for a trading strategy to advance through each stage of the GTAP validation pipeline.

---

# Philosophy

Every trading strategy within GTAP must pass the same objective evaluation process before progressing to the next stage.

This prevents emotional decision-making and ensures that every strategy is validated using measurable performance and risk metrics.

The promotion process evaluates both:

- Platform Readiness
- Strategy Readiness

A strategy advances only after satisfying all required criteria for its current stage.

---

# GTAP Strategy Lifecycle

```
Research
    │
    ▼
Backtesting
    │
    ▼
Forward Testing
    │
    ▼
Paper Trading
    │
    ▼
Prop Evaluation
    │
    ▼
Live Trading
```

---

# Stage 1 — Research

## Objective

Define the strategy completely before writing code or placing trades.

### Requirements

- Trading rules documented
- Entry rules clearly defined
- Exit rules clearly defined
- Stop Loss defined
- Take Profit defined
- Position sizing defined
- Trading session rules defined
- Risk rules documented

### Promotion Decision

✅ Approved for Backtesting

---

# Stage 2 — Backtesting

## Objective

Verify that the strategy has historical validity.

### Minimum Requirements

| Metric | Requirement |
|---------|------------|
| Net Profit | Positive |
| Expectancy | Positive |
| Profit Factor | > 1.30 |
| Rule Consistency | 100% |
| Coding Errors | None |
| Look-Ahead Bias | None |

### Promotion Decision

✅ Approved for Forward Testing

---

# Stage 3 — Forward Testing

## Objective

Validate strategy performance in live market conditions while trading manually.

## Minimum Trade Count

- Minimum 50 completed trades

Trade count alone does not guarantee promotion.

The strategy must also satisfy all quality metrics.

---

# Execution Quality

These are pass/fail requirements.

| Metric | Requirement |
|---------|------------|
| Missing Trades | 0 |
| Duplicate Trades | 0 |
| Repository Errors | 0 |
| Analytics Errors | 0 |
| Rule Violations | 0 |

Failure in any category requires correction before promotion.

---

# Strategy Performance Metrics

| Metric | Minimum Requirement |
|---------|-------------------:|
| Total Trades | ≥ 50 |
| Win Rate | ≥ 55% |
| Profit Factor | ≥ 1.50 |
| Positive Expectancy | Required |
| Net Profit | Positive |
| Average Risk:Reward | ≥ 1.8 |
| Largest Loss | Within Planned Risk |
| Rule Compliance | 100% |

---

# Risk Metrics

Risk is evaluated using **R-Multiples** instead of dollar values to ensure consistency across account sizes.

| Metric | Requirement |
|---------|------------|
| Maximum Drawdown | < 10R |
| Consecutive Losses | Within Acceptable Limits |
| Risk Per Trade | Never Exceeded |
| Daily Loss Limit | Never Exceeded |

---

# Behavioral Metrics

Applicable during manual forward testing.

| Metric | Requirement |
|---------|------------|
| Strategy Followed Exactly | Yes |
| No FOMO Entries | Yes |
| No Revenge Trades | Yes |
| No Moving Stop Loss | Yes |
| No Emotional Exits | Yes |

---

# Analytics Requirements

GTAP must successfully generate:

- Performance Summary
- Equity Curve
- Drawdown Report
- Streak Analysis
- Time Analytics
- Session Analytics
- Promotion Report

---

# Promotion Decision Matrix

## GREEN — Approved

Example:

| Metric | Value |
|---------|------:|
| Trades | 57 |
| Win Rate | 61% |
| Profit Factor | 1.84 |
| Expectancy | Positive |
| Drawdown | Within Limits |
| Execution Errors | 0 |

**Decision**

✅ APPROVED FOR PAPER TRADING

---

## YELLOW — Continue Forward Testing

Example:

| Metric | Value |
|---------|------:|
| Trades | 50 |
| Profit Factor | 1.42 |
| Expectancy | Positive |

**Decision**

Continue Forward Testing

---

## RED — Return to Research

Example:

| Metric | Value |
|---------|------:|
| Trades | 54 |
| Profit Factor | 0.93 |
| Expectancy | Negative |

**Decision**

Return to Strategy Development

---

# Stage 4 — Tradovate Paper Trading

## Objective

Validate GTAP automation.

This stage evaluates the platform rather than the trading strategy itself.

### Requirements

- Orders submitted correctly
- Stop Loss attached correctly
- Take Profit attached correctly
- Orders closed correctly
- Repository updated automatically
- Analytics updated automatically
- Zero execution bugs

### Minimum Requirement

- 50 automated paper trades

### Promotion Decision

✅ Approved for Prop Evaluation

---

# Stage 5 — Prop Evaluation

## Objective

Verify that GTAP can operate within prop firm constraints.

### Requirements

- Daily loss limits respected
- Maximum drawdown respected
- Stable performance
- No platform failures
- Risk management functioning correctly

### Promotion Decision

✅ Approved for Live Trading

---

# Stage 6 — Live Trading

GTAP graduates to production.

Future improvements continue through strategy versioning rather than bypassing the validation pipeline.

---

# GTAP Readiness Score

Every strategy receives a readiness score before promotion.

| Category | Weight |
|----------|-------:|
| Profitability | 30% |
| Risk Management | 25% |
| Consistency | 20% |
| Execution Quality | 15% |
| Rule Compliance | 10% |

## Promotion Bands

### 🟢 90–100

Ready for promotion.

---

### 🟡 80–89

Promising.

Continue testing or improve weak areas.

---

### 🔴 Below 80

Return to strategy development.

---

# Core Principle

No strategy advances because it "feels good."

Every promotion within GTAP is earned through objective performance, disciplined execution, and measurable evidence.