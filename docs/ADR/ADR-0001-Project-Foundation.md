# ADR-0001 — GTAP Project Foundation

---

| Property | Value |
|----------|-------|
| ADR | 0001 |
| Title | GTAP Project Foundation |
| Status | Accepted |
| Date | July 2026 |
| Author | Stanley Enyinnaya |
| Related Documents | GTAP_SDS_Volume_I.md |

---

# Status

**Accepted**

This Architecture Decision Record establishes the foundational architectural principles for the GTAP platform.

All future architectural decisions should align with the principles defined in this document unless superseded by a later ADR.

---

# Context

The project initially began as a lightweight TradingView webhook bot responsible for receiving alerts and forwarding orders to a broker.

As additional capabilities were introduced—including position management, risk validation, analytics, strategy health monitoring, and execution management—it became clear that the project had evolved beyond a simple automation script.

The original architecture no longer reflected the long-term vision.

A new architectural direction was required.

---

# Decision

The project shall evolve into a modular software platform named:

> **GTAP — Greedy Trading Automation Platform**

GTAP shall be designed as an extensible trading platform rather than a single-purpose trading bot.

Trading strategies are considered replaceable components that operate within a standardized execution framework.

The platform architecture shall prioritize:

- Modularity
- Reliability
- Auditability
- Testability
- Extensibility

over rapid feature development.

---

# Architectural Principles

The following principles are adopted as permanent architectural guidelines.

## 1. Platform Before Strategy

Strategies may change.

The platform should not.

GTAP is designed so that strategies can be replaced without redesigning the execution system.

---

## 2. Documentation Before Implementation

Every major module shall have an approved specification before implementation begins.

Documentation is considered part of the software.

Code without documentation is considered incomplete.

---

## 3. Interface-Driven Design

Modules communicate only through documented interfaces.

No module should directly depend on another module's internal implementation.

This minimizes coupling and improves maintainability.

---

## 4. Risk-First Execution

Every order must pass through the Risk Engine before reaching any broker.

No execution path shall bypass risk validation.

Capital protection takes priority over opportunity.

---

## 5. Event-Driven Architecture

GTAP is built around events rather than tightly coupled workflows.

Examples include:

- Signal Received
- Risk Approved
- Order Submitted
- Order Filled
- Position Closed

Each event should be recorded for audit and analytics purposes.

---

## 6. Single Responsibility

Each module owns one primary responsibility.

Examples:

| Module | Responsibility |
|----------|----------------|
| Strategy Engine | Signal Processing |
| Position Manager | Position Lifecycle |
| Risk Engine | Risk Validation |
| Execution Engine | Order Execution |
| Broker Connector | Broker Communication |
| Repository | Persistent Storage |
| Analytics Engine | Performance Analysis |

Responsibilities should not overlap.

---

## 7. Configuration Over Hardcoding

Behavior should be controlled through configuration whenever practical.

Examples include:

- Risk limits
- Trading sessions
- Broker settings
- Strategy parameters
- Position limits

Hardcoded business rules should be avoided.

---

## 8. Deterministic Processing

Given identical inputs, GTAP must produce identical outputs.

Hidden behavior and non-deterministic logic should be avoided unless explicitly documented.

---

## 9. Observability

Every significant decision should be measurable.

GTAP should expose sufficient logging, metrics, and event history to reconstruct trading activity after execution.

---

## 10. Incremental Evolution

GTAP shall evolve through controlled architectural iterations.

Large-scale rewrites should be avoided whenever possible.

Existing modules should be improved through refactoring while preserving documented interfaces.

---

# Initial Technology Decisions

The following implementation technologies are accepted for Version 1.

| Area | Decision |
|-------|----------|
| Language | Python |
| Signal Source | TradingView Webhooks |
| Initial Database | SQLite |
| Broker Integration | Tradovate |
| Version Control | Git |
| Documentation | Markdown |
| Testing | Pytest |

These choices may be revisited through future ADRs.

---

# Consequences

## Positive

- Clear architectural direction.
- Easier onboarding of future contributors.
- Reduced coupling between modules.
- Better long-term maintainability.
- Independent module testing.
- Simplified strategy replacement.
- Consistent engineering practices.

---

## Negative

- Higher upfront documentation effort.
- More design work before implementation.
- Additional maintenance of specifications.

These trade-offs are considered acceptable in exchange for improved software quality and long-term maintainability.

---

# Alternatives Considered

## Continue as a TradingView Webhook Bot

Rejected.

Reason:

The project scope has exceeded the capabilities and maintainability of a single-purpose webhook application.

---

## Build Around a Single Strategy

Rejected.

Reason:

Strategies evolve over time.

The platform should remain stable while strategies are replaced or improved.

---

## Monolithic Architecture

Rejected.

Reason:

A monolithic design would tightly couple execution, risk, broker communication, and analytics, making future enhancements more difficult.

---

# Related Documents

- GTAP_SDS_Volume_I.md
- Position Manager Specification
- Risk Engine Specification
- Execution Engine Specification

---

# Future ADRs

Examples of future Architecture Decision Records include:

- ADR-0002 — Repository Architecture
- ADR-0003 — Event Bus Design
- ADR-0004 — Risk Engine Design
- ADR-0005 — Broker Abstraction Layer
- ADR-0006 — Analytics Pipeline
- ADR-0007 — Database Migration Strategy
- ADR-0008 — Multi-Broker Support
- ADR-0009 — Cloud Deployment Architecture

---

# Approval

This Architecture Decision Record establishes the foundational architectural direction for GTAP.

Future architectural decisions should reference this document before introducing new patterns, technologies, or structural changes.

Any modification to these principles should be documented through a subsequent ADR rather than altering this record directly.

---

**Decision:** Accepted

**Effective Date:** July 2026

**Supersedes:** None

**Superseded By:** None