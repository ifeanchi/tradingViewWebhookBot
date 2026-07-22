# GTAP Position Management Specification

**Document ID:** GTAP-PMS-001  
**Version:** 1.0 Draft  
**Status:** Proposed  
**Applies To:** GTAP Core, Greedy Man v1, TradingView backtests, webhook forward tests, broker execution, analytics, and reporting  
**Primary Goal:** Ensure that position behavior is identical across backtesting, forward testing, paper trading, and live execution.

---

## 1. Purpose

The GTAP Position Management Specification defines how GTAP opens, adds to, protects, reduces, reverses, and closes positions.

This document exists to prevent execution mismatches between:

- TradingView strategy backtests
- TradingView indicator alerts
- GTAP webhook processing
- Mock broker execution
- Tradovate paper trading
- Tradovate live trading
- Repository records
- Analytics reports
- Trade Quality Assurance
- Strategy Health Monitoring

No strategy may be promoted unless its position-management behavior matches this specification across all execution environments.

---

## 2. Core Principle

A strategy generates a trade opportunity.

GTAP decides whether that opportunity becomes:

- a new position,
- a scale-in,
- a scale-out,
- an exit,
- a reversal,
- or a rejected action.

The strategy is responsible for signal generation.

The Position Manager and Risk Engine are responsible for position behavior.

---

## 3. Position Lifecycle

Every position follows this lifecycle:

```text
FLAT
  ↓
ENTRY REQUESTED
  ↓
ENTRY APPROVED
  ↓
ENTRY SUBMITTED
  ↓
ENTRY FILLED
  ↓
OPEN
  ├── ADD REQUESTED
  ├── PARTIAL EXIT REQUESTED
  ├── STOP UPDATED
  ├── TARGET UPDATED
  ├── EXIT REQUESTED
  └── REVERSAL REQUESTED
  ↓
CLOSING
  ↓
CLOSED
```

A position must never move directly from `FLAT` to `OPEN` without an approved and recorded entry event.

---

## 4. Position States

GTAP recognizes the following position states:

| State | Meaning |
|---|---|
| `FLAT` | No open position |
| `PENDING_ENTRY` | Entry approved but not fully filled |
| `OPEN_LONG` | Net long position exists |
| `OPEN_SHORT` | Net short position exists |
| `PENDING_ADD` | Scale-in order submitted |
| `PENDING_EXIT` | Exit order submitted |
| `PARTIALLY_FILLED` | Order is only partially filled |
| `CLOSING` | Exit process is active |
| `CLOSED` | Position fully closed |
| `ERROR` | Position state is inconsistent or unresolved |
| `HALTED` | Trading disabled by risk or operational controls |

The broker position is the authoritative live-state source.

The repository is the authoritative historical record.

---

## 5. Position Identity

Every position receives a unique `position_id`.

All entries, adds, exits, stop updates, and targets belonging to the same net position reference that `position_id`.

Required identifiers:

```text
strategy_id
strategy_version
position_id
signal_id
order_id
execution_id
trade_leg_id
parent_entry_id
broker_account_id
broker_position_id
```

Example:

```text
position_id: GM-MNQ-20260721-001
initial entry: leg 1
first add: leg 2
second add: leg 3
final exit: closes position GM-MNQ-20260721-001
```

---

## 6. Position Model

GTAP v1 uses a **unified net-position model**.

Under this model:

- All same-direction fills belong to one position.
- Every add changes the total quantity.
- Every add may change the weighted average entry price.
- Risk is evaluated at the position level.
- The position has one authoritative protective stop.
- The position may have one or multiple profit targets.
- Analytics retain each leg separately while also reporting the combined position.

This model must be implemented consistently in Pine Script, GTAP, and broker execution.

---

## 7. Initial Entry Rules

An initial entry may occur only when:

