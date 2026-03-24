---
name: cris
description: Applies Cris's coding philosophy and edicts to production code and tests. Use when generating or reviewing code, implementing features, refactoring, writing unit tests, or when the user asks for code changes.
---

# Cris's Coding Philosophy and Edicts

Apply these whenever generating or suggesting code or tests.

## Core Philosophy

- **Simple is best.** Prefer language primitives and straightforward constructs over more complex solutions.
- **When complexity is necessary, document it.** Explain the reason and approach so future readers can follow.

## Priority Order

Code should be, in this order:

1. **Functional** — Correct and complete.
2. **Maintainable** — Easy to understand and change.
3. **Performant** — Efficient enough for the context; never at the cost of clarity when the difference is negligible.

## Maintainability

- Maintainable code is easy to understand. Poorly organized or structured code is hard to understand.
- **Plain English:** Name functions and variables so they read like plain English when possible—callable names should read as what they do; value names should read as what they hold (subject to language syntax and idioms).
- **Variable and parameter names:** Spell things out. The name should read like plain language at the call site: a reader should not need context, comments, or a glossary to know what the value is.
- **Name length:** Use as many characters as clarity requires. Do not shorten names to "save space" in the editor. Clarity beats brevity.
- **Abbreviations:** Do not abbreviate domain words unless the abbreviation is a universal industry standard in *this* codebase (and is used consistently everywhere). Examples of what **not** to do: `ing` for `ingredient`, `cust` for `customer`, `qty` for `quantity`, `msg` for `message`, `tmp` / `data` / `obj` as placeholders for real concepts. If the full word feels long, that usually means the value needs a more specific name (e.g. `ingredient_id` vs `ingredient`), not a shorter abbreviation.
- **Short names:** `x`, `n`, `i`, `tmp` are only acceptable in tiny scopes where convention is obvious (e.g. loop index `i`, short math). For business or persisted data, use the real noun.
- **Naming review test:** If you would expand the abbreviation when explaining this line out loud to a teammate, use the expanded form in code. When in doubt, use the longer, explicit name.
- **Booleans:** Always prefix with `is_` or `has_`. Use `is_` for states and conditions (e.g. `is_active`, `is_empty`); use `has_` for presence or possession (e.g. `has_permission`, `has_errors`). Applies to variables, parameters, attributes, properties, and functions that return a bool (predicates).
- **Lists:** Name list-typed values with plural nouns when possible (e.g. `ingredients`, `order_lines`). When iterating, use `for <singular> in <plural>` (e.g. `for ingredient in ingredients:`) so the loop reads like English.
- **Concepts:** Well organized (clear modules, layers, and boundaries).
- **Functions:** Do one discrete thing; avoid multi-purpose or side-effect-heavy functions. Name them in plain English like a short verb phrase (e.g. what the caller is asking to happen).
- **Constants:** Use only for static values; no computed or mutable "constants."

## Organizing code

- **Shared state → class.** If several functions share mutable or long-lived state (instance fields, loaded config, connections, caches, or anything you would thread through parameters as a bundle), use a class. Do not hide that coupling in module-level globals or ad-hoc dicts passed everywhere.
- **One class, one goal.** A class should have a single, obvious responsibility. If you cannot state its goal in one short sentence, split it.
- **Goal-aligned logic stays on the class.** Any helper that exists only to serve that class’s goal—and would not be called as a standalone utility by unrelated code—must be a method (including `_` helpers), not a module-level function next to the class.
- **Module-level functions are for reuse without shared state.** Prefer top-level functions only when the operation is clearly generic, stateless, or shared by multiple types of callers. If it only makes sense next to one class, it belongs inside that class.
- **Default assumption:** New behavior that needs context → method on the object that owns that context; prove otherwise before adding a free function.

## Code Smells to Avoid

- **Many parameters** — A function with a lot of parameters is usually a sign that the design is too complex. Prefer smaller, focused functions or structured arguments (e.g. objects/dataclasses) where appropriate.
- **High cyclomatic complexity** — Too many branches in one function, or nested loops that stack up, usually means the implementation should be split (helpers, smaller functions, clearer data structures). Call this out in code review when you see it; refactor before it spreads.
- **Hard or overly complex unit tests** — If tests are difficult to write or become very complex, the code under test is likely poorly structured. Improve structure and boundaries so tests stay simple.
- **Unnecessary `else`** — If you can express the logic without an `else`, do so (e.g. early returns, guard clauses, or separate branches instead of deep if/else chains).

## Unit tests

Treat test code with the same standards as production code: naming, structure, clarity, and scope discipline.

### Isolation and I/O

- Prefer **not** calling real external services from unit tests when you can avoid it. Use **mocking**, **stubs**, and tools like **VCR** (or equivalent) so tests stay fast, deterministic, and offline-friendly.

### Fixtures and data

- **Large or complex fixtures** (big YAML/JSON blobs, huge inline dicts) belong in a **separate file** (or dedicated factory/module), not pasted in the middle of a test module.

### Parameterization

- **Parameterized tests** and **`subTest`** (or the test runner’s equivalent) are encouraged: they cut duplication and make it natural to cover multiple inputs and expected outcomes in one place.

### Data setup with Django / Factory Boy

- Prefer **factories** over hand-built model graphs. Use **traits** (and related Factory Boy patterns) to express variations (“with orders”, “vegan customer”, etc.) instead of copy-pasting setup.

### What kind of test is this?

- **HTTP / API endpoints:** Treat these more like **integration tests**: exercise the real route, then assert on status, shape, and key fields of the response.
- **Classes and pure functions:** Treat these as **unit tests**: build minimal inputs (often via factories), call the unit, assert on return value or side effects you control.

### Shape of a good test

Aim for the same story every time: **starting state** (arrange) → **run the code under test** (act) → **verify outcomes** (assert). Readers should see what went in and what should come out without hunting.
