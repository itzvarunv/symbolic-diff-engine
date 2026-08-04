import re

# SPECIAL BASKET: Dictionary for Function Swaps & Signs
TRANS_DERIVATIVES = {
    "sin": ("cos", 1),
    "cos": ("sin", -1),
    "exp": ("exp", 1),
    "ln": ("1/x", 1),
    "tan": ("sec²", 1),
}


def contains_var(expr, target_var):
    """Detects target_var as an isolated variable token (e.g. '2x', 'x^2', but not 'tax')."""
    # Ensures no letter/underscore immediately precedes or follows the variable
    pattern = rf"(?<![a-zA-Z_]){re.escape(target_var)}(?![a-zA-Z_])"
    return bool(re.search(pattern, expr))


# ==========================================
# 1. REGULAR BASKET: Polynomial Engine
# ==========================================
def differentiate_regular_basket(expr_str, target_var):
    """Handles pure powers, linear terms, and polynomials (e.g., x^2, 3x, x+1)."""
    expr_clean = expr_str.replace(" ", "")

    if not contains_var(expr_clean, target_var):
        return "0"
    if expr_clean == target_var:
        return "1"

    # Match polynomial sum terms (e.g., x^2+1, 2x-5)
    expr_norm = re.sub(
        rf"(\d)({re.escape(target_var)})", r"\1*\2", expr_clean
    )
    terms = re.findall(r"[+-]?[^+-]+", expr_norm)
    diff_terms = []

    for term in terms:
        if not contains_var(term, target_var):
            continue  # Constant terms drop to 0

        match_pow = re.match(
            rf"^([+-]?\d*\.?\d*)?\*?{re.escape(target_var)}(?:\^([+-]?\d+))?$",
            term,
        )
        if match_pow:
            c1_str, p_str = match_pow.groups()
            c = (
                float(c1_str)
                if c1_str not in ("", "+", "-")
                else (-1.0 if c1_str == "-" else 1.0)
            )
            p = float(p_str) if p_str else 1.0

            new_c = c * p
            new_p = p - 1.0

            if new_p == 0:
                diff_terms.append(f"{new_c:g}")
            elif new_p == 1:
                c_fmt = (
                    ""
                    if new_c == 1
                    else ("-" if new_c == -1 else f"{new_c:g}")
                )
                diff_terms.append(f"{c_fmt}{target_var}")
            else:
                c_fmt = (
                    ""
                    if new_c == 1
                    else ("-" if new_c == -1 else f"{new_c:g}")
                )
                diff_terms.append(f"{c_fmt}{target_var}^{new_p:g}")
        else:
            diff_terms.append("1")

    if not diff_terms:
        return "0"

    res = " + ".join(diff_terms).replace("+ -", "- ")
    return f"({res})" if len(diff_terms) > 1 else res


# ==========================================
# 2. SPECIAL BASKET: Dictionary Swap Engine
# ==========================================
def differentiate_special_basket(funcs, inner_expr, target_var):
    """Swaps functions using the dictionary and recursively delegates inner derivatives to the Regular Basket."""
    if not contains_var(inner_expr, target_var):
        return "0"

    # Inner derivative processed via Regular Basket
    inner_diff = differentiate_regular_basket(inner_expr, target_var)

    if not funcs:
        return inner_diff

    derived_parts = []
    current_sign = 1.0
    current_inner = inner_expr

    for i in range(len(funcs) - 1, -1, -1):
        f = funcs[i]
        d_func, sign = TRANS_DERIVATIVES[f]
        current_sign *= sign

        if i == len(funcs) - 1:
            derived_parts.append(f"{d_func}({inner_expr})")
        else:
            derived_parts.append(f"{d_func}({current_inner})")
        current_inner = f"{f}({current_inner})"

    if inner_diff != "1" and inner_diff != "0":
        derived_parts.append(f"({inner_diff})")

    sign_str = "-" if current_sign == -1 else ""
    return sign_str + "".join(derived_parts)


# ==========================================
# 3. HYBRID FACTOR DISPATCHER
# ==========================================
def differentiate_factor(factor, target_var):
    """Routes the factor to either the Regular or Special Basket based on outer functions and powers."""
    funcs = factor["funcs"]
    inner = factor["inner"]
    p = factor.get("pow", 1)

    if not contains_var(inner, target_var):
        return "0"

    # Power Rule wrapper
    pow_coeff = f"{p}" if p != 1 else ""
    new_pow = p - 1

    base_str = inner
    for f in reversed(funcs):
        base_str = f"{f}({base_str})"

    if new_pow == 0:
        pow_str = ""
    elif new_pow == 1:
        pow_str = f"({base_str})"
    else:
        pow_str = f"({base_str})^({new_pow})"

    # Select Basket: If funcs exist -> Special Basket; else -> Regular Basket
    if funcs:
        base_diff = differentiate_special_basket(funcs, inner, target_var)
    else:
        base_diff = differentiate_regular_basket(inner, target_var)

    components = [c for c in [pow_coeff, pow_str, base_diff] if c]
    return "*".join(components) if components else "1"


# ==========================================
# 4. PRODUCT / LIST EXECUTION ENGINE
# ==========================================
def differentiate_expression_list(factors, target_var):
    """Applies Product Rule across list factors using basket derivatives."""
    sum_terms = []

    for i, target_factor in enumerate(factors):
        if not contains_var(target_factor["inner"], target_var):
            continue

        d_i = differentiate_factor(target_factor, target_var)
        if d_i == "0":
            continue

        term_copy = []
        for j, f in enumerate(factors):
            if j == i:
                term_copy.append(f"({d_i})")
            else:
                base_str = f["inner"]
                for fn in reversed(f["funcs"]):
                    base_str = f"{fn}({base_str})"
                p = f.get("pow", 1)
                term_copy.append(
                    f"({base_str})" if p == 1 else f"({base_str})^({p})"
                )

        sum_terms.append("*".join(term_copy))

    return " + ".join(sum_terms).replace("+ -", "- ") if sum_terms else "0"


# ==========================================
# 5. USER INPUT INTERACTIVE CLI
# ==========================================
def user_input_cli():
    print("==================================================")
    print("  HYBRID BASKET CAS ENGINE (USER INPUTABLE)")
    print("==================================================")

    while True:
        factors = []
        try:
            num_factors = int(
                input(
                    "\nHow many factors in this term? (e.g., 2 for division/product): "
                )
            )
        except ValueError:
            num_factors = 1

        for i in range(1, num_factors + 1):
            print(f"\n--- Factor #{i} ---")
            inner = input(
                "  Enter inner expression (e.g., x, x^2+1, 2x): "
            ).strip()

            print("  Special functions available:", ", ".join(TRANS_DERIVATIVES.keys()))
            funcs_str = input(
                "  Enter outer special functions (outermost to innermost, or blank): "
            ).strip()
            funcs = (
                [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
                if funcs_str
                else []
            )

            try:
                power = int(
                    input(
                        "  Enter power (e.g., 1 for product, -1 for division denominator): "
                    )
                    or "1"
                )
            except ValueError:
                power = 1

            factors.append({"funcs": funcs, "inner": inner, "pow": power})

        target_var = input(
            "\nDifferentiate with respect to variable (e.g., x): "
        ).strip()
        result = differentiate_expression_list(factors, target_var)

        print("\n==================================================")
        print(f"DERIVATIVE RESULT (df / d{target_var}):")
        print(result)
        print("==================================================")

        again = input("\nRun another calculation? (y/n): ").strip().lower()
        if again != "y":
            break


if __name__ == "__main__":
    user_input_cli()