1. The account is flat for the symbol and strategy.
2. A valid strategy signal exists.
3. The signal is within the approved session.
4. The signal has not expired.
5. The Risk Engine approves the requested quantity.
6. The daily loss limit has not been reached.
7. The maximum trade limit has not been reached.
8. The strategy is not halted.
9. Broker connectivity is healthy.
10. No conflicting pending order exists.

Initial-entry quantity defaults to one contract unless the Risk Engine approves a different amount.

The first successful fill establishes:

```text
position_id
initial_entry_price
weighted_average_price
current_quantity
maximum_quantity
initial_stop
initial_target
opened_at
direction
```

---

## 8. Scale-In Policy

A scale-in is a same-direction addition to an existing open position.

A scale-in is not treated as a new independent position.

### 8.1 Required Conditions

A scale-in may occur only when all of the following are true:

1. A position is already open.
2. The add signal matches the current position direction.
3. The add signal is fresh.
4. The maximum position quantity has not been reached.
5. The maximum number of adds has not been reached.
6. Total position risk remains within the configured limit.
7. The add is within the approved trading session.
8. The add is within the permitted distance from the initial entry.
9. The add is not blocked by momentum-exhaustion rules.
10. The add is not blocked by daily risk controls.
11. No add order is already pending.
12. The broker-reported position agrees with GTAP state.

### 8.2 Fresh-Signal Requirement

A single persistent condition must not generate repeated adds.

Every scale-in requires a unique `signal_id`.

The same TradingView alert or bar event may not be reused to create multiple adds.

GTAP must reject:

```text
duplicate signal_id
duplicate webhook payload
duplicate broker order request
repeated same-bar recalculation without a new signal
```

### 8.3 Same-Bar Adds

GTAP v1 policy:

> Same-bar scale-ins are disabled by default.

They may be enabled only for a strategy that explicitly defines an intrabar add event and passes parity testing.

For Greedy Man v1:

```text
allow_same_bar_adds: false
```

`calc_on_order_fills=true` may be used for controlled testing, but it must not create repeated adds merely because the entry condition remains true.

### 8.4 Add Count

Definitions:

```text
initial entry = stack level 1
first add     = stack level 2
second add    = stack level 3
third add     = stack level 4
```

If `max_position_quantity = 4`, then the position can contain:

- one initial contract,
- plus up to three additional contracts.

GTAP must distinguish:

- `entries_today`
- `adds_today`
- `current_position_quantity`
- `maximum_position_quantity_reached`
- `rejected_adds`

### 8.5 Distance Rule

For a long position:

```text
distance_ticks =
(current_market_price - initial_entry_price) / minimum_tick
```

For a short position:

```text
distance_ticks =
(initial_entry_price - current_market_price) / minimum_tick
```

An add is rejected when distance exceeds `max_add_distance_ticks`.

---

## 9. Opposite-Signal Policy

Opposite signals must never cause an accidental reversal.

GTAP v1 supports four policies:

| Policy | Behavior |
|---|---|
| `IGNORE` | Ignore opposite signal while position is open |
| `EXIT_ONLY` | Close current position but do not open opposite direction |
| `EXIT_THEN_REVERSE` | Close current position, confirm flat, then open opposite direction |
| `IMMEDIATE_REVERSAL` | Broker reversal order; not permitted in GTAP v1 |

### Greedy Man v1 Default

```text
opposite_signal_policy: EXIT_ONLY
```

Therefore:

```text
Long position + short signal
→ request exit
→ confirm flat
→ do not automatically open short
```

A new short requires a new signal after the flat state is confirmed.

---

## 10. Reversal Rules

GTAP v1 prohibits implicit reversal.

The system must never rely on default broker or Pine behavior to reverse a position.

A reversal requires:

1. An explicit reversal policy.
2. A close request for the existing position.
3. Confirmation that the current position is flat.
4. Cancellation of all previous protective orders.
5. A new signal identifier.
6. A new risk evaluation.
7. A new position identifier.
8. Submission of a separate opposite-direction order.

---

## 11. Position Risk

Position risk is evaluated across the entire open quantity.

For a long position:

