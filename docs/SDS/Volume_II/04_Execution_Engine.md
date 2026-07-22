# GTAP Software Design Specification

# Volume II

# 04 — Execution Engine Specification

---

| Property | Value |
|----------|-------|
| Project | GTAP (Greedy Trading Automation Platform) |
| Module | Execution Engine |
| Document ID | GTAP-SDS-VII-04 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | Stanley Enyinnaya |
| Depends On | Risk Engine |
| Criticality | HIGH |

---

# Table of Contents

1. Purpose
2. Scope
3. Responsibilities
4. Non-Responsibilities
5. Design Philosophy
6. Inputs
7. Outputs
8. Execution Workflow
9. Order Lifecycle
10. Order State Machine
11. Retry Policy
12. Partial Fill Management
13. Failure Handling
14. Data Ownership
15. Logging & Audit
16. Performance
17. Configuration
18. Recovery
19. Acceptance Criteria
20. Future Enhancements

---

# 1. Purpose

The Execution Engine converts approved trading decisions into executable broker instructions.

It is responsible for creating, tracking, monitoring, and completing the lifecycle of every order submitted to a broker.

The Execution Engine assumes that every request has already passed validation and risk evaluation.

---

# 2. Scope

The Execution Engine manages:

- Order creation
- Order submission requests
- Order tracking
- Retry handling
- Timeout detection
- Partial fills
- Order completion
- Order cancellation
- Execution status publishing

---

# 3. Responsibilities

The Execution Engine SHALL:

✓ Build execution requests

✓ Assign Execution IDs

✓ Submit requests to Broker Connector

✓ Track execution progress

✓ Handle retries

✓ Detect timeouts

✓ Manage partial fills

✓ Publish execution events

✓ Maintain execution state

---

# 4. Non-Responsibilities

The Execution Engine SHALL NOT:

✗ Evaluate strategy quality

✗ Evaluate risk

✗ Calculate PnL

✗ Manage positions

✗ Communicate directly with broker APIs

Those functions belong to other engines.

---

# 5. Design Philosophy

The Execution Engine follows these principles:

• Reliability over speed

• Idempotent execution

• One execution owner

• Explicit state transitions

• Immutable execution history

• Broker-independent operation

---

# 6. Inputs

Consumes:

Risk Decision

Execution Plan

Position Context

Account Context

Configuration

---

# 7. Outputs

Produces:

Execution Request

Execution Status

Execution Events

Execution Result

---

Possible terminal results:

SUCCESS

FAILED

CANCELLED

EXPIRED

REJECTED

---

# 8. Execution Workflow

Approved Trade

↓

Generate Execution ID

↓

Build Broker Order

↓

Validate Order

↓

Submit to Broker Connector

↓

Wait for Broker Response

↓

Monitor Order

↓

Complete Execution

↓

Publish Events

↓

Notify Repository

---

# 9. Order Lifecycle

```
NEW

↓

READY

↓

SUBMITTED

↓

ACKNOWLEDGED

↓

WORKING

↓

FILLED

↓

COMPLETED
```

Alternative paths:

```
WORKING

↓

PARTIALLY_FILLED

↓

WORKING
```

or

```
WORKING

↓

CANCELLED
```

or

```
WORKING

↓

REJECTED
```

---

# 10. Order State Machine

Allowed transitions:

NEW → READY

READY → SUBMITTED

SUBMITTED → ACKNOWLEDGED

ACKNOWLEDGED → WORKING

WORKING → PARTIALLY_FILLED

PARTIALLY_FILLED → FILLED

FILLED → COMPLETED

WORKING → CANCELLED

WORKING → REJECTED

WORKING → EXPIRED

Invalid transitions must be rejected.

---

# 11. Retry Policy

Retry is permitted only for transient failures.

Examples:

✓ Temporary network interruption

✓ Broker timeout

✓ Gateway unavailable

Retries are NOT permitted for:

✗ Risk rejection

✗ Invalid order

✗ Authentication failure

✗ Symbol rejection

Each retry receives:

Retry Number

Timestamp

Reason

Maximum retry count is configurable.

---

# 12. Partial Fill Management

Partial fills remain active until:

Remaining Quantity = 0

or

Order Cancelled

or

Order Expired

Each fill is recorded individually.

Average fill price is recalculated after every fill.

---

# 13. Failure Handling

Failure categories:

Execution Failure

Communication Failure

Broker Rejection

Timeout

Duplicate Submission

Unexpected Exception

Every failure produces:

Execution Event

Structured Error

Audit Record

Health Notification (when applicable)

---

# 14. Data Ownership

The Execution Engine owns:

Execution ID

Execution Status

Execution Timeline

Retry History

Order Progress

Ownership ends when execution reaches a terminal state.

---

# 15. Logging & Audit

Minimum events:

Execution Created

Submitted

Acknowledged

Retry Started

Retry Completed

Partial Fill

Filled

Cancelled

Rejected

Completed

Each log contains:

Execution ID

Request ID

Order ID

Timestamp

Latency

Broker Status

---

# 16. Performance

Target metrics:

Execution creation:

<2 ms

Order construction:

<3 ms

Internal processing:

<5 ms

Maximum internal latency:

<10 ms

Broker latency is measured separately.

---

# 17. Configuration

Configurable settings:

maximum_retries

retry_delay

execution_timeout

allow_partial_fills

cancel_on_timeout

default_order_type

default_time_in_force

---

# 18. Recovery

After restart:

Load Active Executions

↓

Reconnect Broker

↓

Request Open Orders

↓

Reconcile State

↓

Resume Monitoring

Execution recovery must never duplicate broker orders.

---

# 19. Acceptance Criteria

The Execution Engine is complete when:

✓ Approved trades become broker execution requests.

✓ Every execution has a unique Execution ID.

✓ Order state transitions follow the documented state machine.

✓ Retry logic respects policy.

✓ Partial fills are tracked correctly.

✓ Recovery restores in-flight executions safely.

✓ Every execution is fully auditable.

---

# 20. Future Enhancements

Future versions may support:

- Smart order routing

- Multi-broker execution

- Iceberg orders

- TWAP/VWAP execution

- Execution algorithms

- Advanced order types

- Portfolio execution

- Cross-market execution

- Low-latency execution mode

These enhancements must preserve the engine's responsibility as the owner of execution state and workflow.

---

# Appendix A — Engine Contract

Consumes:

Approved execution requests from the Risk Engine.

Produces:

Broker-ready execution requests and execution state updates.

Owns:

Execution lifecycle.

Does Not Own:

Strategy validation

Risk evaluation

Position management

Broker API implementation

Analytics

---

# Closing Statement

The Execution Engine is responsible for the disciplined conversion of approved trading decisions into broker-executable orders. By isolating execution workflow from business logic, GTAP ensures that order handling remains reliable, deterministic, recoverable, and fully auditable, regardless of broker implementation or market conditions.

---

**End of Document**