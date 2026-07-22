# GTAP Software Design Specification

# Volume II

# 02 — Position Manager Specification

---

| Property | Value |
|----------|-------|
| Project | GTAP (Greedy Trading Automation Platform) |
| Module | Position Manager |
| Document ID | GTAP-SDS-VII-02 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | Stanley Enyinnaya |
| Depends On | Strategy Engine |

---

# Table of Contents

1. Purpose
2. Scope
3. Responsibilities
4. Non-Responsibilities
5. Design Principles
6. Inputs
7. Outputs
8. Position State Model
9. Position Lifecycle
10. Position Decision Engine
11. Position Rules
12. Position State Machine
13. Data Ownership
14. Error Handling
15. Logging
16. Performance
17. Configuration
18. Recovery & Synchronization
19. Acceptance Criteria
20. Future Enhancements

---

# 1. Purpose

The Position Manager is the authoritative owner of all active trading positions within GTAP.

It determines how an incoming validated signal affects the current portfolio state before any risk evaluation or order execution occurs.

The Position Manager ensures that GTAP always maintains a consistent, deterministic view of market exposure.

---

# 2. Scope

The Position Manager is responsible for:

- Tracking all active positions
- Evaluating incoming signals against current exposure
- Detecting adds, reductions, reversals, and exits
- Maintaining average entry price
- Maintaining realized and unrealized PnL
- Publishing updated position state
- Synchronizing with broker positions when required

---

# 3. Responsibilities

The Position Manager SHALL:

✓ Own the current position state

✓ Determine whether a signal creates, modifies, reduces, reverses, or closes a position

✓ Maintain average entry price

✓ Maintain quantity

✓ Maintain position status

✓ Detect invalid transitions

✓ Publish position updates

---

# 4. Non-Responsibilities

The Position Manager SHALL NOT:

✗ Evaluate account risk

✗ Approve or reject trades based on risk

✗ Submit broker orders

✗ Communicate directly with broker APIs

✗ Calculate strategy performance metrics

---

# 5. Design Principles

The Position Manager follows these principles:

- Single source of truth
- Deterministic state transitions
- Immutable event history
- Explicit ownership
- Broker-independent logic
- Event-driven updates

---

# 6. Inputs

Primary input:

ValidatedSignal

Example:

```json
{
  "request_id": "REQ-20260720-00154",
  "symbol": "MES",
  "action": "BUY",
  "quantity": 2,
  "price": 6325.75
}
```

Additional inputs include:

- Existing Position State
- Repository Records
- Broker Synchronization Events

---

# 7. Outputs

The Position Manager produces a Position Decision.

Possible outputs:

- OPEN_POSITION
- ADD_POSITION
- REDUCE_POSITION
- CLOSE_POSITION
- REVERSE_POSITION
- NO_ACTION

Each decision is forwarded to the Risk Engine.

---

# 8. Position State Model

Each position contains:

Position ID

Account

Strategy

Symbol

Direction

Quantity

Average Entry

Current Price

Realized PnL

Unrealized PnL

Status

Last Update Time

Version Number

---

# 9. Position Lifecycle

```
FLAT

↓

OPEN

↓

ADD

↓

REDUCE

↓

CLOSE

↓

ARCHIVED
```

A reversal is treated as:

```
Close Existing Position

↓

Open New Position
```

Never modify direction in-place.

---

# 10. Position Decision Engine

For every incoming signal, the Position Manager evaluates:

Current Position

↓

Incoming Action

↓

Requested Quantity

↓

Projected Position

↓

State Transition

↓

Publish Decision

---

Decision examples:

Flat + BUY

↓

OPEN_POSITION

---

Long + BUY

↓

ADD_POSITION

---

Long + SELL (Partial)

↓

REDUCE_POSITION

---

Long + SELL (Full)

↓

CLOSE_POSITION

---

Long + SELL (Larger than Position)

↓

REVERSE_POSITION

---

# 11. Position Rules

## One Position Per Symbol Per Strategy

Only one active position may exist for the same:

- Account
- Strategy
- Symbol

---

## Average Entry Price

Adding contracts recalculates average entry.

Reducing contracts does not.

---

## Direction

Allowed values:

LONG

SHORT

FLAT

---

## Quantity

Must never become negative.

---

## Reversal

Always represented as:

Close

↓

Open

Never as a direct direction change.

---

# 12. Position State Machine

```
FLAT

↓

OPEN

↓

ADDING

↓

OPEN

↓

REDUCING

↓

OPEN

↓

CLOSING

↓

FLAT
```

Alternative branch:

```
OPEN

↓

REVERSING

↓

FLAT

↓

OPEN
```

Terminal states:

ARCHIVED

ERROR

---

# 13. Data Ownership

The Position Manager owns:

- Position State
- Quantity
- Average Entry
- Position Direction
- Position Version

Ownership transfers only through published events.

---

# 14. Error Handling

Example error codes:

P001 Position Not Found

P002 Invalid Transition

P003 Negative Quantity

P004 Duplicate Position

P005 Synchronization Failure

P006 Invalid Average Price

Errors terminate the position update and are recorded for audit.

---

# 15. Logging

Minimum events:

- Position Created
- Position Updated
- Position Reduced
- Position Closed
- Position Reversed
- Synchronization Started
- Synchronization Completed
- Synchronization Failed

Each log entry includes:

- Request ID
- Position ID
- Strategy
- Symbol
- Timestamp

---

# 16. Performance

Target metrics:

Position lookup:

<2 ms

Position evaluation:

<5 ms

Decision generation:

<5 ms

Maximum latency:

<10 ms

Supports:

10,000+ concurrent tracked positions

---

# 17. Configuration

Configurable parameters:

```
allow_position_adds

allow_reversals

maximum_position_size

maximum_contracts

sync_interval

position_timeout

auto_archive_closed_positions
```

---

# 18. Recovery & Synchronization

The Position Manager supports recovery after restart.

Recovery process:

Load Repository

↓

Load Active Positions

↓

Request Broker Snapshot

↓

Compare States

↓

Resolve Differences

↓

Publish Synchronization Report

Repository remains the primary system of record.

Broker synchronization resolves discrepancies but does not overwrite historical events.

---

# 19. Acceptance Criteria

The Position Manager is complete when:

✓ Every valid signal results in the correct position decision

✓ Position state remains internally consistent

✓ Average entry calculations are accurate

✓ Reversals are represented as close then open

✓ Position history is immutable

✓ Recovery restores active positions correctly

✓ Performance targets are met

---

# 20. Future Enhancements

Future versions may support:

- Portfolio-level positions
- Multi-account aggregation
- Cross-strategy netting
- Multi-leg options
- Spread positions
- Portfolio hedging
- Multi-broker synchronization
- Distributed state replication

These enhancements must preserve the Position Manager as the single authoritative owner of position state.

---

# Appendix A — Engine Contract

Consumes:

Validated Signals

Produces:

Position Decisions

Owns:

Current Position State

Does Not Own:

Risk Evaluation

Broker Communication

Order Execution

Analytics

---

# Closing Statement

The Position Manager is the authoritative representation of GTAP's market exposure.

Its role is to ensure that every change in exposure is explicit, deterministic, auditable, and recoverable. By separating position state management from risk evaluation and execution, GTAP maintains clear ownership boundaries and ensures that downstream engines always operate from a trusted and consistent view of the portfolio.

---

**End of Document**