```text
position_risk =
(weighted_average_entry - protective_stop)
× point_value
× total_quantity
```

For a short position:

```text
position_risk =
(protective_stop - weighted_average_entry)
× point_value
× total_quantity
```

An add must be rejected when:

```text
projected_position_risk > maximum_allowed_position_risk
```

This remains true even if the configured maximum stack count has not been reached.

The stack limit is a quantity limit.

The risk limit is a financial-loss limit.

Both must pass.

---

## 12. Protective Stop Policy

Every open position must have an active protective stop.

### 12.1 Stop Requirement

A position is not considered operationally healthy until the broker confirms an active protective stop.

If a position is filled but no stop is confirmed within the configured timeout:

```text
severity: CRITICAL
action: immediate stop retry
fallback: market exit
```

### 12.2 Unified Stop

Greedy Man v1 uses one position-level stop.

After an add:

- total quantity is recalculated,
- weighted average entry is recalculated,
- projected risk is recalculated,
- the position-level stop is updated according to the configured stop policy.

### 12.3 Stop Policy Options

GTAP supports:

| Policy | Behavior |
|---|---|
| `FIXED_FROM_INITIAL_ENTRY` | Stop remains based on first entry |
| `FIXED_FROM_WEIGHTED_AVERAGE` | Stop moves with weighted average |
| `NO_RISK_INCREASE` | Stop may improve but may never increase total risk |
| `PER_LEG` | Each entry leg has its own stop |

### Greedy Man v1 Default

```text
stop_policy: NO_RISK_INCREASE
```

This means an add may not widen total monetary risk.

The stop may:

- remain unchanged,
- move toward breakeven,
- tighten,
- or be rejected if the add would exceed risk.

---

## 13. Take-Profit Policy

GTAP supports:

| Policy | Behavior |
|---|---|
| `SINGLE_POSITION_TARGET` | Entire position exits at one target |
| `MULTI_TARGET` | Quantity is divided among targets |
| `PER_LEG_TARGET` | Every entry leg has a separate target |
| `TRAIL_ONLY` | No fixed profit target |
| `HYBRID` | Partial target plus trailing remainder |

### Greedy Man v1 Proposed Default

```text
take_profit_policy: HYBRID
```

Example for four contracts:

```text
TP1: close 2 contracts
TP2: close 1 contract
Runner: trail 1 contract
```

For one contract:

```text
single fixed target or trailing stop
```

The exact allocation must be defined in the Greedy Man configuration.

---

## 14. Trailing Stop Policy

A trailing stop must specify:

```text
activation threshold
trail distance
quantity covered
reference price
update frequency
minimum improvement
```

A trailing stop may not:

- widen the current stop,
- increase maximum position risk,
- coexist with conflicting protective orders,
- remain active after the position closes.

Greedy Man v1 must use broker-supported trailing behavior or a GTAP-managed synthetic trail, but not both simultaneously.

---

## 15. Partial Exits

A partial exit reduces quantity while preserving the same `position_id`.

After every partial exit, GTAP must update:

```text
remaining_quantity
realized_pnl
unrealized_pnl
protective_stop_quantity
remaining_targets
position_risk
```

The repository must preserve the closed leg and remaining open position separately.

---

## 16. Time-Based Exit

When the configured auto-exit time is reached:

1. Cancel all unfilled entry and add orders.
2. Cancel existing targets if necessary.
3. Submit a close order for the entire remaining position.
4. Confirm the broker position is flat.
5. Cancel any orphaned stop or target orders.
6. Mark the position closed.
7. Record the exit reason as `TIME_EXIT`.

No new position or add may be opened after the strategy entry cutoff.

---

## 17. Daily Order and Trade Limits

GTAP distinguishes the following limits:

```text
maximum_initial_entries_per_day
maximum_adds_per_position
maximum_total_fills_per_day
maximum_completed_positions_per_day
maximum_open_quantity
maximum_daily_loss
```

A single `orderCount` variable must not represent all of these concepts.

