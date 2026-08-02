# Master Lookup Table for Base Derivatives
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


def differentiate_chain_stack(stack, target_var, constant=1.0):
    """Differentiates a chain stack like ['sin', 'cos', 'u']."""
    base_var = stack[-1]

    if base_var != target_var:
        return {"result_str": "0", "is_zero": True}

    func_layers = stack[:-1]

    if not func_layers:
        c_fmt = f"{constant:g}" if constant != 1.0 else ""
        return {"result_str": f"{c_fmt}{base_var}", "is_zero": False}

    derived_parts = []
    current_sign = 1.0
    inner_expr = base_var

    for i in range(len(func_layers) - 1, -1, -1):
        f = func_layers[i]
        d_func, sign = BASE_DERIVATIVES[f]
        current_sign *= sign

        if i == len(func_layers) - 1:
            if d_func == "1/x":
                derived_parts.append(f"(1/{base_var})")
            else:
                derived_parts.append(f"{d_func}({base_var})")
        else:
            if "x" in d_func:
                term = d_func.replace("x", inner_expr)
            else:
                term = f"{d_func}({inner_expr})"
            derived_parts.append(term)

        inner_expr = f"{f}({inner_expr})"

    final_const = constant * current_sign
    if final_const == 1:
        c_str = ""
    elif final_const == -1:
        c_str = "-"
    else:
        c_str = f"{final_const:g}"

    return {"result_str": c_str + "".join(derived_parts), "is_zero": False}


def differentiate_multi_term(term_data, target_var):
    """Differentiates a multi-variable product term without '*'."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    target_idx = -1
    for idx, stack in enumerate(brackets):
        if stack[-1] == target_var:
            target_idx = idx
            break

    if target_idx == -1:
        return "0"

    diff_res = differentiate_chain_stack(
        brackets[target_idx], target_var, constant=1.0
    )
    if diff_res["is_zero"]:
        return "0"

    parts = []
    for idx, stack in enumerate(brackets):
        if idx == target_idx:
            parts.append(f"({diff_res['result_str']})")
        else:
            b_var = stack[-1]
            funcs = stack[:-1]
            expr = b_var
            for f in reversed(funcs):
                expr = f"{f}({expr})"
            parts.append(expr)

    c_fmt = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")
    return c_fmt + "".join(parts)


def format_term_display(term_data):
    """Formats a term dictionary cleanly without '*'."""
    brackets = term_data.get("brackets", [])
    const = term_data.get("const", 1.0)

    c_str = "" if const == 1.0 else ("-" if const == -1.0 else f"{const:g}")
    b_strs = []

    for stack in brackets:
        b_var = stack[-1]
        funcs = stack[:-1]
        expr = b_var
        for f in reversed(funcs):
            expr = f"{f}({expr})"
        b_strs.append(expr)

    return c_str + "".join(b_strs)


def display_current_system(system_terms):
    print("\n--- CURRENT FUNCTION SYSTEM ---")
    if not system_terms:
        print("f(...) = 0 (No terms added yet)")
    else:
        formatted = [format_term_display(t) for t in system_terms]
        print("f(...) = " + " + ".join(formatted).replace("+ -", "- "))
    print("-------------------------------\n")


def main_menu():
    system_terms = []

    while True:
        print("===============================")
        print("    DIFFERENTIATION MENU      ")
        print("===============================")
        print("1. Add Single Composite Term (e.g. 3sin(cos(u)))")
        print("2. Add Multi-Variable Product Term (e.g. 4sin(u)exp(h))")
        print("3. Display Current System")
        print("4. Differentiate System (Partial / Total)")
        print("5. Reset All Terms")
        print("E. Exit")

        choice = input("\nChoose an option: ").strip().upper()

        if choice == "1":
            var_name = input(
                "Enter custom variable name (e.g. u, h, x, theta): "
            ).strip()
            try:
                const = float(
                    input("Enter constant multiplier (default 1.0): ") or "1.0"
                )
            except ValueError:
                const = 1.0

            print("\nSupported functions:", ", ".join(BASE_DERIVATIVES.keys()))
            funcs_str = input(
                "Enter nested functions from OUTSIDE to INSIDE separated by commas (e.g. sin, cos): "
            ).strip()

            func_list = (
                [f.strip().lower() for f in funcs_str.split(",") if f.strip()]
                if funcs_str
                else []
            )

            valid = True
            for f in func_list:
                if f not in BASE_DERIVATIVES:
                    print(f"Error: Function '{f}' is not supported!")
                    valid = False
                    break

            if valid:
                stack = func_list + [var_name]
                system_terms.append({"brackets": [stack], "const": const})
                print("Term added successfully!")
                display_current_system(system_terms)

        elif choice == "2":
            try:
                const = float(
                    input("Enter total constant multiplier (default 1.0): ")
                    or "1.0"
                )
            except ValueError:
                const = 1.0

            num_vars = int(
                input("How many different variables in this product term?: ")
            )
            brackets = []

            for i in range(1, num_vars + 1):
                print(f"\n--- Variable #{i} ---")
                var_name = input("Enter variable name (e.g. u, h, x): ").strip()
                funcs_str = input(
                    f"Enter functions for {var_name} (outer to inner, or press Enter for plain {var_name}): "
                ).strip()

                func_list = (
                    [
                        f.strip().lower()
                        for f in funcs_str.split(",")
                        if f.strip()
                    ]
                    if funcs_str
                    else []
                )

                stack = func_list + [var_name]
                brackets.append(stack)

            system_terms.append({"brackets": brackets, "const": const})
            print("\nMulti-variable product term added!")
            display_current_system(system_terms)

        elif choice == "3":
            display_current_system(system_terms)

        elif choice == "4":
            if not system_terms:
                print("\nNo terms to differentiate! Please add terms first.")
                continue

            display_current_system(system_terms)
            target_var = input(
                "Which variable do you want to differentiate with respect to?: "
            ).strip()

            diff_results = []
            for term in system_terms:
                res = differentiate_multi_term(term, target_var)
                if res != "0":
                    diff_results.append(res)

            print("\n==========================================")
            print(f" PARTIAL DERIVATIVE: ∂f / ∂{target_var}")
            print("==========================================")
            if not diff_results:
                print(f"∂f / ∂{target_var} = 0")
            else:
                out = " + ".join(diff_results).replace("+ -", "- ")
                print(f"∂f / ∂{target_var} = {out}")
            print("==========================================\n")

        elif choice == "5":
            system_terms.clear()
            print("\nSystem cleared!")

        elif choice == "E":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main_menu()
