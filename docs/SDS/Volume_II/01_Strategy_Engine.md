# GTAP Software Design Specification

# Volume II

# 01 — Strategy Engine Specification

---

| Property | Value |
|----------|-------|
| Project | GTAP (Greedy Trading Automation Platform) |
| Module | Strategy Engine |
| Document ID | GTAP-SDS-VII-01 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | Stanley Enyinnaya |
| Depends On | GTAP Request Lifecycle, GTAP System Architecture |

---

# Table of Contents

1. Purpose
2. Scope
3. Responsibilities
4. Non-Responsibilities
5. Design Principles
6. Inputs
7. Outputs
8. Public Interface
9. Internal Processing Pipeline
10. State Machine
11. Validation Rules
12. Duplicate Detection
13. Data Ownership
14. Error Handling
15. Logging
16. Performance Requirements
17. Configuration
18. Security Considerations
19. Acceptance Criteria
20. Future Enhancements

---

# 1. Purpose

The Strategy Engine is the entry point into GTAP.

Its responsibility is to receive trading requests from external strategies, validate them, normalize them into GTAP's internal format, and forward valid signals to the Position Manager.

The Strategy Engine does **not** decide whether a trade should execute.

---

# 2. Scope

The Strategy Engine is responsible for:

- Receiving webhook requests
- Parsing payloads
- Schema validation
- Duplicate detection
- Strategy authorization
- Symbol validation
- Signal normalization
- Event creation
- Request ID generation
- Publishing validated signals

---

# 3. Responsibilities

The Strategy Engine SHALL:

✓ Receive incoming webhook requests

✓ Validate payload structure

✓ Validate required fields

✓ Reject malformed requests

✓ Normalize symbols

✓ Assign Request IDs

✓ Timestamp requests

✓ Verify enabled strategies

✓ Publish validated signals

✓ Generate audit events

---

# 4. Non-Responsibilities

The Strategy Engine SHALL NOT:

✗ Evaluate account risk

✗ Determine position sizing

✗ Submit broker orders

✗ Modify positions

✗ Communicate with broker APIs

✗ Calculate profit/loss

✗ Persist execution records

Those responsibilities belong to downstream engines.

---

# 5. Design Principles

The Strategy Engine follows these principles:

• Stateless request processing

• Deterministic outputs

• Fail fast

• Immutable inputs

• Idempotent processing

• Interface-first communication

• Complete auditability

---

# 6. Inputs

Primary input:

Incoming webhook payload.

Example:

```json
{
  "strategy":"Greedy Strategy",
  "symbol":"MES",
  "action":"BUY",
  "quantity":2,
  "price":6325.75,
  "stop":6320.75,
  "target":6335.75,
  "timestamp":"2026-07-20T14:30:01Z"
}
```

Supported sources include:

- TradingView
- REST API
- Simulation Engine
- Future AI Engine

---

# 7. Outputs

The Strategy Engine produces exactly one of two outputs.

## Accepted Signal

```
ValidatedSignal
```

Forwarded to Position Manager.

---

## Rejected Signal

```
ValidationError
```

Returned immediately.

Processing stops.

---

# 8. Public Interface

### Input

```
receive_signal(payload)
```

Returns

```
StrategyResult
```

Example:

```
SUCCESS

↓

ValidatedSignal
```

or

```
FAILURE

↓

ValidationError
```

The interface should remain stable regardless of internal implementation.

---

# 9. Internal Processing Pipeline

Incoming Request

↓

Parse JSON

↓

Validate Schema

↓

Validate Required Fields

↓

Validate Strategy

↓

Validate Symbol

↓

Validate Timestamp

↓

Duplicate Detection

↓

Normalize Data

↓

Assign Request ID

↓

Generate Event

↓

Publish Signal

---

# 10. State Machine

```
RECEIVED

↓

PARSING

↓

VALIDATING

↓

NORMALIZING

↓

READY

↓

PUBLISHED
```