Each counter must be tracked independently.

---

## 18. Order Handling

Every order must pass through these statuses:

```text
CREATED
VALIDATED
APPROVED
SUBMITTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCEL_REQUESTED
CANCELLED
REJECTED
EXPIRED
ERROR
```

No analytics record may assume that a submitted order was filled.

Only confirmed fills change position quantity.

---

## 19. Duplicate Protection

GTAP must reject duplicate events using:

```text
signal_id
idempotency_key
broker_order_id
execution_id
position_id
timestamp tolerance
```

A repeated TradingView webhook must return the original result rather than creating another order.

---

## 20. Broker Reconciliation

GTAP must periodically compare:

```text
GTAP expected position
vs
broker actual position
```

A mismatch creates a reconciliation incident.

Examples:

- GTAP expects long 2, broker reports long 1.
- GTAP expects flat, broker reports short 1.
- GTAP expects stop quantity 3, broker stop covers 1.
- GTAP expects one active target, broker has two orphaned targets.

Critical mismatches may trigger:

```text
halt strategy
cancel orders
flatten position
notify operator
create audit incident
```

---

## 21. Required Repository Fields

Every execution record should include:

```text
strategy_id
strategy_version
position_id
trade_leg_id
signal_id
parent_entry_id
order_id
broker_order_id
execution_id
symbol
direction
action
order_type
requested_quantity
filled_quantity
position_before
position_after
stack_level
entry_price
fill_price
weighted_average_after
stop_before
stop_after
target_before
target_after
risk_before
risk_after
realized_pnl
unrealized_pnl
commission
slippage
event_time
broker_time
status
exit_reason
rejection_reason
```

Valid `action` values:

```text
INITIAL_ENTRY
ADD
PARTIAL_EXIT
FULL_EXIT
STOP_EXIT
TARGET_EXIT
TIME_EXIT
RISK_EXIT
MANUAL_EXIT
REVERSAL_EXIT
```

---

## 22. TradingView Parity Rules

The TradingView strategy must model the same rules as GTAP.

Required parity areas:

- initial-entry conditions,
- add conditions,
- maximum quantity,
- fresh-signal requirement,
- same-bar policy,
- opposite-signal policy,
- stop behavior,
- target behavior,
- time exit,
- commission,
- slippage,
- session timezone,
- quantity rules,
- order timing.

TradingView-specific settings must be documented:

```text
pyramiding
calc_on_order_fills
calc_on_every_tick
process_orders_on_close
bar magnifier
fill assumptions
```

A strategy change affecting any of these requires a new strategy version.

---

## 23. Backtest-to-Forward-Test Promotion Gate

A strategy cannot advance until parity testing confirms:

1. Identical signals for the same market data.
2. Identical direction decisions.
3. Identical add decisions.
4. Identical maximum quantity.
5. Identical opposite-signal behavior.
6. Equivalent stop and target handling.
7. Equivalent time-exit behavior.
8. No unexplained reversals.
9. No duplicate orders.
10. No unmanaged position legs.

Parity target:

```text
signal parity: 100%
direction parity: 100%
quantity parity: 100%
position-state parity: 100%
exit-reason parity: at least 95%
price parity: within defined slippage tolerance
```

---

## 24. Trade Quality Assurance Rules

Critical failures:

- open position without confirmed stop,
- position exceeds maximum quantity,
- position exceeds maximum allowed risk,
- accidental reversal,
- untracked add,
- duplicate fill,
- repository-broker quantity mismatch,
- orphaned stop or target,
- position remains open after mandatory exit,
- same signal creates multiple unauthorized adds.

Warnings:

- add near maximum distance,
- high slippage,
- delayed stop update,
- partial-fill delay,
- repeated rejected adds,
- unusual holding time.

---

## 25. Greedy Man v1 Proposed Configuration

