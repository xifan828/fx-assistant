
from simulation.generate_strategy import generate_trading_strategy
from simulation.back_test import BackTest

#generate_trading_strategy()

def back_test(currency_pair, strategy_file_path):
    back_test = BackTest(
        currency_pair=currency_pair,
        strategy_file_path=strategy_file_path
    )
    updated_strategy = back_test.evaluate_strategy()
    back_test.write_strategy(updated_strategy)


if __name__ == "__main__":
    #back_test("EUR/USD", r"simulation\trading_strategy.csv")

    generate_trading_strategy(r"simulation\12_09_12_13\trading_strategy.csv")