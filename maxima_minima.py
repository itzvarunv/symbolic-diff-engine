import math
import random
import re

# Global data holder structure
parent = {
    "polynomial": [],
    "complex": []
}

TRANS_DERIVATIVES = ["sin", "cos", "exp", "ln", "tan", "arcsin", "arccos", "arctan"]

FUNC_MAP = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "ln": math.log,
    "arcsin": math.asin,
    "arccos": math.acos,
    "arctan": math.atan,
}


# ==========================================================
# 1. DIFFERENTIATION ENGINE FOR POLYNOMIALS
# ==========================================================
def differentiate_polynomial(poly_coeffs):
    """
    Differentiates polynomial sum(c_i * x^i).
    P'(x) = 1*c1*x^0 + 2*c2*x^1 + ... + n*cn*x^(n-1)
    """
    if len(poly_coeffs) <= 1:
        return [0.0]
    
    diff_coeffs = []
    for power in range(1, len(poly_coeffs)):
        diff_coeffs.append(power * poly_coeffs[power])
        
    return diff_coeffs


# ==========================================================
# 2. DATA COLLECTION ENGINE
# ==========================================================
def collect_data():
    """Collects polynomial coefficients and complex composite terms into parent."""
    global parent
    parent["polynomial"] = []
    parent["complex"] = []

    print("\n==========================================")
    print("        DATA COLLECTION ENGINE           ")
    print("==========================================")

    # Polynomial Section
    print("\n--- 1. POLYNOMIAL TERMS ---")
    try:
        max_degree = int(input("Enter highest power/degree of original f(x) (e.g., 3 for cubic, -1 if none): "))
    except ValueError:
        max_degree = -1

    if max_degree >= 0:
        poly_coeffs = []
        for power in range(max_degree + 1):
            while True:
                try:
                    coeff = float(input(f"  Enter coefficient for x^{power} (default 0.0): ") or "0.0")
                    poly_coeffs.append(coeff)
                    break
                except ValueError:
                    print("  Invalid input! Enter a valid number.")
        parent["polynomial"] = poly_coeffs

    # Complex / Product Terms Section
    print("\n--- 2. COMPLEX & PRODUCT TERMS ---")
    try:
        num_complex_terms = int(input("How many complex/product terms in f(x)? (0 if none): "))
    except ValueError:
        num_complex_terms = 0

    for t in range(1, num_complex_terms + 1):
        print(f"\n -> Complex Term #{t}")
        try:
            const = float(input("   Enter constant multiplier for this term (default 1.0): ") or "1.0")
        except ValueError:
            const = 1.0

        try:
            num_factors = int(input("   How many factors in this term? (e.g., 2 for sin(x)*exp(x)): ") or "1")
        except ValueError:
            num_factors = 1

        factors = []
        for f_idx in range(1, num_factors + 1):
            print(f"      Factor #{f_idx}:")
            inner = input("        Enter inner expression (e.g., x, x+1): ").strip() or "x"
            
            print(f"        Available special functions: {', '.join(TRANS_DERIVATIVES)}")
            funcs_str = input("        Enter outer functions (outermost to innermost, comma-separated, or blank): ").strip()
            funcs = [f.strip().lower() for f in funcs_str.split(",") if f.strip()] if funcs_str else []

            try:
                power = float(input("        Enter exponent power for this factor (default 1.0): ") or "1.0")
            except ValueError:
                power = 1.0

            factors.append({
                "funcs": funcs,
                "inner": inner,
                "pow": power
            })

        parent["complex"].append({
            "const": const,
            "factors": factors
        })

    return parent


# ==========================================================
# 3. EVALUATORS & EXACT ANALYTICAL SOLVER
# ==========================================================
def evaluate_poly(coeffs, x):
    """Evaluates polynomial sum(c_i * x^i)."""
    return sum(c * (x ** i) for i, c in enumerate(coeffs))


def evaluate_inner_expr(expr_str, target_var, x_val):
    """Evaluates inner string expressions at x = x_val."""
    clean_expr = expr_str.strip()
    pattern = rf"\b{re.escape(target_var)}\b"
    substituted = re.sub(pattern, f"({x_val})", clean_expr)

    allowed_names = {
        "math": math, "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "exp": math.exp, "log": math.log,
    }
    try:
        return float(eval(substituted, {"__builtins__": None}, allowed_names))
    except Exception:
        return float(x_val)


