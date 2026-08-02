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


def diff_expression(expr_str, target_var):
    """Differentiates basic polynomial/linear inner expressions like '2x+1' or 'x^2'."""
    expr_str = expr_str.replace(" ", "")

    # Match simple linear/polynomial patterns (e.g. 2x, x, x^2, x+1)
    if expr_str == target_var:
        return "1"

    # Match ax^n
    match_pow = re.match(
        rf"^([+-]?\d*\.?\d*){re.escape(target_var)}\^(\d+)$", expr_str
    )
    if match_pow:
        coeff_str, p_str = match_pow.groups()
        coeff = float(coeff_str) if coeff_str not in ("", "+", "-") else (
            -1.0 if coeff_str == "-" else 1.0
        )
        p = int(p_str)
        new_c = coeff * p
        new_p = p - 1
        c_fmt = f"{new_c:g}" if new_c != 1 else ""
        return f"{c_fmt}{target_var}^{new_p}" if new_p > 1 else f"{c_fmt}{target_var}"

    # Match ax + b or ax - b
    match_lin = re.match(
        rf"^([+-]?\d*\.?\d*){re.escape(target_var)}([+-]\d+\.?\d*)?$", expr_str
    )
    if match_lin:
        coeff_str = match_lin.group(1)
        coeff = float(coeff_str) if coeff_str not in ("", "+", "-") else (
            -1.0 if coeff_str == "-" else 1.0
        )
        return f"{coeff:g}"

    return "1"  # Default fallback for unparsed inner derivatives


def differentiate_chain_stack(funcs, inner_expr, target_var, constant=1.0):
    """Applies Chain Rule with custom inner expressions like cos(x+1)."""
    if target_var not in inner_expr:
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

    # Multiply by inner derivative if it's not 1
    if inner_diff != "1":
        derived_parts.append(f"({inner_diff})")

    final_const = constant * current_sign
    c_str = "" if final_const == 1 else ("-" if final_const == -1 else f"{final_const:g}")

    return {"result_str": c_str + "".join(derived_parts), "is_zero": False}


def differentiate_multi_term(term_data, target_var):
    """Differentiates products handling inner functions."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    target_indices = [
        i for i, b in enumerate(brackets) if target_var in b["inner"]
    ]

    if not target_indices:
        return "0"

    # Single matching variable in term
    if len(target_indices) == 1:
        idx = target_indices[0]
        diff_res = differentiate_chain_stack(
            brackets[idx]["funcs"], brackets[idx]["inner"], target_var, constant=1.0
        )
        if diff_res["is_zero"]:
            return "0"

        parts = []
        for i, b in enumerate(brackets):
            if i == idx:
                parts.append(f"({diff_res['result_str']})")
            else:
                expr = b["inner"]
                for f in reversed(b["funcs"]):
                    expr = f"{f}({expr})"
                parts.append(expr)

        c_fmt = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")
        return c_fmt + "".join(parts)

    return "0"


def format_term_display(term_data):
    """Formats expressions nicely without '*'."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    c_str = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")
    b_strs = []

    for b in brackets:
        expr = b["inner"]
        for f in reversed(b["funcs"]):
            expr = f"{f}({expr})"
        b_strs.append(expr)

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
        print("    DIFFERENTIATION MENU v2    ")
        print("===============================")
        print("1. Add Composite Term with Inner Expr (e.g. 5cos(x+1))")
        print("2. Display Current System")
        print("3. Differentiate System")
        print("4. Reset System")
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
                "Enter inner expression (e.g. x+1, 2u, x^2): "
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
            display_current_system(system_terms)

        elif choice == "3":
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

        elif choice == "4":
            system_terms.clear()
            print("\nCleared system!")

        elif choice == "E":
            break


if __name__ == "__main__":
    main_menu()
