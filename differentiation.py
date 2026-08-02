import re

BASE_DERIVATIVES = {
    "sin": ("cos", 1),
    "cos": ("sin", -1),
    "tan": ("sec²", 1),
    "exp": ("exp", 1),
    "ln": ("1/x", 1),
    "arcsin": ("1/√(1-x²)", 1),
    "arccos": ("1/√(1-x²)", -1),
    "arctan": ("1/(1+x²)", 1),
}


def contains_var(expr, target_var):
    """Uses regex word boundary to prevent substring false positives (e.g., 'x' inside 'tax')."""
    return bool(re.search(rf"\b{re.escape(target_var)}\b", expr))


def diff_expression(expr_str, target_var):
    """Differentiates linear/polynomial expressions (e.g. x+1, x^2+1, 2*x, x*2)."""
    expr_str = expr_str.replace(" ", "")

    if not contains_var(expr_str, target_var):
        return "0"

    # Match polynomial sum terms like x^2+1, 2x-5, x^2+3x+2
    # Standardize explicit multiplication for parsing
    expr_clean = re.sub(
        rf"(\d)({re.escape(target_var)})", r"\1*\2", expr_str
    )

    # Split expression into addition/subtraction terms while retaining signs
    terms = re.findall(r"[+-]?[^+-]+", expr_clean)
    diff_terms = []

    for term in terms:
        if not contains_var(term, target_var):
            continue  # Constants drop to 0

        # Match c*x^n or x^n*c or c*x or x*c or x^n
        match_pow = re.match(
            rf"^([+-]?\d*\.?\d*)?\*?{re.escape(target_var)}(?:\^(\d+))?\*?(\d*\.?\d*)?$",
            term,
        )
        if match_pow:
            c1_str, p_str, c2_str = match_pow.groups()

            # Calculate total coefficient
            c1 = (
                float(c1_str)
                if c1_str not in ("", "+", "-")
                else (-1.0 if c1_str == "-" else 1.0)
            )
            c2 = float(c2_str) if c2_str else 1.0
            coeff = c1 * c2

            p = int(p_str) if p_str else 1

            new_c = coeff * p
            new_p = p - 1

            if new_p == 0:
                c_fmt = f"{new_c:g}"
                diff_terms.append(c_fmt)
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
                diff_terms.append(f"{c_fmt}{target_var}^{new_p}")
        else:
            # Fallback if unparseable complex inner term
            diff_terms.append("1")

    if not diff_terms:
        return "0"

    result = " + ".join(diff_terms).replace("+ -", "- ")
    return f"({result})" if len(diff_terms) > 1 else result


def differentiate_chain_stack(funcs, inner_expr, target_var, constant=1.0):
    """Applies Chain Rule with inner expressions using word boundary checks."""
    if not contains_var(inner_expr, target_var):
        return {"result_str": "0", "is_zero": True}

    inner_diff = diff_expression(inner_expr, target_var)

    if not funcs:
        c_fmt = f"{constant:g}" if constant != 1.0 else ""
        return {"result_str": f"{c_fmt}{inner_diff}", "is_zero": False}

    derived_parts = []
    current_sign = 1.0
    current_inner = inner_expr

    for i in range(len(funcs) - 1, -1, -1):
        f = funcs[i]
        d_func, sign = BASE_DERIVATIVES[f]
        current_sign *= sign

        if i == len(funcs) - 1:
            if d_func == "1/x":
                derived_parts.append(f"(1/({inner_expr}))")
            else:
                derived_parts.append(f"{d_func}({inner_expr})")
        else:
            term = f"{d_func}({current_inner})"
            derived_parts.append(term)

        current_inner = f"{f}({current_inner})"

    if inner_diff != "1":
        derived_parts.append(f"({inner_diff})")

    final_const = constant * current_sign
    c_str = (
        "" if final_const == 1 else ("-" if final_const == -1 else f"{final_const:g}")
    )

    return {"result_str": c_str + "".join(derived_parts), "is_zero": False}


def build_bracket_str(b):
    """Utility to render a bracket representation as string."""
    expr = b["inner"]
    for f in reversed(b["funcs"]):
        expr = f"{f}({expr})"
    return expr


