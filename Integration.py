import math
import re

# Import derivative lookup dictionary from differentiation.py for supported function names
from differentiation import BASE_DERIVATIVES

SUPPORTED_FUNCS = list(BASE_DERIVATIVES.keys())


# --- 1. USER INPUT FUNCTIONS ---


def input_single_composite_term():
    """Prompts for a single/composite term (e.g. 5*cos(x))."""
    print("\n--- ADD SINGLE/COMPOSITE TERM ---")
    try:
        const = float(input("Enter constant multiplier (default 1.0): ") or "1.0")
    except ValueError:
        const = 1.0

    inner = input("Enter inner expression (e.g., x, x+1): ").strip()

    print(f"Supported functions: {', '.join(SUPPORTED_FUNCS)}")
    funcs_str = input(
        "Enter outer functions from OUTSIDE to INSIDE separated by commas (e.g. sin, cos) or leave blank: "
    ).strip()

    func_list = (
        [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
        if funcs_str
        else []
    )

    return {"const": const, "brackets": [{"funcs": func_list, "inner": inner}]}


def input_product_term():
    """Prompts for a product term (e.g. 3 * sin(x) * exp(x))."""
    print("\n--- ADD PRODUCT TERM ---")
    try:
        const = float(input("Enter constant multiplier (default 1.0): ") or "1.0")
    except ValueError:
        const = 1.0

    try:
        num_factors = int(input("How many factors in this product term?: "))
    except ValueError:
        num_factors = 1

    brackets = []
    for i in range(1, num_factors + 1):
        print(f"\n -> Factor #{i}:")
        inner = input("   Enter inner expression (e.g., x, x+1): ").strip()
        funcs_str = input(
            "   Enter outer functions (comma separated or blank): "
        ).strip()

        func_list = (
            [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
            if funcs_str
            else []
        )
        brackets.append({"funcs": func_list, "inner": inner})

    return {"const": const, "brackets": brackets}


# --- 2. NUMERICAL EVALUATION ENGINE ---


def evaluate_term_factor(factor, target_var, var_value):
    """Evaluates a single bracket factor given x = var_value."""
    inner_expr = factor["inner"].replace("^", "**")
    
    # Handle implicit multiplication like 2x -> 2*x
    inner_expr = re.sub(rf"(\d)({re.escape(target_var)})", r"\1*\2", inner_expr)

    # Safe evaluation environment
    eval_env = {
        target_var: float(var_value),
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "log": math.log,
        "ln": math.log,
        "sqrt": math.sqrt,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        val = float(eval(inner_expr, {"__builtins__": {}}, eval_env))
    except Exception:
        val = 0.0

    # Apply outer functions from inside to outside
    func_map = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "ln": math.log,
        "log": math.log,
        "arcsin": math.asin,
        "arccos": math.acos,
        "arctan": math.atan,
    }

    for func_name in reversed(factor["funcs"]):
        if func_name in func_map:
            try:
                val = func_map[func_name](val)
            except Exception:
                val = 0.0

    return val


def evaluate_system_at(system_terms, target_var, var_value):
    """Evaluates the entire function system at target_var = var_value."""
    total_value = 0.0

    for term in system_terms:
        term_val = term["const"]
        for factor in term["brackets"]:
            term_val *= evaluate_term_factor(factor, target_var, var_value)
        total_value += term_val

    return total_value


# --- 3. NUMERICAL INTEGRATION ENGINE (SIMPSON'S RULE) ---


def integrate_definite_simpsons(system_terms, target_var, lower_bound, upper_bound, steps=1000):
    """Calculates definite integral using Simpson's 1/3 Rule.
    
    Formula: ∫[a to b] f(x) dx ≈ (h/3) * [f(a) + 4*f(x1) + 2*f(x2) + 4*f(x3) + ... + f(b)]
    """
    if steps % 2 != 0:
        steps += 1  # Simpson's rule requires an even number of intervals

    h = (upper_bound - lower_bound) / steps

    # Initial endpoints evaluation
    sum_val = evaluate_system_at(
        system_terms, target_var, lower_bound
    ) + evaluate_system_at(system_terms, target_var, upper_bound)

    # Sum intermediate weighted steps
    for i in range(1, steps):
        x_i = lower_bound + i * h
        weight = 4 if i % 2 != 0 else 2
        sum_val += weight * evaluate_system_at(system_terms, target_var, x_i)

    integral_result = sum_val * (h / 3.0)

    print("\n==========================================")
    print("      DEFINITE INTEGRAL RESULT")
    print("==========================================")
    print(f" Target Variable: {target_var}")
    print(f" Lower Bound (a): {lower_bound}")
    print(f" Upper Bound (b): {upper_bound}")
    print(f" Evaluated Area ≈ {integral_result:.8f}")
    print("==========================================\n")

    return integral_result


# --- 4. MAIN CLI DRIVER ---


def main():
    system_terms = []

    while True:
        print("==========================================")
        print("     DEFINITE INTEGRATION ENGINE v2.0     ")
        print("==========================================")
        print(f"Current Terms in System: {len(system_terms)}")
        print("1. Add Single/Composite Term (e.g. 2*sin(x))")
        print("2. Add Product Term (e.g. sin(x)*exp(x))")
        print("3. Compute Definite Integral")
        print("4. Clear System")
        print("E. Exit")

        choice = input("\nChoose an option: ").strip().upper()

        if choice == "1":
            system_terms.append(input_single_composite_term())
            print("Term added successfully!")

        elif choice == "2":
            system_terms.append(input_product_term())
            print("Product term added successfully!")

        elif choice == "3":
            if not system_terms:
                print("\n[!] Please add at least one term before integrating!\n")
                continue

            target_var = input("\nEnter target variable (default 'x'): ").strip() or "x"

            while True:
                try:
                    lower_b = float(input("Enter LOWER bound (a): "))
                    upper_b = float(input("Enter UPPER bound (b): "))
                    break
                except ValueError:
                    print("Invalid input! Please enter valid numeric bounds.")

            integrate_definite_simpsons(
                system_terms, target_var, lower_b, upper_b, steps=2000
            )

        elif choice == "4":
            system_terms.clear()
            print("\nCleared all system terms!\n")

        elif choice == "E":
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