Failure states:

```
INVALID

DUPLICATE

UNAUTHORIZED

EXPIRED

FAILED
```

Every request reaches exactly one terminal state.

---

# 11. Validation Rules

The Strategy Engine validates:

## Payload

- JSON syntax
- Required fields
- Data types

---

## Strategy

- Enabled
- Authorized
- Supported version

---

## Symbol

Examples:

MES

MNQ

ES

NQ

Unknown symbols are rejected.

---

## Quantity

Must satisfy:

- integer
- greater than zero
- below configured maximum

---

## Timestamp

Reject if:

- missing
- invalid
- expired
- future beyond configured tolerance

---

## Action

Allowed:

BUY

SELL

EXIT

REDUCE

REVERSE

---

# 12. Duplicate Detection

Duplicate requests are rejected.

Detection may use:

- Request ID
- Strategy ID
- Timestamp
- Hash of payload
- Configurable replay window

Rejected duplicates generate an audit event but never continue through the pipeline.

---

# 13. Data Ownership

The Strategy Engine owns:

- Incoming request
- Normalized signal
- Validation result
- Request metadata

Ownership transfers to Position Manager only after successful publication.

---

# 14. Error Handling

Every error returns:

- Error Code
- Error Message
- Timestamp
- Request ID
- Strategy Name

Example codes:

S001 Invalid JSON

S002 Missing Field

S003 Unknown Strategy

S004 Unsupported Symbol

S005 Duplicate Request

S006 Timestamp Invalid

S007 Unauthorized Strategy

---

# 15. Logging

Every request generates structured logs.

Minimum events:

- Request Received
- Parsing Started
- Validation Passed
- Validation Failed
- Duplicate Detected
- Signal Published

Sensitive information must never appear in logs.

---

# 16. Performance Requirements

Target metrics:

Webhook parsing:

<10 ms

Validation:

<15 ms

Normalization:

<5 ms

Average engine latency:

<25 ms

Throughput:

≥100 requests/second

No blocking operations should occur during request validation.

---

# 17. Configuration

Configurable parameters include:

```
enabled_strategies

allowed_symbols

duplicate_window_seconds

max_quantity

max_clock_skew

supported_actions

logging_level
```

Business rules must remain configurable.

---

# 18. Security Considerations

Incoming requests should support:

- API authentication
- HMAC signature verification
- IP allowlist
- TLS encryption
- Rate limiting
- Payload size limits

The engine must reject unauthenticated or tampered requests.

---

# 19. Acceptance Criteria

The Strategy Engine is considered complete when:

✓ Valid requests become Validated Signals.

✓ Invalid payloads are rejected.

✓ Duplicate requests never propagate.

✓ Request IDs are unique.

✓ Structured logs exist for every request.

✓ Configuration changes require no code modification.

✓ Average processing latency meets performance targets.

---

# 20. Future Enhancements

Potential enhancements include:

- Multiple simultaneous strategy sources
- Strategy version negotiation
- AI signal ingestion
- Event bus integration
- Signal priority queues
- Dynamic schema validation
- Distributed ingestion
- Kafka/NATS support
- Multi-region failover

These enhancements should preserve the Strategy Engine's responsibility as a pure ingestion and normalization component.

---

# Appendix A — Engine Contract

### Consumes

External trading requests.

### Produces

Validated GTAP Signals.

### Owns

Signal validation.

### Does Not Own

Risk evaluation, execution, broker communication, position management, or analytics.

---

# Closing Statement

The Strategy Engine serves as the secure, deterministic gateway into GTAP. Its purpose is not to determine whether a trade is good or profitable, but to ensure that every request entering the platform is authentic, well-formed, normalized, traceable, and ready for downstream processing. By enforcing strict validation and maintaining clear ownership boundaries, the Strategy Engine establishes the foundation for a reliable, auditable, and extensible trading platform.

---

**End of Document**