import sympy as sp


def format_term(var_name, power):
    # Map numbers to clean unicode superscript digits
    superscripts = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    power_str = str(power).translate(superscripts)
    return f"{var_name}{power_str}"


def term_collection():
    while True:
        try:
            terms = int(input("How many terms: "))
            if terms > 0:
                break
            else:
                print("Invalid integer selected!")
        except Exception:
            print("Ran into an error please try again!")
    return terms


powers = {}


def get_name(powers):
    while True:
        try:
            name = input("Give the name for your variable: ")
            powers[name] = []
            break
        except Exception:
            print("Please try again!")
    return powers, name


def integrate(name, powers):
    bases = powers[name]

    while True:
        try:
            constant_c = float(
                input("Enter the value you would like to set for constant (C): ")
            )
            break
        except ValueError:
            print("Invalid input! Please enter a valid number.")

    # Insert constant at index 0
    bases.insert(0, constant_c)

    # Traverse from index 1, dividing each coefficient by power and incrementing power
    power = 1
    for index in range(1, len(bases)):
        bases[index] = bases[index] / power
        power += 1

    powers[name] = bases
    return powers


def show_answers(what, powers):
    if what == 1:
        for variable in powers:
            bases = powers[variable]
            show = sp.Symbol(variable)
            stop = len(bases) - 1
            start = 0
            for number in bases:
                term_str = format_term(show, start)

                if start != stop:
                    print(f"{number}{term_str} + ", end="")
                else:
                    print(f"{number}{term_str}")
                start += 1
        print()


def menu(stop, powers):
    print("Enter 1 to integrate while 'E' to exit")
    choice = input("What do you choose?: ")
    if choice.upper().strip() == "E":
        print("Goodbye ;)")
        return True
    elif choice.strip() == "1":
        while True:
            try:
                name = input(
                    "Which variable which you had created to be integrated?: "
                )
                if name in powers:
                    powers = integrate(name, powers)
                    show_answers(1, powers)
                    break
                else:
                    print("Variable not found")
            except Exception as e:
                print(f"Error details: {e}")
    else:
        print("Please enter a valid choice!")
    return stop


if __name__ == "__main__":
    terms = term_collection()

    while True:
        try:
            variables = int(input("How many variables are you using: "))
            if variables > 0:
                break
            else:
                print("Invalid integer selected")
        except Exception:
            print("Ran into an error please again!")

    for i in range(1, variables + 1):
        print(f"Doing progress of variable {i}...")
        powers, name = get_name(powers)
        bases = powers[name]
        for j in range(terms + 1):
            term_display = format_term(name, j)
            while True:
                try:
                    value = float(
                        input(f"Enter the constant before {term_display}: ")
                    )
                    break
                except Exception:
                    print("Try again!")
            bases.append(value)
        powers[name] = bases
        print()

    stop = False
    while not stop:
        stop = menu(stop, powers)
        print()
