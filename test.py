import math
# Import Simpson's integration engine from Integration.py
from Integration import evaluate_system_at, integrate_definite_simpsons

# Optional verification library
try:
    from scipy.integrate import quad
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def run_cli_test():
    print("==================================================")
    print("      INTEGRATION ENGINE ACCURACY BENCHMARK       ")
    print("==================================================")

    # ----------------------------------------------------
    # Complex Function System definition:
    # f(x) = 3 * sin(x+2) * cos(x) * sin(x) + sin(x+3)
    #
    # Term 1: 1 * sin(x+3)
    # Term 2: 3 * sin(x+2) * cos(x) * sin(x)
    # ----------------------------------------------------
    test_system = [
        # Term 1: sin(x+3)
        {
            "const": 1.0,
            "brackets": [
                {"funcs": ["sin"], "inner": "x+3"}
            ]
        },
        # Term 2: 3 * sin(x+2) * cos(x) * sin(x)
        {
            "const": 3.0,
            "brackets": [
                {"funcs": ["sin"], "inner": "x+2"},
                {"funcs": ["cos"], "inner": "x"},
                {"funcs": ["sin"], "inner": "x"}
            ]
        }
    ]

    target_var = "x"
    lower_bound = 2.0
    upper_bound = 8.0

    print("Function to Evaluate:")
    print("  f(x) = sin(x + 3) + 3 * sin(x + 2) * cos(x) * sin(x)\n")
    print(f"Integration Bounds: a = {lower_bound}, b = {upper_bound}\n")

    # 1. Run our engine
    our_result = integrate_definite_simpsons(
        test_system, target_var, lower_bound, upper_bound, steps=2000
    )

    # 2. Benchmark Verification
    print("--- VERIFICATION CHECK ---")
    
    # Mathematical reference function for verification
    def exact_f(x):
        return math.sin(x + 3) + 3 * math.sin(x + 2) * math.cos(x) * math.sin(x)

    if HAS_SCIPY:
        expected_result, error_est = quad(exact_f, lower_bound, upper_bound)
        diff = abs(our_result - expected_result)
        
        print(f" SciPy Benchmark Result : {expected_result:.8f}")
        print(f" Our Simpson's Engine   : {our_result:.8f}")
        print(f" Absolute Difference    : {diff:.10f}")
        
        if diff < 1e-6:
            print("\n[SUCCESS] The integration engine is rock solid! Accuracy within 0.000001.")
        else:
            print("\n[WARNING] Minor deviation detected.")
    else:
        print(" (Install `scipy` via `pip install scipy` to run automatic cross-checking)")


if __name__ == "__main__":
    run_cli_test()
