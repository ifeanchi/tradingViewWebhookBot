# GTAP Request Lifecycle

---

| Property | Value |
|----------|-------|
| Project | GTAP (Greedy Trading Automation Platform) |
| Document | Request Lifecycle |
| Version | 1.0.0 |
| Status | Draft |
| Owner | Stanley Enyinnaya |
| Last Updated | July 2026 |

---

# Purpose

This document describes the complete lifecycle of a trading request inside GTAP.

It defines:

- how a signal enters the platform,
- how it is validated,
- how risk is evaluated,
- how orders are executed,
- how positions are managed,
- and how every event is recorded.

This document serves as the reference workflow for all module specifications.

---

# High-Level Lifecycle

```
TradingView

↓

Webhook

↓

Strategy Engine

↓

Position Manager

↓

Risk Engine

↓

Execution Engine

↓

Broker Connector

↓

Broker

↓

Repository

↓

Analytics

↓

Health Monitor

↓

Archive
```

Every request follows this exact sequence.

No module may bypass another module unless explicitly documented by a future ADR.

---

# Lifecycle Overview

Every request progresses through twelve stages.

| Stage | Description |
|--------|-------------|
| 1 | Signal Creation |
| 2 | Signal Reception |
| 3 | Strategy Validation |
| 4 | Position Evaluation |
| 5 | Risk Evaluation |
| 6 | Execution Planning |
| 7 | Broker Submission |
| 8 | Execution Monitoring |
| 9 | Position Update |
| 10 | Repository Update |
| 11 | Analytics Update |
| 12 | Lifecycle Completion |

---

# Stage 1 — Signal Creation

Owner:

External Strategy

Examples:

- TradingView
- Pine Script
- Future AI Strategy

The strategy generates a trading opportunity.

Example:

```
BUY MES

Price: 6320.25

Stop: 6315.25

Target: 6330.25
```

This is still an external alert.

It is **not yet** a GTAP Signal.

---

# Stage 2 — Signal Reception

Owner:

Strategy Engine

Responsibilities:

- Receive webhook
- Parse JSON
- Verify schema
- Timestamp request
- Generate Request ID

Output:

```
IncomingRequest
```

Example:

```
REQ-20260718-000154
```

Every request receives a globally unique identifier.

---

# Stage 3 — Strategy Validation

Owner:

Strategy Engine

Validation includes:

- Required fields
- Strategy enabled
- Symbol supported
- Duplicate detection
- Timestamp validity
- Payload integrity

Possible outcomes:

```
Accepted

Rejected
```

Rejected requests terminate immediately.

Accepted requests become GTAP Signals.

---

# Stage 4 — Position Evaluation

Owner:

Position Manager

Responsibilities:

- Determine current position
- Detect reversals
- Detect adds
- Detect reductions
- Detect duplicate entries
- Calculate projected position

Possible outcomes:

```
Flat

Open

Add

Reduce

Reverse

Ignore
```

Output:

Position Decision

---

# Stage 5 — Risk Evaluation

Owner:

Risk Engine

Checks include:

- Daily loss
- Max contracts
- Buying power
- Margin
- Session
- Risk per trade
- Position exposure
- Strategy permissions
- Broker availability

Possible outcomes:

```
Approve

Reject

Resize

Delay

Cancel
```

Rejected requests terminate.

Approved requests continue.

---

# Stage 6 — Execution Planning

Owner:

Execution Engine

Responsibilities:

- Build broker order
- Determine order type
- Validate order parameters
- Assign execution ID
- Prepare retry policy

Output:

Execution Plan

---

# Stage 7 — Broker Submission

Owner:

Broker Connector

Responsibilities:

- Authenticate
- Submit order
- Receive acknowledgment
- Handle broker errors

Possible responses:

```
Accepted

Rejected

Pending
```

---

# Stage 8 — Execution Monitoring

Owner:

Execution Engine

Responsibilities:

- Monitor fills
- Detect partial fills
- Retry when necessary
- Handle timeouts
- Track order lifecycle

Possible events:

```
Submitted

Acknowledged

Partial Fill

Filled

Cancelled

Expired

Rejected
```

Execution completes only after a terminal broker state.

---

# Stage 9 — Position Update

Owner:

Position Manager

Responsibilities:

- Update position size
- Update average entry
- Update realized PnL
- Update unrealized PnL
- Detect flat position

The Position Manager becomes the authoritative source for current position state.

---

# Stage 10 — Repository Update

Owner:

Repository

Every lifecycle event is persisted.

Examples:

- Signal
- Risk Decision
- Execution
- Fill
- Position
- Trade
- Metrics

Nothing is discarded.

---

# Stage 11 — Analytics Update

Owner:

Analytics Engine

Updates include:

- Win rate
- Profit factor
- Drawdown
- Trade duration
- MAE
- MFE
- Strategy statistics
- Daily metrics

Analytics are computed from Repository data.

Analytics never modify trading decisions.

---

# Stage 12 — Lifecycle Completion

The request is considered complete when:

- Position reaches its terminal state
- Repository has been updated
- Analytics have been refreshed
- Final events have been published

The lifecycle is now closed.

---

# Event Timeline

Every request produces an immutable sequence of events.

Example:

```
Signal Received

↓

Signal Validated

↓

Position Evaluated

↓

Risk Approved

↓

Execution Planned

↓

Broker Submitted

↓

Broker Acknowledged

↓

Order Filled

↓

Position Updated

↓

Trade Closed

↓

Repository Updated

↓

Analytics Updated
```

---

# Request State Machine

```
RECEIVED

↓

VALIDATED

↓

POSITION_READY

↓

RISK_APPROVED

↓

EXECUTION_READY

↓

SUBMITTED

↓

FILLED

↓

POSITION_UPDATED

↓

COMPLETED
```

Possible failure states:

```
REJECTED

CANCELLED

FAILED

EXPIRED
```

---

# Module Ownership

| Stage | Owner |
|--------|-------|
| Signal Reception | Strategy Engine |
| Validation | Strategy Engine |
| Position Evaluation | Position Manager |
| Risk Approval | Risk Engine |
| Execution Planning | Execution Engine |
| Broker Communication | Broker Connector |
| Position Updates | Position Manager |
| Persistence | Repository |
| Analytics | Analytics Engine |

Each stage has exactly one owner.

---

# Failure Handling

If any stage fails:

1. Record the failure event.
2. Stop processing unless recovery is supported.
3. Preserve audit information.
4. Return a structured response.
5. Notify the Health Monitor when applicable.

No failure should silently terminate a request.

---

# Guiding Principles

The GTAP request lifecycle follows these principles:

- Every request has a unique identifier.
- Every stage has one owner.
- Every decision is auditable.
- Every transition is deterministic.
- Every event is recorded.
- No module bypasses another.
- Repository remains the system of record.

---

# Relationship to Other Documents

This document complements:

- GTAP_SDS_Volume_I.md
- GTAP_System_Architecture.md
- GTAP_Glossary.md
- ADR-0001-Project-Foundation.md

Module specifications must align with the lifecycle defined here.

---

# Closing Statement

The GTAP Request Lifecycle defines the canonical path that every trading request follows through the platform.

Future enhancements may extend the lifecycle but should preserve the principles of deterministic processing, modular ownership, complete auditability, and risk-first execution established by the GTAP architecture.

---

**End of Document**