# GTAP Software Design Specification

# Volume II

# 03 — Risk Engine Specification

---

| Property | Value |
|----------|-------|
| Project | GTAP (Greedy Trading Automation Platform) |
| Module | Risk Engine |
| Document ID | GTAP-SDS-VII-03 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | Stanley Enyinnaya |
| Depends On | Position Manager |
| Criticality | CRITICAL |

---

# Table of Contents

1. Purpose
2. Scope
3. Responsibilities
4. Non-Responsibilities
5. Design Philosophy
6. Inputs
7. Outputs
8. Risk Decision Pipeline
9. Risk Evaluation Order
10. Risk Rules
11. Position Sizing
12. Exposure Management
13. State Machine
14. Decision Matrix
15. Error Codes
16. Audit & Logging
17. Performance
18. Configuration
19. Recovery
20. Acceptance Criteria
21. Future Enhancements

---

# 1. Purpose

The Risk Engine is the final authority responsible for determining whether a proposed trading action is permitted.

Its mission is to protect trading capital by ensuring every request complies with GTAP's configured risk policies before execution.

No order may reach the Execution Engine without explicit approval from the Risk Engine.

---

# 2. Scope

The Risk Engine evaluates:

- Account-level limits
- Position-level limits
- Trade-level limits
- Strategy permissions
- Session restrictions
- Broker readiness
- Margin availability
- Buying power
- Daily drawdown
- Maximum exposure

---

# 3. Responsibilities

The Risk Engine SHALL:

✓ Evaluate every trade request

✓ Calculate projected exposure

✓ Enforce configured limits

✓ Resize trades when allowed

✓ Reject invalid requests

✓ Produce deterministic decisions

✓ Publish immutable audit events

---

# 4. Non-Responsibilities

The Risk Engine SHALL NOT:

✗ Generate signals

✗ Manage positions

✗ Submit broker orders

✗ Calculate analytics

✗ Modify historical events

---

# 5. Design Philosophy

The Risk Engine is built upon five principles.

## Risk Before Opportunity

Protecting capital always takes priority over entering a trade.

---

## Default Deny

Every request begins in a rejected state.

Approval must be earned by passing every validation rule.

---

## Deterministic Decisions

The same inputs must always produce the same decision.

---

## Explicit Decisions

The Risk Engine never returns ambiguous results.

Every request ends with one clear outcome.

---

## Complete Auditability

Every evaluation must be reconstructable after execution.

---

# 6. Inputs

The Risk Engine receives:

Validated Signal

Current Position

Account State

Broker Status

Market Data

Risk Configuration

Strategy Configuration

---

# 7. Outputs

Exactly one decision is returned.

APPROVE

REJECT

RESIZE

DELAY

CANCEL

No additional decision types are permitted without an approved ADR.

---

# 8. Risk Decision Pipeline

Incoming Position Decision

↓

Account Validation

↓

Broker Validation

↓

Trading Session Validation

↓

Strategy Permission Validation

↓

Buying Power Validation

↓

Position Limit Validation

↓

Exposure Validation

↓

Drawdown Validation

↓

Risk Per Trade Validation

↓

Decision Generation

↓

Publish Risk Event

---

Every rule must execute in the defined order.

---

# 9. Risk Evaluation Order

The order of evaluation is fixed.

1. Request Integrity

2. Broker Status

3. Trading Session

4. Strategy Enabled

5. Symbol Enabled

6. Buying Power

7. Margin

8. Position Size

9. Daily Drawdown

10. Portfolio Exposure

11. Risk Per Trade

12. Final Decision

Later rules must never execute if an earlier rule produces a terminal rejection.

---

# 10. Risk Rules

## Daily Loss Limit

Reject if:

Daily Loss ≥ Configured Limit

---

## Maximum Contracts

Reject if:

Projected Position > Maximum Contracts

---

## Buying Power

Reject if:

Buying Power < Required Margin

---

## Margin

Reject if:

Required Margin exceeds Available Margin

---

## Session

Reject if:

Trading outside approved hours.

---

## Strategy Permission

Reject if:

Strategy disabled.

---

## Symbol Permission

Reject if:

Instrument disabled.

---

## Broker Status

Reject if:

Broker unavailable.

---

## Exposure

Reject if:

Portfolio exposure exceeds configured threshold.

---

