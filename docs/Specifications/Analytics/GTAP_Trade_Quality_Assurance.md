# GTAP Trade Quality Assurance (TQA)

> **Document Version:** 1.0
> **Project:** GTAP (Greedy Trading Automation Platform)
> **Status:** Active

---

# Purpose

Every completed trade is automatically inspected before being accepted into the GTAP analytics database.

The objective is to identify abnormal trades, execution issues, platform bugs, and unexpected behavior before they affect strategy evaluation.

A trade may still be valid while being flagged for review.

---

# Quality Levels

## PASS

Trade follows all expected parameters.

No review required.

---

## WARNING

Trade completed successfully but contains unusual characteristics.

Requires manual review.

---

## CRITICAL

Trade indicates a potential platform or execution failure.

Must be investigated before strategy promotion.

---

# Quality Checks

---

## 1. Outlier Loss Detection

Purpose:

Identify trades whose loss greatly exceeds expected risk.

### Rule

Flag when:

Actual Loss > Expected Risk × Threshold

Default Threshold:

2.0x

Example

Expected Risk:

10 points

Actual Loss:

25 points

Result

⚠ WARNING

---

## 2. Outlier Profit Detection

Purpose:

Detect unusually large wins.

Although positive, these may indicate:

- missed exit
- execution bug
- duplicate fills
- incorrect target

Rule

Profit > Expected Target × 2

Result

⚠ Review Required

---

## 3. Missing Stop Loss

Trigger

Trade opens without stop attached.

Severity

🔴 CRITICAL

---

## 4. Missing Take Profit

Trigger

No TP order submitted.

Severity

🟡 WARNING

---

## 5. Slippage Detection

Measure

Expected Entry

vs

Actual Fill

If slippage exceeds threshold:

Flag trade.

---

## 6. Holding Time Outlier

Every strategy has an expected holding time.

Example

Greedy Man

Expected:

15 seconds – 5 minutes

Trade Duration:

48 minutes

Result

⚠ Review

---

## 7. Risk Violation

Detect when:

Actual Risk >

Configured Risk

Severity

🔴 CRITICAL

---

## 8. Position Size Violation

Trigger

Contracts >

Allowed Contracts

Severity

🔴 CRITICAL

---

## 9. Trading Session Violation

Trigger

Trade entered outside allowed session.

Severity

🟡 WARNING

---

## 10. Duplicate Trade Detection

Trigger

Same entry

Same time

Same direction

Same price

Severity

🔴 CRITICAL

---

## 11. Missing Repository Record

Trade executed

Repository missing record

Severity

🔴 CRITICAL

---

## 12. Analytics Sync Failure

Repository updated

Analytics not updated

Severity

🔴 CRITICAL

---

# Trade Quality Score

Each trade receives a quality score.

| Category | Weight |
|-----------|--------:|
| Execution | 30 |
| Risk | 25 |
| Data Integrity | 20 |
| Rule Compliance | 15 |
| Strategy Compliance | 10 |

Maximum Score

100

---

## Rating

### 🟢 95–100

Excellent

---

### 🟡 85–94

Minor Issues

---

### 🟠 70–84

Needs Review

---

### 🔴 Below 70

Critical Investigation

---

# Example Report

Trade ID:

36

Quality Score:

58 / 100

Issues Detected

✓ Holding Time Outlier

✓ Loss Exceeded Expected Risk

✓ Risk Violation

Recommendation

Review before approving strategy.

---

# Strategy Health

Trade Quality also contributes to the overall GTAP Strategy Readiness Score.

Example

Trade Quality Average

98.4 / 100

This ensures that profitable strategies with poor execution quality are not promoted.

---

# Core Principle

Profitability alone is not sufficient.

A strategy must also demonstrate:

- Reliable execution
- Consistent risk management
- Accurate trade recording
- High-quality operational performance

Only strategies with both strong performance and high trade quality are eligible for promotion.