def evaluate_parent_at(parent_data, target_var, x_val):
    """Evaluates total f(x) = Polynomial Part + Complex Part."""
    total_val = evaluate_poly(parent_data.get("polynomial", []), x_val)

    for term in parent_data.get("complex", []):
        term_val = term.get("const", 1.0)
        for factor in term.get("factors", []):
            funcs = factor.get("funcs", [])
            inner_str = factor.get("inner", target_var)
            power = factor.get("pow", 1.0)

            val = evaluate_inner_expr(inner_str, target_var, x_val)
            for func_name in reversed(funcs):
                if func_name in FUNC_MAP:
                    try:
                        val = FUNC_MAP[func_name](val)
                    except ValueError:
                        val = 0.0
            term_val *= (val ** power)
        total_val += term_val

    return total_val


def evaluate_derivative_at(parent_data, target_var, x_val, h=1e-5):
    """
    Numerically approximates f'(x) via central difference.

    Needed because this codebase has no symbolic differentiation for
    'complex' (transcendental/product) terms -- only differentiate_polynomial
    exists, and it only handles the pure-polynomial part. This lets the
    adaptive search below hunt for zeros of f'(x) (actual critical points)
    instead of zeros of f(x) itself.
    """
    f_plus = evaluate_parent_at(parent_data, target_var, x_val + h)
    f_minus = evaluate_parent_at(parent_data, target_var, x_val - h)
    return (f_plus - f_minus) / (2 * h)


def solve_analytic_derivative_zeros(diff_coeffs, original_coeffs):
    """Exact solver for f'(x) = 0 for degree 1, 2, or 3 derivative polynomials."""
    solutions = []
    epsilon = 0.001

    coeffs = diff_coeffs + [0.0] * (4 - len(diff_coeffs))
    c, b, a, d = coeffs[0], coeffs[1], coeffs[2], coeffs[3]
    roots = []

    # Cubic Case
    if abs(d) > 1e-12:
        A, B, C = a / d, b / d, c / d
        p = B - (A**2) / 3.0
        q = (2 * (A**3) / 27.0) - (A * B / 3.0) + C
        discriminant = (q**2 / 4.0) + (p**3 / 27.0)
        shift = A / 3.0

        if discriminant > 1e-12:
            u = math.cbrt(-q / 2.0 + math.sqrt(discriminant))
            v = math.cbrt(-q / 2.0 - math.sqrt(discriminant))
            roots.append(u + v - shift)
        elif abs(discriminant) <= 1e-12:
            if abs(q) <= 1e-12:
                roots.append(-shift)
            else:
                u = math.cbrt(-q / 2.0)
                roots.append(2 * u - shift)
                roots.append(-u - shift)
        else:
            r = math.sqrt(-(p**3) / 27.0)
            phi = math.acos(max(-1.0, min(1.0, -q / (2.0 * r))))
            cube_root_r = math.cbrt(r)
            roots.extend([
                2 * cube_root_r * math.cos(phi / 3.0) - shift,
                2 * cube_root_r * math.cos((phi + 2 * math.pi) / 3.0) - shift,
                2 * cube_root_r * math.cos((phi + 4 * math.pi) / 3.0) - shift
            ])

    # Quadratic Case
    elif abs(a) > 1e-12:
        disc = b**2 - 4 * a * c
        if disc > 0:
            roots.append((-b + math.sqrt(disc)) / (2 * a))
            roots.append((-b - math.sqrt(disc)) / (2 * a))
        elif abs(disc) <= 1e-12:
            roots.append(-b / (2 * a))

    # Linear Case
    elif abs(b) > 1e-12:
        roots.append(-c / b)

    unique_roots = []
    for r in roots:
        if not any(math.isclose(r, ur, abs_tol=1e-7) for ur in unique_roots):
            unique_roots.append(r)

    for root in unique_roots:
        root_clean = round(root, 10)
        val_center = evaluate_poly(original_coeffs, root_clean)
        val_right = evaluate_poly(original_coeffs, root_clean + epsilon)
        val_left = evaluate_poly(original_coeffs, root_clean - epsilon)

        if val_right > val_center and val_left > val_center:
            classification = "minima"
        elif val_right < val_center and val_left < val_center:
            classification = "maxima"
        else:
            classification = "inflection"

        solutions.append([root_clean, classification])

    return solutions