## Risk Per Trade

Reject if:

Projected loss exceeds configured percentage.

---

# 11. Position Sizing

The Risk Engine may resize orders.

Example:

Requested:

10 Contracts

Maximum Allowed:

6 Contracts

Decision:

RESIZE

Approved Quantity:

6

Resizing must always be logged.

---

# 12. Exposure Management

Exposure is monitored across:

Account

Strategy

Instrument

Portfolio

Future versions may include sector and correlation exposure.

---

# 13. State Machine

```
RECEIVED

↓

VALIDATING

↓

CALCULATING

↓

DECISION_READY

↓

APPROVED
```

Alternative terminal states:

REJECTED

RESIZED

DELAYED

CANCELLED

FAILED

---

# 14. Decision Matrix

| Rule | Pass | Fail |
|------|------|------|
| Broker Online | Continue | Reject |
| Session Open | Continue | Reject |
| Strategy Enabled | Continue | Reject |
| Buying Power | Continue | Reject |
| Margin | Continue | Reject |
| Max Contracts | Continue | Resize / Reject |
| Drawdown | Continue | Reject |
| Exposure | Continue | Reject |
| Risk Per Trade | Continue | Reject |

---

# 15. Standard Error Codes

| Code | Description |
|------|-------------|
| R001 | Duplicate Request |
| R002 | Daily Loss Limit |
| R003 | Maximum Contracts |
| R004 | Buying Power |
| R005 | Margin |
| R006 | Broker Offline |
| R007 | Position Conflict |
| R008 | Symbol Disabled |
| R009 | Trading Session Closed |
| R010 | Risk Per Trade Exceeded |
| R011 | Portfolio Exposure |
| R012 | Strategy Disabled |

Error codes are stable API contracts and must not be reused for different meanings.

---

# 16. Audit & Logging

Every evaluation records:

- Request ID
- Position ID
- Account
- Strategy
- Symbol
- Timestamp
- Rules Evaluated
- Rule Outcomes
- Final Decision
- Decision Reason
- Engine Version

Logs are immutable and retained according to platform policy.

---

# 17. Performance Requirements

Target metrics:

Single evaluation:

<15 ms

Maximum latency:

<20 ms

Throughput:

500+ evaluations/second

No network calls should block rule evaluation except validated broker status checks.

---

# 18. Configuration

Configurable parameters include:

```
daily_loss_limit

risk_per_trade

maximum_contracts

maximum_portfolio_exposure

maximum_strategy_exposure

allow_resizing

session_start

session_end

allowed_symbols

enabled_strategies
```

Configuration changes should not require source-code changes.

---

# 19. Recovery

On restart:

Load configuration

↓

Restore account state

↓

Restore open positions

↓

Synchronize broker status

↓

Resume evaluation

Historical risk decisions are never recalculated.

---

# 20. Acceptance Criteria

The Risk Engine is complete when:

✓ Every request receives one deterministic decision.

✓ Rules execute in the documented order.

✓ Rejections stop downstream processing.

✓ Resized trades preserve audit history.

✓ Decisions are reproducible from recorded inputs.

✓ Performance targets are met.

✓ All decision reasons are logged.

---

# 21. Future Enhancements

Future versions may support:

- Dynamic volatility-based risk
- Correlation limits
- Sector exposure controls
- Machine-learning anomaly detection
- Portfolio Value-at-Risk (VaR)
- Stress testing
- Adaptive position sizing
- Multi-account capital allocation
- Real-time risk dashboards

These enhancements must preserve the Risk Engine's role as the final approval authority before execution.

---

# Appendix A — Engine Contract

Consumes:

- Validated Signal
- Position Decision
- Account State
- Configuration

Produces:

- APPROVE
- REJECT
- RESIZE
- DELAY
- CANCEL

Owns:

Risk evaluation and trade authorization.

Does Not Own:

Signal generation, position management, order execution, broker communication, or analytics.

---

# Closing Statement

The Risk Engine is the primary safeguard of GTAP. Every trade, regardless of its source, strategy, or confidence level, must pass through this engine before capital is committed. By enforcing deterministic evaluation, explicit ownership, comprehensive auditability, and configurable risk policies, the Risk Engine ensures that GTAP remains disciplined, resilient, and trustworthy under both normal and exceptional market conditions.

---

**End of Document**