def differentiate_multi_term(term_data, target_var):
    """Applies Product Rule when multiple brackets share the target variable."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    target_indices = [
        i for i, b in enumerate(brackets) if contains_var(b["inner"], target_var)
    ]

    if not target_indices:
        return "0"

    product_terms = []

    # Product Rule sum over matching target indices: sum( d(b_i)/dx * prod_{j!=i} b_j )
    for target_idx in target_indices:
        diff_res = differentiate_chain_stack(
            brackets[target_idx]["funcs"],
            brackets[target_idx]["inner"],
            target_var,
            constant=1.0,
        )

        if diff_res["is_zero"]:
            continue

        parts = []
        for i, b in enumerate(brackets):
            if i == target_idx:
                parts.append(f"({diff_res['result_str']})")
            else:
                parts.append(build_bracket_str(b))

        product_terms.append("".join(parts))

    if not product_terms:
        return "0"

    combined = " + ".join(product_terms).replace("+ -", "- ")
    c_fmt = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")

    return f"{c_fmt}({combined})" if len(product_terms) > 1 and const != 1.0 else f"{c_fmt}{combined}"


def format_term_display(term_data):
    """Formats terms cleanly for display."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    c_str = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")
    b_strs = [build_bracket_str(b) for b in brackets]

    return c_str + "".join(b_strs)


def display_current_system(system_terms):
    print("\n--- CURRENT FUNCTION SYSTEM ---")
    if not system_terms:
        print("f(...) = 0")
    else:
        formatted = [format_term_display(t) for t in system_terms]
        print("f(...) = " + " + ".join(formatted).replace("+ -", "- "))
    print("-------------------------------\n")


def main_menu():
    system_terms = []

    while True:
        print("===============================")
        print("    DIFFERENTIATION MENU v2.1   ")
        print("===============================")
        print("1. Add Single/Composite Term (e.g. 5cos(x+1))")
        print("2. Add Product Term (e.g. sin(u)exp(u))")
        print("3. Display Current System")
        print("4. Differentiate System")
        print("5. Reset System")
        print("E. Exit")

        choice = input("\nChoose an option: ").strip().upper()

        if choice == "1":
            try:
                const = float(
                    input("Enter constant multiplier (default 1.0): ") or "1.0"
                )
            except ValueError:
                const = 1.0

            inner = input(
                "Enter inner expression (e.g. x+1, 2x, x^2+1): "
            ).strip()

            print("Supported functions:", ", ".join(BASE_DERIVATIVES.keys()))
            funcs_str = input(
                "Enter outer functions from outside to inside (e.g. cos) or leave blank: "
            ).strip()

            func_list = (
                [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
                if funcs_str
                else []
            )

            system_terms.append(
                {"brackets": [{"funcs": func_list, "inner": inner}], "const": const}
            )
            print("Term added successfully!")
            display_current_system(system_terms)

        elif choice == "2":
            try:
                const = float(
                    input("Enter constant multiplier (default 1.0): ") or "1.0"
                )
            except ValueError:
                const = 1.0

            num_factors = int(input("How many factors in this product term?: "))
            brackets = []

            for i in range(1, num_factors + 1):
                print(f"\n--- Factor #{i} ---")
                inner = input("Enter inner expression (e.g. u, u+1): ").strip()
                funcs_str = input("Enter functions (comma separated or blank): ").strip()
                func_list = (
                    [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
                    if funcs_str
                    else []
                )
                brackets.append({"funcs": func_list, "inner": inner})

            system_terms.append({"brackets": brackets, "const": const})
            print("Product term added successfully!")
            display_current_system(system_terms)

        elif choice == "3":
            display_current_system(system_terms)

        elif choice == "4":
            if not system_terms:
                print("\nNo terms to differentiate!")
                continue

            target_var = input(
                "Differentiate with respect to variable (e.g. x, u): "
            ).strip()
            diff_results = []

            for term in system_terms:
                res = differentiate_multi_term(term, target_var)
                if res != "0":
                    diff_results.append(res)

            print("\n==========================================")
            print(f" DERIVATIVE w.r.t {target_var}:")
            print("==========================================")
            if not diff_results:
                print(f"∂f / ∂{target_var} = 0")
            else:
                out = " + ".join(diff_results).replace("+ -", "- ")
                print(f"∂f / ∂{target_var} = {out}")
            print("==========================================\n")

        elif choice == "5":
            system_terms.clear()
            print("\nCleared system!")

        elif choice == "E":
            break


if __name__ == "__main__":
    main_menu()