# ==========================================================
# 4. ADAPTIVE NUMERICAL APPROXIMATION ENGINE
# ==========================================================
def approximate_roots(parent_data, target_var="x", lower_bound=-10.0, upper_bound=10.0, runs=5):
    """Adaptive search algorithm for higher degree polynomials or complex functions."""
    solutions = []
    eps_neighbor = 0.001

    for run_idx in range(1, runs + 1):
        step_size = 1.0
        x = random.uniform(lower_bound, upper_bound)
        max_iter = 100000
        iters = 0

        y_prev = evaluate_derivative_at(parent_data, target_var, x)
        direction = -1 if y_prev > 0 else 1

        while abs(y_prev) > 1e-5 and iters < max_iter:
            iters += 1
            x_next = x + (direction * step_size)
            x_next = max(lower_bound, min(upper_bound, x_next))

            y_next = evaluate_derivative_at(parent_data, target_var, x_next)

            if (y_prev > 0 and y_next < 0) or (y_prev < 0 and y_next > 0):
                direction *= -1
                step_size /= 5.0

            x = x_next
            y_prev = y_next

        root_clean = round(x, 10)
        already_found = any(abs(root_clean - sol[0]) < 1e-4 for sol in solutions)

        if not already_found:
            val_center = evaluate_parent_at(parent_data, target_var, root_clean)
            val_right = evaluate_parent_at(parent_data, target_var, root_clean + eps_neighbor)
            val_left = evaluate_parent_at(parent_data, target_var, root_clean - eps_neighbor)

            if val_right > val_center and val_left > val_center:
                classification = "minima"
            elif val_right < val_center and val_left < val_center:
                classification = "maxima"
            else:
                classification = "inflection"

            solutions.append([root_clean, classification])

    return solutions


# ==========================================================
# 5. MAIN EXECUTION WITH REPEAT LOOP
# ==========================================================
def main():
    while True:
        print("==========================================")
        print("   MAXIMA / MINIMA CRITICAL POINT FINDER  ")
        print("==========================================")

        # 1. Collect Data from User
        data = collect_data()

        orig_poly = data.get("polynomial", [])
        has_complex = len(data.get("complex", [])) > 0
        orig_degree = len(orig_poly) - 1 if orig_poly else -1

        results = []

        if not has_complex and orig_degree >= 1:
            # Differentiate polynomial to find f'(x)
            diff_poly = differentiate_polynomial(orig_poly)
            diff_degree = len(diff_poly) - 1

            print(f"\n[STEP 1] Original Function f(x) Degree: {orig_degree}")
            print(f"[STEP 2] Differentiated f'(x) Coefficients: {diff_poly} (Degree: {diff_degree})")

            if 1 <= diff_degree <= 3:
                print("[INFO] Solving f'(x) = 0 exactly using Analytical Solvers...")
                results = solve_analytic_derivative_zeros(diff_poly, orig_poly)
            else:
                print("[INFO] f'(x) degree >= 4. Switching to Adaptive Engine...")
                try:
                    lower = float(input("  Enter LOWER bound for domain search: "))
                    upper = float(input("  Enter UPPER bound for domain search: "))
                except ValueError:
                    lower, upper = -10.0, 10.0
                results = approximate_roots(data, target_var="x", lower_bound=lower, upper_bound=upper, runs=5)
        else:
            print("\n[INFO] Mixed or Complex function detected.")
            try:
                lower = float(input("  Enter LOWER bound for domain search: "))
                upper = float(input("  Enter UPPER bound for domain search: "))
            except ValueError:
                lower, upper = -10.0, 10.0
            results = approximate_roots(data, target_var="x", lower_bound=lower, upper_bound=upper, runs=5)

        # 2. Display Results
        print("\n==========================================")
        print("             FINAL RESULTS                ")
        print("==========================================")
        if not results:
            print("No real critical points found within specified limits.")
        else:
            for idx, (root, kind) in enumerate(results, 1):
                f_val = round(evaluate_parent_at(data, "x", root), 6)
                print(f"  Point #{idx}: x = {root:<12} | f(x) = {f_val:<10} -> Classification: {kind.upper()}")
        print("==========================================\n")

        # 3. Prompt for Repeat
        again = input("Would you like to analyze another function? (y/n): ").strip().lower()
        if again != 'y':
            print("\nThank you for using the Extrema Finder Engine! Exiting...\n")
            break


if __name__ == "__main__":
    main()