```yaml
position_management:
  model: unified_net_position

  initial_quantity: 1
  max_position_quantity: 4
  max_adds_per_position: 3

  allow_same_bar_adds: false
  require_fresh_signal_for_add: true
  max_add_distance_ticks: 40

  opposite_signal_policy: EXIT_ONLY
  allow_implicit_reversal: false

  stop_policy: NO_RISK_INCREASE
  take_profit_policy: HYBRID

  require_confirmed_stop: true
  stop_confirmation_timeout_seconds: 3
  flatten_if_stop_unconfirmed: true

  entry_cutoff_time: "11:30"
  mandatory_exit_time: "11:30"
  timezone: America/New_York

  reconcile_with_broker: true
  reconciliation_interval_seconds: 5

risk:
  max_position_risk_dollars: TBD
  max_daily_loss_dollars: TBD
  max_completed_positions_per_day: TBD
```

---

## 26. Implementation Responsibilities

### Strategy Engine

- Generate initial-entry signals.
- Generate fresh add signals.
- Generate exit signals.
- Never submit broker orders directly.

### Position Manager

- Track current position state.
- Classify signals as entry, add, exit, or opposite.
- Enforce position policy.
- Maintain position identifiers and stack levels.

### Risk Engine

- Approve or reject entries and adds.
- Calculate projected risk.
- Enforce daily and position-level limits.

### Execution Engine

- Build and submit orders.
- Confirm fills.
- Attach and update protective orders.
- Handle partial fills, retries, and cancellations.

### Broker Connector

- Translate GTAP orders into broker requests.
- Return broker order, execution, and position state.

### Repository

- Persist every state transition and execution event.

### Analytics Engine

- Calculate leg-level and position-level performance.

### Trade Quality Assurance

- Detect position-management violations.

### Strategy Health Monitor

- Include execution and risk-control failures in health scoring.

---

## 27. Acceptance Tests

The implementation must pass at least these scenarios:

1. One valid long entry while flat.
2. One valid short entry while flat.
3. Valid long add after a fresh signal.
4. Rejected duplicate add from the same signal.
5. Rejected add after maximum quantity.
6. Rejected add when projected risk is too high.
7. Opposite signal exits but does not reverse.
8. Stop is updated after an add.
9. Add is rejected if stop protection cannot be confirmed.
10. Partial fill updates quantity correctly.
11. Time exit closes the entire position.
12. Broker mismatch creates an incident.
13. Duplicate webhook does not create a second order.
14. Position closes with no orphaned orders.
15. Backtest and forward test produce matching stack levels.
16. Strategy does not repeatedly add after `calc_on_order_fills` recalculation.
17. A stopped-out position does not inherit old state.
18. A new position receives a new `position_id`.
19. Repository reports both leg-level and position-level P&L.
20. Trade Quality Assurance flags unauthorized stacking.

---

## 28. Decisions Still Required

Before final approval, the following Greedy Man decisions must be finalized:

1. Exact add signal definition.
2. Maximum monetary position risk.
3. Maximum daily loss.
4. Maximum completed positions per day.
5. Take-profit allocation by quantity.
6. Trailing-stop activation threshold.
7. Whether stops remain fixed from initial entry or tighten after adds.
8. Whether a position may be re-entered after a full exit on the same day.
9. Minimum time or price movement between adds.
10. Whether volume confirmation is mandatory for adds.
11. Whether an add is allowed while the position is temporarily losing.
12. Whether news or volatility filters block adds.

---

## 29. Governance Rule

Any modification to:

- stacking,
- quantity,
- stop behavior,
- target behavior,
- reversal behavior,
- time exit,
- or risk calculation

requires:

1. a strategy version increase,
2. updated backtest results,
3. updated forward-test results,
4. parity validation,
5. documentation update,
6. promotion review.

---

## 30. Final Position-Management Principle

> GTAP must never allow a strategy signal, broker default, duplicate webhook, or simulator setting to determine position behavior implicitly.

Every entry, add, exit, stop, target, and reversal must be explicit, validated, risk-approved, recorded, and reproducible.
