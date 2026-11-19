import math
import matplotlib.pyplot as plt
#inputs

def read_positive_float(prompt):
    #this func read a positive decimal number from the user
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            print("Please enter a value greater than zero.")
        except ValueError:
            print("Please enter a valid number.")


def read_percentage(prompt, allow_zero=False):
    #read a percentage (e.g: 25 for 25%)
    while True:
        try:
            value = float(input(prompt))
            minimum = 0 if allow_zero else 0
            if value >= minimum and value <= 100:
                if not allow_zero and value == 0:
                    print("Please enter a percentage greater than zero.")
                    continue
                return value / 100
            print("Please enter a percentage between 0 and 100.")
        except ValueError:
            print("Please enter a valid percentage.")


def read_intervals():
    #read the number of binomial intervals
    while True:
        try:
            intervals = int(input("Enter the number of intervals (1-3): "))
            if 1 <= intervals <= 3:
                return intervals
            print("Intervals must be between 1 and 3.")
        except ValueError:
            print("Please enter a whole number: 1, 2, or 3.")


def read_option_type():
    #read and normalize the option type
    while True:
        option_type = input("Enter option type (call/put): ").strip().lower()
        if option_type in ("call", "c"):
            return "call"
        if option_type in ("put", "p"):
            return "put"
        print("Please enter 'call' or 'put'.")


#pricing calculation

def calculate_american_option(
    strike_price,
    stock_price,
    intervals,
    time_to_expiry,
    volatility,
    risk_free_rate,
    option_type,
):
    
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'.")
    if intervals < 1:
        raise ValueError("intervals must be at least 1.")
    if volatility <= 0:
        raise ValueError("volatility must be greater than zero.")

    #length of each time interval
    delta_t = time_to_expiry / intervals

    #up and down factors.
    up_factor = math.exp(volatility * math.sqrt(delta_t))
    down_factor = 1 / up_factor

    #risk-neutral probability 
    discount_growth = math.exp(risk_free_rate * delta_t)
    up_probability = (discount_growth - down_factor) / (up_factor - down_factor)
    down_probability = 1 - up_probability

    if not 0 <= up_probability <= 1:
        raise ValueError(
            "The selected inputs produce an invalid risk-neutral probability."
        )

    #stock prices and option values at expiration
    option_values = []
    for up_moves in range(intervals + 1):
        stock_at_expiry = (
            stock_price
            * (up_factor ** up_moves)
            * (down_factor ** (intervals - up_moves))
        )

        if option_type == "call":
            payoff = max(stock_at_expiry - strike_price, 0)
        else:
            payoff = max(strike_price - stock_at_expiry, 0)

        option_values.append(payoff)

    #work backwards through the tree
    #for an American option, compare continuation value with immediate
    # exercise value at every node. This is the key difference from a
    # European option, which can only be exercised at expiry
    for step in range(intervals - 1, -1, -1):
        new_values = []

        for up_moves in range(step + 1):
            stock_price_at_node = (
                stock_price
                * (up_factor ** up_moves)
                * (down_factor ** (step - up_moves))
            )

            continuation_value = math.exp(-risk_free_rate * delta_t) * (
                up_probability * option_values[up_moves + 1]
                + down_probability * option_values[up_moves]
            )

            if option_type == "call":
                exercise_value = max(stock_price_at_node - strike_price, 0)
            else:
                exercise_value = max(strike_price - stock_price_at_node, 0)

            # American option value = better of holding and exercising now.
            node_value = max(continuation_value, exercise_value)
            new_values.append(node_value)

        option_values = new_values

    return option_values[0]


#comparison and output 

def compare_with_market(theoretical_value, market_premium):
    #slassify the market premium compared with the theoretical value
    # A small tolerance avoids calling tiny rounding differences meaningful
    tolerance = max(0.01, theoretical_value * 0.01)

    difference = market_premium - theoretical_value
    if abs(difference) <= tolerance:
        return "FAIRLY VALUED"
    if market_premium > theoretical_value:
        return "OVER-VALUED"
    return "UNDER-VALUED"


