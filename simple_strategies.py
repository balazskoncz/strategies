"""
simple_strategies.py
=====================
Two baseline strategies used for comparison against more elaborate ones
(e.g. a trailing stop-loss + re-entry strategy):

- BuyAndHoldStrategy: buys on the first bar and never sells.
- MonkeyStrategy:     emits random BUY / SELL / HOLD signals. Useful as a
                       dumb baseline; the random seed is configurable so
                       runs are reproducible.

Environment-agnostic, no I/O; the caller persists / restores state
between calls.

Shared base classes
--------------------
StrategyParams / StrategyState are meant to be subclassed, not
reinvented per strategy. A strategy with no knobs (BuyAndHoldStrategy)
just uses StrategyParams / StrategyState directly. A strategy that needs
extra fields (MonkeyStrategy) subclasses and adds only what it needs;
`initial()` / `from_dict()` / `to_dict()` are inherited for free.

Typical usage
-------------
    state = StrategyState.initial()
    for date, price in bars:
        action, state = buy_and_hold.on_bar(price, StrategyParams(), state)

    state = MonkeyState.initial()
    for date, price in bars:
        action, state = monkey.on_bar(price, MonkeyParams(seed=42), state)
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class Action(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class StrategyParams:
    """
    Base for a strategy's tunable knobs. Empty on its own — strategies
    with no knobs (e.g. buy & hold) use it directly; strategies that
    need knobs subclass it and add fields.
    """
    pass


@dataclass
class StrategyState:
    """
    Base state shared by every strategy: whether we currently hold a
    position. Strategies that need to remember more subclass this and
    add fields; (de)serialisation is inherited for free.
    """
    in_position: bool = False

    # ------------------------------------------------------------------
    @classmethod
    def initial(cls, **kwargs) -> "StrategyState":
        return cls(**kwargs)

    @classmethod
    def from_dict(cls, d: dict) -> "StrategyState":
        return cls(**d)

    def to_dict(self) -> dict:
        return asdict(self)


class Strategy(ABC):
    """
    Common interface: `on_bar` is a pure function of
    (price, params, state) -> (action, new_state). The caller decides
    how to persist the returned state.
    """

    @abstractmethod
    def on_bar(
        self,
        price: float,
        params: StrategyParams,
        state: StrategyState,
    ) -> tuple[Action, StrategyState]:
        ...


# ---------------------------------------------------------------------------
# Buy & hold
# ---------------------------------------------------------------------------

class BuyAndHoldStrategy(Strategy):
    """
    Buys on the first bar it sees and holds forever after that.
    No knobs, no extra state — `in_position` alone tells the whole story.
    """

    def on_bar(
        self,
        price: float,
        params: StrategyParams,
        state: StrategyState,
    ) -> tuple[Action, StrategyState]:
        st = StrategyState(in_position=state.in_position)

        if not st.in_position:
            st.in_position = True
            return Action.BUY, st

        return Action.HOLD, st


# ---------------------------------------------------------------------------
# Monkey (random)
# ---------------------------------------------------------------------------

@dataclass
class MonkeyParams(StrategyParams):
    """
    seed : int
        Seeds the RNG so runs are reproducible (not that it makes the
        strategy any more useful).
    """
    seed: int


@dataclass
class MonkeyState(StrategyState):
    """
    draw_count : int
        Number of random draws made so far. Combined with the seed to
        derive a fresh, reproducible RNG state on every call without
        having to serialise a random.Random object.
    """
    draw_count: int = 0


class MonkeyStrategy(Strategy):
    """
    Emits random BUY / SELL / HOLD signals.

    On each bar, draws uniformly between HOLD and whichever of
    BUY / SELL is currently valid (BUY when flat, SELL when holding),
    so the resulting action stream stays a coherent state machine.
    """

    def on_bar(
        self,
        price: float,
        params: MonkeyParams,
        state: MonkeyState,
    ) -> tuple[Action, MonkeyState]:
        st = MonkeyState(in_position=state.in_position, draw_count=state.draw_count)

        # random.Random() only accepts None/int/float/str/bytes/bytearray as
        # a seed (Python 3.9+ dropped the implicit hash() fallback for other
        # types), so fold seed + draw_count into a single deterministic int
        # rather than passing a tuple.
        rng = random.Random(params.seed * 2**32 + st.draw_count)
        st.draw_count += 1

        choices = [Action.SELL, Action.HOLD] if st.in_position else [Action.BUY, Action.HOLD]
        action = rng.choice(choices)

        if action == Action.BUY:
            st.in_position = True
        elif action == Action.SELL:
            st.in_position = False

        return action, st
