# 🚀 Greedy Trading Automation Platform (GTAP)

> **From Strategy to Execution.**

A modular, production-oriented trading automation platform built with **Python**, **FastAPI**, and a layered execution architecture that transforms TradingView strategies into validated, auditable, testable, and eventually live-executable trading workflows.

GTAP is designed to bridge the gap between strategy development and real-world execution by introducing structured validation, risk management, execution services, persistence, and broker abstraction before any order reaches a live brokerage.

---

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Persistent_Storage-blue.svg)
![Status](https://img.shields.io/badge/Status-Active_Development-success.svg)
![Tests](https://img.shields.io/badge/Tests-17_Passing-success.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

---

# Table of Contents

- Overview
- Why GTAP?
- Current Features
- System Architecture
- Design Principles
- Project Structure
- Core Components
- Execution Database
- REST API
- TradingView Integration
- Installation
- Configuration
- Running GTAP
- Automated Testing
- Signal Replay
- Deployment
- Roadmap
- Future Vision
- License

---

# Overview

Greedy Trading Automation Platform (GTAP) is a modular trading infrastructure designed to safely automate TradingView strategies while maintaining complete visibility into every stage of the execution pipeline.

Rather than allowing TradingView alerts to communicate directly with a live broker, GTAP introduces multiple layers of validation and auditing before execution occurs.

Every signal is treated as an event that can be:

- Validated
- Risk checked
- Executed
- Persisted
- Audited
- Replayed
- Analyzed

This architecture makes the platform significantly safer than direct webhook-to-broker implementations while providing complete traceability for every trading decision.

GTAP currently executes against a Mock Broker for forward testing and validation. The architecture has been intentionally designed so that the Mock Broker can later be replaced with a live broker integration such as Tradovate with minimal changes to the execution pipeline.

---

# Why GTAP?

Most TradingView automation projects follow a simple pattern:

TradingView

↓

Webhook

↓

Broker

While straightforward, this approach introduces several challenges:

- No centralized risk management
- No execution audit trail
- Limited error handling
- Difficult debugging
- Poor historical visibility
- Tight coupling between TradingView and the broker

GTAP was created to solve these problems by introducing a structured execution pipeline between TradingView and the brokerage layer.

Instead of treating TradingView alerts as executable orders, GTAP treats them as requests that must pass through a series of validation stages before execution.

This architecture enables:

- Controlled execution
- Broker independence
- Better testing
- Improved reliability
- Future scalability
- Complete observability

---

# Current Features

## TradingView Integration

- TradingView Strategy Alerts
- Indicator Alerts
- JSON Webhook Processing
- Signal Normalization

---

## FastAPI REST Server

- Secure webhook endpoint
- REST API
- Health monitoring
- Execution APIs
- Statistics endpoints

---

## Execution Engine

- Modular execution service
- Broker abstraction layer
- Position synchronization
- Order lifecycle management

---

## Risk Engine

- Source validation
- Symbol validation
- Timeframe validation
- Position limits
- Daily loss protection
- Trading enable/disable controls

---

## Mock Broker

Supports realistic paper execution including:

- Accounts
- Orders
- Fills
- Positions

Designed to mirror the behavior of a real broker while remaining completely offline for safe testing.

---

## Execution Repository

Persistent storage for:

- Orders
- Fills
- Positions
- Risk Events
- Audit Events

using a dedicated SQLite execution database.

---

## Signal Replay

Replay historical TradingView signals through the complete execution pipeline to validate changes before live deployment.

---

## Automated Testing

Current test coverage includes:

- Repository testing
- Risk Engine testing
- Mock Broker testing
- Execution Service testing
- Persistence testing
- Integration testing

Current Status:

✅ 17 Passing Tests

---

# Project Philosophy

GTAP is built around one fundamental principle:

> **Every trading decision should be transparent, reproducible, and auditable.**

Rather than connecting TradingView directly to a brokerage account, GTAP creates a structured execution workflow that validates every incoming signal, evaluates risk, executes against a broker abstraction, records every event, and maintains a complete audit history.

This layered architecture provides confidence during forward testing while making the transition to live execution significantly safer.

---

# Current Development Status

| Component | Status |
|-----------|--------|
| TradingView Integration | ✅ Complete |
| FastAPI API | ✅ Complete |
| Signal Normalization | ✅ Complete |
| Risk Engine | ✅ Complete |
| Execution Service | ✅ Complete |
| Mock Broker | ✅ Complete |
| Execution Repository | ✅ Complete |
| SQLite Persistence | ✅ Complete |
| Audit Trail | ✅ Complete |
| Signal Replay | ✅ Complete |
| REST API | ✅ Complete |
| Automated Tests | ✅ Complete |
| Dashboard | 🚧 Planned |
| Tradovate Integration | 🚧 Planned |
| Performance Analytics | 🚧 Planned |
| AI Trading Coach | 🚧 Planned |

---

# High-Level Architecture

```text
                 TradingView Strategy
                         │
                         ▼
                 TradingView Alert
                         │
                         ▼
                  FastAPI Webhook
                         │
                         ▼
                Signal Normalization
                         │
                         ▼
                 Execution Service
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
    Risk Engine                   Mock Broker
          │                             │
          └──────────────┬──────────────┘
                         ▼
              Execution Repository
                         │
      ┌──────────┬──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼
    Orders     Fills    Positions   Audit Log
```

---

**Next:** Part 2 – Project Structure & Core Components

We'll dive into every folder and every major class in the project, explaining exactly how they work together and why the architecture is organized the way it is.

# Project Structure

GTAP follows a layered architecture that separates responsibilities into independent modules. Each layer has a single responsibility, making the platform easier to test, maintain, and extend.

```
greedy-trading-automation-platform/
│
├── broker/
│   ├── broker_interface.py
│   ├── mock_broker.py
│   └── models.py
│
├── models/
│   ├── execution.py
│   ├── signals.py
│   └── ...
│
├── repository/
│   └── execution_repository.py
│
├── services/
│   └── execution_service.py
│
├── tests/
│   ├── test_execution_persistence.py
│   ├── test_mock_broker.py
│   ├── test_risk_engine.py
│   ├── ...
│
├── tools/
│   └── signal_replay.py
│
├── broker_app.py
├── main.py
├── risk_engine.py
├── config.py
├── requirements.txt
├── README.md
└── execution.db
```

> **Note:** The exact folder structure may evolve as the platform grows, but the architectural layers remain the same.

---

# Core Architecture

GTAP is intentionally designed using a layered architecture.

Each layer performs one responsibility and communicates only with the layer directly above or below it.

```
TradingView

↓

FastAPI

↓

Execution Service

↓

Risk Engine

↓

Broker

↓

Repository

↓

SQLite
```

This separation allows each component to evolve independently without affecting the rest of the platform.

---

# Core Components

## TradingView

TradingView is responsible for generating trading signals.

GTAP currently supports:

- Strategy Alerts
- Indicator Alerts
- JSON Webhooks

TradingView never communicates directly with a broker.

Instead, every alert becomes a request that must pass through GTAP's validation pipeline.

---

## FastAPI Webhook Layer

File:

```
main.py
```

Responsibilities:

- Receive TradingView alerts
- Validate webhook secrets
- Parse incoming payloads
- Normalize strategy and indicator signals
- Forward requests into the execution pipeline

The FastAPI layer intentionally contains very little business logic.

Its responsibility is simply to receive requests and hand them off to the Execution Service.

---

## Execution Service

File:

```
services/execution_service.py
```

The Execution Service acts as the orchestration layer for the platform.

It coordinates the interaction between:

- Risk Engine
- Broker
- Repository

Responsibilities include:

- Receive normalized trading signals
- Request risk evaluation
- Submit approved orders
- Synchronize positions
- Persist execution history
- Generate audit events

The Execution Service contains the application's primary business workflow.

Every trading request passes through this component.

---

## Risk Engine

File:

```
risk_engine.py
```

The Risk Engine determines whether a signal is allowed to proceed.

Current validations include:

- Approved signal source
- Approved trading symbol
- Approved timeframe
- Maximum contract limits
- Daily loss protection
- Trading enabled/disabled state

If any validation fails, execution immediately stops and the rejection is recorded as a Risk Event.

This keeps all execution decisions deterministic and fully auditable.

---

## Broker Layer

Directory:

```
broker/
```

GTAP communicates with brokers through an abstraction layer.

Current implementation:

```
Mock Broker
```

Future implementation:

```
Tradovate Broker
```

Because the Execution Service depends on a broker interface rather than a specific broker implementation, replacing the Mock Broker with Tradovate requires minimal changes.

This design follows the Dependency Inversion Principle.

---

## Mock Broker

Current implementation:

```
broker/mock_broker.py
```

The Mock Broker simulates realistic broker behavior while remaining completely offline.

Supported features:

- Accounts
- Orders
- Fills
- Positions

This allows developers to safely forward test trading strategies without risking real capital.

---

## Execution Repository

Directory:

```
repository/
```

The Execution Repository provides persistent storage for execution history.

Current tables include:

- execution_orders
- execution_fills
- execution_positions
- execution_risk_events
- execution_audit_events

The repository isolates database operations from the rest of the application.

This keeps SQL logic separate from business logic and simplifies testing.

---

## Signal Replay Engine

File:

```
tools/signal_replay.py
```

The replay engine allows historical TradingView signals to be processed through the complete execution pipeline.

Replay uses the exact same components as live execution:

TradingView Signal

↓

Execution Service

↓

Risk Engine

↓

Mock Broker

↓

Repository

This makes replay an excellent regression-testing tool before deploying new platform changes.

---

# Execution Lifecycle

Every signal follows the same lifecycle.

```
TradingView Alert

        │

        ▼

Webhook Received

        │

        ▼

Signal Validation

        │

        ▼

Risk Evaluation

        │

        ▼

Order Approved?

   ┌───────────────┐
   │               │
   │     YES       │
   │               │
   ▼               ▼
Execute         Reject
   │               │
   ▼               ▼
Persist       Risk Event
   │
   ▼
Audit Event
```

Because every branch is recorded, GTAP maintains a complete history of both successful executions and rejected signals.

---

# Design Principles

GTAP follows several software engineering principles.

## Separation of Concerns

Each module performs one responsibility.

Examples:

- FastAPI receives requests.
- Risk Engine validates.
- Broker executes.
- Repository persists.

---

## Dependency Injection

Execution Service does not create brokers.

Instead, a broker implementation is injected during application startup.

This allows Mock Broker and future live brokers to be swapped without modifying execution logic.

---

## Repository Pattern

Database access is isolated within the repository layer.

Advantages include:

- Easier testing
- Cleaner business logic
- Database independence
- Better maintainability

---

## Auditability

Every important decision generates an audit event.

This provides complete visibility into:

- Signal receipt
- Risk approval
- Risk rejection
- Order submission
- Order fills
- Position synchronization

No execution decision occurs without leaving a trace.

---

## Extensibility

GTAP is designed for future expansion.

Planned additions include:

- Tradovate Adapter
- Interactive Brokers Adapter
- Performance Dashboard
- Portfolio Analytics
- AI Trading Coach

These features can be added without redesigning the existing architecture.

# Execution Database

GTAP separates execution history from signal logging by using a dedicated execution database.

Current database:

```
execution.db
```

Unlike temporary in-memory objects, every important execution event is persisted for auditing, debugging, replay, and future analytics.

---

## Database Schema

```
execution.db

├── execution_orders
├── execution_fills
├── execution_positions
├── execution_risk_events
└── execution_audit_events
```

Each table represents a stage of the execution lifecycle.

---

## execution_orders

Stores every order submitted to the broker.

Typical fields include:

| Field | Description |
|--------|-------------|
| id | Internal order identifier |
| signal_id | Source signal |
| broker_order_id | Broker-generated order ID |
| symbol | Trading symbol |
| side | BUY / SELL |
| quantity | Number of contracts |
| status | Pending, Filled, Cancelled |
| created_at | Timestamp |

Purpose:

- Order history
- Broker reconciliation
- Replay validation
- Performance analysis

---

## execution_fills

Stores every completed execution.

Typical fields include:

| Field | Description |
|--------|-------------|
| id | Fill identifier |
| order_id | Associated order |
| symbol | Instrument |
| quantity | Filled quantity |
| fill_price | Execution price |
| filled_at | Fill timestamp |

Purpose:

- P&L calculations
- Slippage analysis
- Broker verification

---

## execution_positions

Tracks the platform's understanding of open positions.

Typical fields include:

| Field | Description |
|--------|-------------|
| symbol | Trading symbol |
| quantity | Current position size |
| average_price | Average entry |
| updated_at | Last synchronization |

Purpose:

- Position synchronization
- Risk evaluation
- Portfolio monitoring

---

## execution_risk_events

Stores every risk decision.

Examples:

- Source rejected
- Invalid timeframe
- Trading disabled
- Daily loss exceeded
- Position size exceeded

Purpose:

Every rejected trade becomes part of the permanent audit history.

This allows developers to answer questions like:

> Why wasn't this order executed?

without searching application logs.

---

## execution_audit_events

The audit log records every important system event.

Examples:

- Signal received
- Risk approved
- Risk rejected
- Order submitted
- Fill received
- Position updated

Unlike standard application logs, audit events describe business decisions rather than technical events.

---

# REST API

GTAP exposes a REST API for monitoring and interacting with the execution platform.

---

## Health

```
GET /broker/health
```

Returns platform health information.

Example response:

```json
{
  "status": "ok",
  "database": "execution.db",
  "broker": "MockBroker"
}
```

---

## Accounts

```
GET /broker/accounts
```

Returns broker account information.

---

## Positions

```
GET /broker/positions
```

Returns all open positions currently tracked by the broker.

---

## Orders

```
GET /broker/orders
```

Returns submitted broker orders.

---

## Execution Summary

```
GET /broker/execution-summary
```

Returns summary statistics for the execution database.

Example:

```json
{
    "orders": 15,
    "fills": 15,
    "positions": 1,
    "risk_events": 2,
    "audit_events": 48
}
```

Useful for quickly verifying platform activity.

---

## Execution Orders

```
GET /broker/execution-orders
```

Returns persisted execution orders.

---

## Execution Fills

```
GET /broker/execution-fills
```

Returns persisted fills.

---

## Risk Events

```
GET /broker/risk-events
```

Returns all rejected or blocked executions.

Useful for debugging strategy behavior.

---

## Audit Events

```
GET /broker/audit-events
```

Returns the chronological execution history.

This endpoint provides the complete business audit trail.

---

## Test Signal

```
POST /broker/test-signal
```

Injects a sample signal directly into the execution pipeline.

Useful for:

- Integration testing
- Development
- API verification

---

## Reset Broker

```
POST /broker/reset
```

Resets the Mock Broker state.

Execution history remains intact.

---

# TradingView Integration

GTAP accepts TradingView webhooks using JSON payloads.

TradingView never communicates directly with a broker.

Instead, alerts become execution requests processed by GTAP.

---

## Supported Alert Types

### Strategy Alerts

Generated from TradingView strategies using strategy placeholders.

Example:

```json
{
    "secret": "...",
    "source": "Greedy Futures Strategy",
    "order_action": "{{strategy.order.action}}",
    "order_contracts": "{{strategy.order.contracts}}",
    "order_price": "{{strategy.order.price}}",
    "position_size": "{{strategy.position_size}}",
    "symbol": "{{ticker}}",
    "timeframe": "{{interval}}",
    "exchange": "{{exchange}}",
    "timestamp": "{{time}}"
}
```

---

### Indicator Alerts

Generated from TradingView indicators.

Example:

```json
{
    "secret": "...",
    "source": "Zone Sweep Indicator",
    "action": "LONG",
    "symbol": "{{ticker}}",
    "price": "{{close}}",
    "timeframe": "{{interval}}",
    "exchange": "{{exchange}}",
    "timestamp": "{{time}}"
}
```

---

# Signal Normalization

TradingView strategies and indicators produce different payload formats.

GTAP converts both formats into a single normalized execution request.

Example:

Strategy payload

```
BUY
1 Contract
22500.25
```

↓

Normalized

```
Action: LONG
Symbol: MNQ1!
Price: 22500.25
Contracts: 1
```

This normalization ensures every downstream component processes identical objects regardless of signal source.

---

# End-to-End Execution Flow

The complete lifecycle of a trading signal is illustrated below.

```
TradingView

      │

      ▼

Webhook Received

      │

      ▼

Signal Normalization

      │

      ▼

Execution Service

      │

      ▼

Risk Engine

      │

      ▼

Approved?

   ┌───────────────┐
   │               │
   │     YES       │
   │               │
   ▼               ▼
Broker         Risk Event
   │
   ▼
Fill
   │
   ▼
Repository
   │
   ▼
Audit Trail
```

Every execution follows this identical pipeline, ensuring consistent behavior whether processing live alerts or replaying historical signals.

---

# Why Persistence Matters

Every decision made by GTAP is permanently recorded.

This enables:

- Complete auditability
- Trade replay
- Strategy debugging
- Historical analytics
- Performance reporting
- Compliance-style traceability

The platform is designed so that no execution decision occurs without leaving a permanent record.

This philosophy forms the foundation for future features such as live broker execution, performance dashboards, portfolio analytics, and AI-assisted trade review.

# Installation

GTAP is designed to be simple to install while remaining production-ready.

## Prerequisites

Before installing GTAP, ensure your environment includes:

- Python 3.11+
- Git
- SQLite (bundled with Python)
- TradingView account (for webhook alerts)

Recommended:

- Visual Studio Code
- Postman
- DB Browser for SQLite

---

## Clone the Repository

```bash
git clone https://github.com/<your-username>/greedy-trading-automation-platform.git

cd greedy-trading-automation-platform
```

---

## Create a Virtual Environment

Windows

```powershell
python -m venv venv

venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

GTAP uses environment variables for secrets and configuration.

Copy the template:

```bash
cp .env.example .env
```

Windows PowerShell

```powershell
copy .env.example .env
```

Example:

```text
WEBHOOK_SECRET=YOUR_SECRET_HERE
```

Never commit your `.env` file.

---

# Running GTAP

Start the FastAPI application.

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

Server:

```
http://localhost:8000
```

Swagger API Documentation:

```
http://localhost:8000/docs
```

OpenAPI Specification:

```
http://localhost:8000/openapi.json
```

---

# First-Time Verification

After startup, verify the application.

Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
    "status":"ok"
}
```

Then verify the Broker API.

```bash
curl http://localhost:8000/broker/health
```

Expected:

```json
{
    "status":"ok",
    "broker":"MockBroker"
}
```

If both endpoints respond successfully, GTAP is ready to receive TradingView alerts.

---

# Testing

GTAP includes automated unit and integration tests.

Run the complete suite:

```bash
python -m pytest -v
```

Current status:

```
17 Passed
0 Failed
```

---

## Test Coverage

Current automated tests validate:

✔ Mock Broker

✔ Risk Engine

✔ Execution Repository

✔ Execution Persistence

✔ Signal Replay

✔ API Integration

As the platform grows, additional coverage will be added for broker adapters, analytics, and AI-assisted trade review.

---

# Forward Testing Workflow

Current execution workflow:

```
TradingView

↓

Webhook

↓

Execution Service

↓

Risk Engine

↓

Mock Broker

↓

Execution Repository

↓

Review Results
```

No real trades are placed.

The Mock Broker enables safe forward testing while preserving the complete execution history for analysis.

---

# Signal Replay

Historical TradingView alerts can be replayed through the platform.

Replay follows the exact same execution pipeline used during live operation.

```
Historical Signals

↓

Replay Tool

↓

Execution Service

↓

Risk Engine

↓

Mock Broker

↓

Execution Repository
```

Replay is useful for:

- Regression testing

- Risk validation

- Performance verification

- Platform upgrades

---

# Deployment

GTAP can be deployed on any platform capable of running Python and FastAPI.

Common deployment targets include:

- Windows Server

- Ubuntu

- Docker

- Railway

- Render

- Azure

- AWS

- Google Cloud

Future releases will include Docker Compose and Kubernetes deployment examples.

---

# Security

GTAP has been designed with security in mind.

Current protections include:

- Webhook secret validation

- Structured request validation

- Risk-based execution controls

- Persistent audit logging

Recommended production practices:

- HTTPS only

- Reverse proxy (Nginx)

- Environment variables

- Firewall restrictions

- Database backups

---

# Logging

GTAP records multiple layers of execution history.

Current logging includes:

Application Logs

- FastAPI

Execution Logs

- Orders

- Fills

- Positions

Risk Logs

- Rejected Signals

Audit Logs

- Business Events

This layered logging model makes troubleshooting significantly easier than relying on application logs alone.

---

# Contributing

Contributions are welcome.

When contributing:

1. Fork the repository.

2. Create a feature branch.

3. Add automated tests.

4. Follow existing project structure.

5. Submit a Pull Request.

Major architectural changes should include documentation updates.

---

# Development Roadmap

## Phase 1 — Foundation ✅

- TradingView Integration

- FastAPI

- Signal Logging

---

## Phase 2 — Execution ✅

- Risk Engine

- Mock Broker

- Execution Service

---

## Phase 3 — Persistence ✅

- Execution Repository

- Audit Trail

- SQLite

---

## Phase 4 — Analytics 🚧

Planned:

- Performance Dashboard

- Equity Curve

- Trade Statistics

- Win Rate Analytics

- Drawdown Analysis

---

## Phase 5 — Live Trading 🚧

Planned:

- Tradovate Adapter

- Live Order Routing

- Position Synchronization

- Broker Reconciliation

---

## Phase 6 — Intelligence 🚧

Planned:

- AI Trade Coach

- Performance Suggestions

- Risk Optimization

- Behavioral Analysis

- Strategy Insights

---

# Long-Term Vision

GTAP is being built as a broker-agnostic trading automation platform.

The long-term architecture is intended to support multiple execution providers through interchangeable broker adapters.

Future architecture:

```
TradingView

      │

Execution Service

      │

Broker Interface

 ┌──────────┼──────────────┐

 ▼          ▼              ▼

Mock     Tradovate      Interactive Brokers

Broker     Adapter            Adapter
```

This design allows the execution pipeline to remain unchanged while new brokers are introduced.

---

# License

This project is licensed under the MIT License.

---

# Disclaimer

GTAP is provided for educational and research purposes.

Trading financial markets involves substantial risk.

The software does not guarantee profitability, and users are responsible for validating strategies before deploying them with real capital.

Always test thoroughly in simulated environments before enabling live execution.

---

# Acknowledgments

GTAP is the result of an iterative engineering process focused on building a transparent, modular, and production-oriented trading automation platform.

The project continues to evolve toward safe live execution, advanced analytics, and AI-assisted trading workflows.

---

> **Greedy Trading Automation Platform (GTAP)**  
> *From Strategy to Execution.*