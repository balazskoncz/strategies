import pytest

from simple_strategies import (
    Action,
    BuyAndHoldStrategy,
    MonkeyParams,
    MonkeyState,
    MonkeyStrategy,
    Strategy,
    StrategyParams,
    StrategyState,
)


class TestStrategyState:
    def test_initial_defaults_to_flat(self):
        assert StrategyState.initial().in_position is False

    def test_round_trip(self):
        state = StrategyState(in_position=True)
        assert StrategyState.from_dict(state.to_dict()) == state


class TestStrategy:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Strategy()


class TestBuyAndHoldStrategy:
    def setup_method(self):
        self.strategy = BuyAndHoldStrategy()
        self.params = StrategyParams()

    def test_first_bar_buys(self):
        state = StrategyState.initial()
        action, state = self.strategy.on_bar(100.0, self.params, state)
        assert action == Action.BUY
        assert state.in_position is True

    def test_holds_forever_after_buying(self):
        state = StrategyState.initial()
        _, state = self.strategy.on_bar(100.0, self.params, state)
        for price in [50.0, 200.0, 0.01, 1_000_000.0]:
            action, state = self.strategy.on_bar(price, self.params, state)
            assert action == Action.HOLD
            assert state.in_position is True

    def test_does_not_mutate_input_state(self):
        state = StrategyState.initial()
        _, new_state = self.strategy.on_bar(100.0, self.params, state)
        assert state.in_position is False
        assert new_state.in_position is True


class TestMonkeyState:
    def test_initial_defaults(self):
        state = MonkeyState.initial()
        assert state.in_position is False
        assert state.draw_count == 0

    def test_round_trip(self):
        state = MonkeyState(in_position=True, draw_count=3)
        assert MonkeyState.from_dict(state.to_dict()) == state


class TestMonkeyStrategy:
    def setup_method(self):
        self.strategy = MonkeyStrategy()
        self.prices = [100, 101, 99, 98, 105, 110, 95, 90, 120, 80]

    def _run(self, seed, prices=None):
        params = MonkeyParams(seed=seed)
        state = MonkeyState.initial()
        actions = []
        for price in prices or self.prices:
            action, state = self.strategy.on_bar(float(price), params, state)
            actions.append(action)
        return actions

    def test_same_seed_is_reproducible(self):
        assert self._run(seed=7) == self._run(seed=7)

    def test_different_seeds_can_diverge(self):
        prices = list(range(100, 130))
        assert self._run(seed=1, prices=prices) != self._run(seed=2, prices=prices)

    def test_action_respects_position_state(self):
        params = MonkeyParams(seed=99)
        state = MonkeyState.initial()
        for price in range(100, 160):
            was_in_position = state.in_position
            action, state = self.strategy.on_bar(float(price), params, state)
            if was_in_position:
                assert action in (Action.SELL, Action.HOLD)
            else:
                assert action in (Action.BUY, Action.HOLD)

    def test_in_position_flips_on_buy_and_sell(self):
        params = MonkeyParams(seed=99)
        state = MonkeyState.initial()
        for price in range(100, 160):
            action, state = self.strategy.on_bar(float(price), params, state)
            if action == Action.BUY:
                assert state.in_position is True
            elif action == Action.SELL:
                assert state.in_position is False

    def test_draw_count_increments_each_call(self):
        params = MonkeyParams(seed=1)
        state = MonkeyState.initial()
        for expected in range(5):
            assert state.draw_count == expected
            _, state = self.strategy.on_bar(100.0, params, state)
        assert state.draw_count == 5

    def test_does_not_mutate_input_state(self):
        params = MonkeyParams(seed=1)
        state = MonkeyState.initial()
        _, new_state = self.strategy.on_bar(100.0, params, state)
        assert state.draw_count == 0
        assert new_state.draw_count == 1