def main():
    print("\nAmerican Option Pricing - Binomial Model")
    print("=" * 46)
    print("Enter volatility and risk-free rate as percentages.\n")

    #inputs based on the project requirements.
    strike_price = read_positive_float("Enter strike price: ")
    stock_price = read_positive_float("Enter stock price: ")
    intervals = read_intervals()
    time_to_expiry = read_positive_float("Enter time to expiry in years: ")
    volatility = read_percentage("Enter volatility (0-100%): ")
    risk_free_rate = read_percentage(
        "Enter risk-free rate (0-100%, enter 0 if applicable): ",
        allow_zero=True,
    )
    market_premium = read_positive_float("Enter current market premium: ")
    option_type = read_option_type()

    try:
        theoretical_value = calculate_american_option(
            strike_price=strike_price,
            stock_price=stock_price,
            intervals=intervals,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            option_type=option_type,
        )
    except ValueError as error:
        print(f"\nCalculation error: {error}")
        return

    decision = compare_with_market(theoretical_value, market_premium)
    difference = market_premium - theoretical_value

    
    print("RESULT")
    print("-" * 46)
    print(f"Option type:              {option_type.title()}")
    print(f"Theoretical option value: {theoretical_value:.4f}")
    print(f"Market premium:           {market_premium:.4f}")
    print(f"Market - theoretical:     {difference:+.4f}")
    print(f"Decision:                 {decision}")
    
    print("Note: This result is an estimate based on the entered assumptions.")

    show_tree = input("\nDo you want to see the binomial tree? (yes/no): ").strip().lower()
    if show_tree in ("yes", "y"):
        display_binomial_tree(
            stock_price=stock_price,
            intervals=intervals,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
        )


def display_binomial_tree(stock_price, intervals, time_to_expiry, volatility):
    delta_t = time_to_expiry / intervals
    up_factor = math.exp(volatility * math.sqrt(delta_t))
    down_factor = 1 / up_factor
    tree_values = []

    print("\nBINOMIAL STOCK-PRICE TREE")
    print("-" * 30)

    for step in range(intervals + 1):
        values = []

        for up_moves in range(step + 1):
            stock_price_at_node = (
                stock_price
                * (up_factor ** up_moves)
                * (down_factor ** (step - up_moves))
            )
            values.append(f"{stock_price_at_node:.4f}")

        spaces = " " * ((intervals - step) * 4)
        print(f"Step {step}: {spaces}" + "    ".join(values))

        step_values = []
        for up_moves in range(step + 1):
            stock_price_at_node = (
                stock_price
                * (up_factor ** up_moves)
                * (down_factor ** (step - up_moves))
            )
            step_values.append(stock_price_at_node)
        tree_values.append(step_values)

    plt.figure(figsize=(10, 6))

    for step in range(intervals):
        for up_moves in range(step + 1):
            current_y = 2 * up_moves - step
            down_y = 2 * up_moves - (step + 1)
            up_y = 2 * (up_moves + 1) - (step + 1)
            plt.plot([step, step + 1], [current_y, down_y], color="gray")
            plt.plot([step, step + 1], [current_y, up_y], color="gray")

    for step, step_values in enumerate(tree_values):
        for up_moves, value in enumerate(step_values):
            y_position = 2 * up_moves - step
            plt.scatter(step, y_position, color="royalblue", s=600, zorder=2)
            plt.text(
                step,
                y_position,
                f"{value:.2f}",
                color="white",
                ha="center",
                va="center",
                fontsize=9,
                zorder=3,
            )

    plt.title("Binomial Stock-Price Tree")
    plt.xlabel("Time Step")
    plt.ylabel("Up/Down Position")
    plt.xticks(range(intervals + 1))
    plt.yticks([])
    plt.grid(axis="x", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.show()

   


if __name__ == "__main__":
    main()
