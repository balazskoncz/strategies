# strategies

Small, environment-agnostic trading strategy building blocks. Each strategy is a pure
function of `(price, params, state) -> (action, new_state)` — no I/O, no file reads, no DB
writes. The caller (backtest harness, cloud handler, whatever) owns persisting and
restoring state between calls.

Included so far:

| Strategy | Description |
| --- | --- |
| `BuyAndHoldStrategy` | Buys on the first bar it sees and holds forever. No knobs. |
| `MonkeyStrategy` | Emits random BUY / SELL / HOLD signals. Seeded for reproducibility — useful as a dumb baseline, not for actual trading. |

## Installation

Requires Python 3.9+. No third-party runtime dependencies.

Install directly from GitHub:

```bash
pip install git+https://github.com/balazskoncz/strategies.git
```

Or clone and install locally (editable, so local edits are picked up immediately):

```bash
git clone https://github.com/balazskoncz/strategies.git
cd strategies
pip install -e .
```

## Usage

```python
from simple_strategies import (
    Action,
    BuyAndHoldStrategy,
    MonkeyParams,
    MonkeyState,
    MonkeyStrategy,
    StrategyParams,
    StrategyState,
)

prices = [100.0, 102.0, 98.0, 95.0, 101.0]

# --- Buy & hold ---------------------------------------------------------
strategy = BuyAndHoldStrategy()
params = StrategyParams()
state = StrategyState.initial()

for price in prices:
    action, state = strategy.on_bar(price, params, state)
    print(price, action)

# --- Monkey (random, but reproducible) ----------------------------------
strategy = MonkeyStrategy()
params = MonkeyParams(seed=42)
state = MonkeyState.initial()

for price in prices:
    action, state = strategy.on_bar(price, params, state)
    print(price, action)
```

Every strategy state supports `to_dict()` / `from_dict()` for persistence between
runs (e.g. in a database, between invocations of a stateless cloud function):

```python
saved = state.to_dict()          # -> plain dict, safe to json.dumps / store
state = MonkeyState.from_dict(saved)
```

### Writing a new strategy

Subclass `Strategy` and implement `on_bar`. Reuse `StrategyParams` / `StrategyState`
directly if your strategy needs no extra knobs or memory; subclass them and add fields
only when you actually need to remember or configure something extra — see
`MonkeyParams` / `MonkeyState` in [simple_strategies.py](simple_strategies.py) for an
example.

## Development

```bash
pip install -e ".[test]"
pytest -q
```

## License

[Apache License 2.0](LICENSE)
