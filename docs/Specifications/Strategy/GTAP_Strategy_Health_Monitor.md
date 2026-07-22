# GTAP Strategy Health Monitor (SHM)

> **Document Version:** 1.0
> **Project:** GTAP (Greedy Trading Automation Platform)
> **Component:** Strategy Health Monitor (SHM)
> **Status:** Active

---

# Purpose

The Strategy Health Monitor continuously evaluates the operational health of every trading strategy within GTAP.

Unlike profitability metrics alone, the SHM combines performance, execution quality, risk management, platform stability, and data integrity into a single health assessment.

The objective is to determine whether a strategy is safe to promote, safe to automate, and safe to trade with live capital.

---

# Philosophy

A profitable strategy can still be unhealthy.

Examples:

- Excessive drawdowns
- Frequent execution errors
- Poor rule compliance
- Missing repository records
- Platform instability
- Data synchronization failures

GTAP promotes healthy strategies—not simply profitable ones.

---

# Health Categories

## 1. Profitability

Weight: **25%**

### Metrics

- Net Profit
- Profit Factor
- Expectancy
- Win Rate
- Average R-Multiple

---

## 2. Risk Management

Weight: **20%**

### Metrics

- Maximum Drawdown
- Daily Loss Compliance
- Risk Per Trade
- Consecutive Losses
- Largest Loss
- Recovery Factor

---

## 3. Execution Quality

Weight: **15%**

### Metrics

- Entry Accuracy
- Exit Accuracy
- Slippage
- Holding Time Compliance
- Stop Loss Attached
- Take Profit Attached

---

## 4. Strategy Discipline

Weight: **10%**

### Metrics

- Rule Compliance
- No FOMO Trades
- No Revenge Trades
- No Manual Overrides
- Session Compliance

---

## 5. Data Integrity

Weight: **10%**

### Metrics

- Repository Sync
- Analytics Sync
- Missing Trades
- Duplicate Trades
- Corrupt Records

---

## 6. Platform Stability

Weight: **10%**

### Metrics

- API Errors
- Database Errors
- Order Submission Errors
- Connection Failures
- Retry Success Rate

---

## 7. Trade Quality

Weight: **10%**

Average Trade Quality Score from the Trade Quality Assurance system.

---

# Overall Health Score

Each category contributes to an overall score out of 100.

| Category | Weight |
|----------|-------:|
| Profitability | 25% |
| Risk Management | 20% |
| Execution Quality | 15% |
| Strategy Discipline | 10% |
| Data Integrity | 10% |
| Platform Stability | 10% |
| Trade Quality | 10% |

---

# Health Ratings

## 🟢 Excellent (90–100)

Strategy is operating at institutional quality.

Recommendation:

Eligible for promotion.

---

## 🟢 Good (80–89)

Healthy overall.

Minor improvements recommended.

---

## 🟡 Fair (70–79)

Operational concerns detected.

Continue monitoring.

Promotion not recommended until issues are resolved.

---

## 🟠 Poor (60–69)

Significant weaknesses detected.

Requires investigation.

---

## 🔴 Critical (<60)

Strategy health unacceptable.

Promotion blocked.

Immediate review required.

---

# Health Dashboard

Example:

--------------------------------------------------

GTAP Strategy Health Dashboard

Strategy:
Greedy Man v1.0

Overall Health

94 / 100

--------------------------------------------------

Profitability

92

█████████░

Risk

96

██████████

Execution

95

██████████

Discipline

100

██████████

Trade Quality

97

██████████

Platform

98

██████████

Data Integrity

100

██████████

--------------------------------------------------

Recommendation

READY FOR PAPER TRADING

--------------------------------------------------

---

# Health Trend

Health should also be monitored over time.

Example

Week 1

82

Week 2

88

Week 3

92

Week 4

95

A declining trend is an early warning that a strategy may be degrading even if profitability remains positive.

---

# Alert Levels

## INFO

Minor anomaly detected.

No action required.

---

## WARNING

Health score below 85.

Review recommended.

---

## HIGH

Health score below 75.

Promotion paused.

---

## CRITICAL

Health score below 60.

Trading disabled until reviewed.

---

# Integration

The Strategy Health Monitor receives data from:

- Strategy Engine
- Repository
- Analytics Engine
- Risk Engine
- Trade Quality Assurance
- Reporting Engine
- Tradovate Connector

It serves as the centralized operational assessment layer for GTAP.

---

# Promotion Gate

Before a strategy advances to the next lifecycle stage, the Strategy Health Monitor must confirm:

- Health Score ≥ 90
- No unresolved critical alerts
- No critical execution failures
- No data integrity failures
- No platform stability failures
- Promotion Criteria satisfied

Only then is the strategy eligible for advancement.

---

# Core Principle

GTAP does not promote strategies solely because they are profitable.

A strategy must demonstrate:

- Sustainable profitability
- Controlled risk
- Reliable execution
- Complete data integrity
- Stable platform operation
- High operational quality

The Strategy Health Monitor is the final authority on whether a strategy is ready to advance through the GTAP lifecycle.