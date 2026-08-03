# Symbolic Calculus Toolkit

Two terminal-based tools sharing a common representation for functions — a symbolic differentiation engine and a numerical (Simpson's rule) definite integration engine — plus the rudimentary precursors each was built up from.

Both tools operate on the same underlying model: a function system is a list of **terms**, each term has a `const` multiplier and one or more **brackets** (`{"funcs": [...], "inner": "..."}` — an outer function chain applied to an inner expression). Differentiation works on this model symbolically, string-in string-out; integration works on it numerically, evaluating it at sample points and running Simpson's rule.

## Files

| File | What it does |
|---|---|
| `differentiation.py` | Symbolic partial/total differentiation over the term/bracket model — chain rule, product rule, polynomial inner expressions. |
| `differentiation_rudimentary.py` | The precursor: single-variable polynomials as coefficient lists, power rule applied directly on the list (pop constant, multiply by power, shift). Where the whole thing started. |
| `Integration.py` | Numerical definite integration over the same term/bracket model, via Simpson's 1/3 rule. Imports `BASE_DERIVATIVES` from `differentiation.py` for its supported-function list. |
| `Integration_rudimentary.py` | The integration mirror of the differentiation precursor: coefficient-list power-rule integration (insert constant of integration, divide each shifted coefficient by its new power). |
| `test.py` | Accuracy benchmark for `Integration.py` against SciPy's `quad` on a compound trig product — matches to 10 decimal places. |

## Why the rudimentary versions exist

Both started as coefficient-list power-rule tools — correct by construction, since a list of polynomial coefficients is closed under both differentiation and integration (differentiate/integrate a degree-n polynomial, you get a degree-(n∓1) polynomial in the exact same list structure). No parsing, nothing to mis-tokenize.

The upgrade to `differentiation.py` / `Integration.py` trades that safety for expressiveness: arbitrary strings (`x+1`, `sin(u)exp(u)`, `x^2+3x+2`) instead of a fixed-shape coefficient list. That's a much bigger jump than it looks — every new syntax shape is a new case the parser either handles or silently mishandles, which is exactly where the bugs below live. None of them show up in the rudimentary files, because there's no string parsing surface for a bug to hide in.

## Running them

```bash
python3 differentiation.py     # symbolic differentiation menu
python3 Integration.py         # numerical definite integration menu
python3 test.py                # runs the SciPy accuracy benchmark (needs scipy: pip install scipy)
```

`Integration.py` imports directly from `differentiation.py`, so keep them in the same directory.

## Known bugs — not fixed yet, flagging for future-me

These are documented rather than patched for now, since the fixes aren't obvious yet. Listed here so they don't get rediscovered from scratch later.

### In `differentiation.py`

- **Coefficient directly attached to a variable reads as "variable not present."** `diff_expression("2x", "x")` returns `"0"` instead of `"2"`, and `differentiate_chain_stack(["sin"], "2x", "x")` comes back `is_zero: True` — the whole term silently vanishes. Root cause: `contains_var` uses `\b{var}\b`, and regex word boundaries don't exist between two word characters (digits count as word characters), so there's no boundary between `2` and `x`. The multiplication-standardizing substring substitution (`digit·var` → `digit*var`) only runs *inside* `diff_expression`, after the `contains_var` gate has already rejected the raw string. Suspect the fix involves running that substitution earlier, before the gate check — haven't nailed down the cleanest way to do that without breaking the cases that currently work.
- **Products inside an inner expression still aren't parsed.** `x*sin(x)` as an inner string falls through to the generic `1` fallback (with a warning printed, at least). The polynomial matcher only handles sums of `c*x^n` terms — it has no notion of a product of two sub-expressions where one isn't a bare polynomial term.
- **`simplify_expression_str` can leave a dangling operator.** `simplify_expression_str("cos(x)*(1)")` → `"cos(x)*"`. The `\(1\)` removal regex eats the `(1)` before the `\*1\b` cleanup regex gets a chance to see the full `*1` shape.

### In `Integration.py`

- **Naming your variable after a reserved constant or function silently corrupts the entire integral.** `evaluate_term_factor` builds its eval environment as one dict literal:
  ```python
  eval_env = {
      target_var: float(var_value),
      "sin": math.sin, ..., "pi": math.pi, "e": math.e,
  }
  ```
  If `target_var` is `"e"`, `"pi"`, `"sin"`, `"cos"`, `"tan"`, `"exp"`, `"log"`, `"ln"`, or `"sqrt"`, that key appears twice in the literal and the later one wins — so the actual sweep value gets silently overwritten by the constant/function. Confirmed directly: integrating `f(e) = e` from 0 to 10 (a straight line, should be 50) returns `27.18...` — every sample point evaluated `e` as `math.e` regardless of where the sweep actually was. No error, no warning, just a wrong-but-plausible number.
- **Domain errors evaluate to `0.0` instead of failing loudly.** `arcsin(2)` and `ln(-1)` (both undefined) silently return `0.0` in `evaluate_term_factor`'s `except` block. If a definite integral's bounds sweep through a domain-invalid region for one of the functions in use, Simpson's rule just treats those points as zero-area contributions instead of surfacing that the integral doesn't exist over that range.

## Verified working

- Simpson's rule itself (even-step correction, 1-4-2-4...-1 weighting, `h/3` scaling) — matches SciPy's `quad` to 10 decimal places on `test.py`'s compound trig product test.
- Reversed bounds correctly flip the sign of the result.
- Product rule in `differentiation.py` is genuinely correct (verified against `sin(u)exp(u)` differentiated w.r.t. `u`).
- Nested transcendental inner expressions in `differentiation.py` (e.g. `cos(sin(x))`) differentiate correctly via recursion.

## Requirements

Python 3, standard library only for both engines. `test.py` additionally needs `scipy` (`pip install scipy`) to run the accuracy benchmark — it's optional; without it, `test.py` just skips the verification step. The rudimentary files need `sympy`, used only for display formatting, not for any actual symbolic math.
