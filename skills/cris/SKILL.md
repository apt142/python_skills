---
name: "cris"
description: "Applies Cris's coding philosophy and edicts to production code, tests, and commit messages. Use when generating or reviewing code, implementing features, refactoring, writing unit tests, writing commit messages, or when the user asks for code changes."
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

## Replacing an existing function

When new code supersedes an existing function, keep the old name on the old behavior and give the replacement its own name.

- **Do not rename the old function to `<name>_legacy` and slot the new one in under the old name.** Anyone familiar with the code will read the familiar name and assume the familiar contents. Reusing a name for different behavior makes the code lie to the people who know it best.
- **Give the new function a new name that describes what it does**, where a better name exists.
- **Mark the old function `@deprecated`** (`typing_extensions.deprecated`) with a message pointing to the replacement, e.g. `@deprecated("Use get_available_swap_ids instead.")`.
- **Why:** the code tells the story by itself. A reader sees the old function, sees it is deprecated, and is pointed at its successor without digging through git history.

## Comments and docstrings

Comments are for a future human, and that human is capable. Give them the intent and let them work out the rest.

### Talk to Cris in the chat, not in the code

Comments describe the code for a future reader. They are not a channel for explaining the current edit. Anything about what was changed, why it was changed, or what to review goes in the chat response.

- No change-narration comments: `# Added null check`, `# Updated per request`, `# New helper for X`, `# Refactored to use Y`, `# Changed from Z`.
- No notes addressed to the reviewer: `# NOTE: you may want to...`, `# TODO(claude): confirm this`. Raise the question in the chat instead.
- If a comment would stop being true or useful once the change is merged, it does not belong in the code.

### Docstrings

Good names already do most of the explaining. A docstring adds what the name cannot.

- **One or two sentences** for a function or class description. Say what it is for, or the non-obvious thing about how it behaves. If it needs a paragraph, the design probably needs another look, or the extra detail belongs in an inline comment next to the tricky line.
- **Do not document parameters or return values by default.** Skip `Args:` / `Returns:` / `Raises:` sections that only restate names and types. Document an input or output only when something about it is non-standard or tricky, for example:
  - units or scale that the name and type do not carry (seconds vs milliseconds, 0–1 vs 0–100)
  - a sentinel or special meaning (`None` means "use the default", `-1` means "unbounded")
  - an accepted shape looser or stricter than the type suggests
  - the argument is mutated
  - an ordering or uniqueness assumption the caller has to satisfy
- **When you do call out an input, mention only that input.** Do not fill out the rest of the parameter list for symmetry.

Too much:

```python
def load_ingredient_substitutions(customer_id: int, is_including_inactive: bool = False) -> list[Substitution]:
    """
    Loads ingredient substitutions for a customer.

    This function queries the database for all substitutions associated with
    the given customer and returns them as a list.

    Args:
        customer_id: The ID of the customer.
        is_including_inactive: Whether to include inactive substitutions.

    Returns:
        A list of Substitution objects.
    """
```

About right:

```python
def load_ingredient_substitutions(customer_id: int, is_including_inactive: bool = False) -> list[Substitution]:
    """Substitutions the customer has chosen, most recent first."""
```

With a tricky input:

```python
def schedule_retry(job: Job, delay: float | None = None) -> None:
    """
    Requeue a failed job with backoff.

    `delay` is in seconds; None uses the job's own backoff policy rather than zero.
    """
```

### Writing comments well

- **Describe intention, not directives or absolutes.** Say what something is *for*, not what callers must do. Prefer "Intended to be built once per request" over "Built once per request"; prefer "meant to be tunable without a deploy" over "takes effect within five minutes."
- **Say when a property holds by convention rather than enforcement.** If nothing in the code guarantees the thing you are describing, name that. `"...; nothing enforces this beyond convention, so avoid calling it again mid-request"` is more useful than a confident claim a reader can disprove in one grep.
- **Comments that overclaim poison the well.** A reader who finds one comment that does not match the code starts skipping all of them. An accurate, humble comment is worth more than a precise, brittle one.
- **Verify a claim before carrying it forward.** A comment inherited from moved or refactored code may have been wrong, or may have gone stale where it sat. If it asserts something checkable — "this is a lazily-resolved proxy", "this is called once per request" — check it before reproducing it, and rewrite it around the reason that actually holds.
- **Do not restate behavior that is determined elsewhere.** Point at where it is decided instead. Two statements of the same fact will drift, and the comment is the copy that loses.
- **Avoid telling the reader what to do.** They are not present to argue back, and they usually have context the author did not. Explain the why; trust them with the what.
- **Do not narrate history.** No "recently refactored," "moved from," "this used to be called." Describe the code as it is now.
- **Annotate rather than delete when something is deliberately unused.** A field kept for a planned feature is better marked `# Reserved. Not used yet` than removed — it preserves intent, and removal can carry migration or config risk that deletion alone does not reveal.

## Organizing code

- **Shared state → class.** If several functions share mutable or long-lived state (instance fields, loaded config, connections, caches, or anything you would thread through parameters as a bundle), use a class. Do not hide that coupling in module-level globals or ad-hoc dicts passed everywhere.
- **One class, one goal.** A class should have a single, obvious responsibility. If you cannot state its goal in one short sentence, split it.
- **Goal-aligned logic stays on the class.** Any helper that exists only to serve that class's goal—and would not be called as a standalone utility by unrelated code—must be a method (including `_` helpers), not a module-level function next to the class.
- **Module-level functions are for reuse without shared state.** Prefer top-level functions only when the operation is clearly generic, stateless, or shared by multiple types of callers. If it only makes sense next to one class, it belongs inside that class.
- **Default assumption:** New behavior that needs context → method on the object that owns that context; prove otherwise before adding a free function.

## Code Smells to Avoid

- **Many parameters** — A function with a lot of parameters is usually a sign that the design is too complex. Prefer smaller, focused functions or structured arguments (e.g. objects/dataclasses) where appropriate.
- **High cyclomatic complexity** — Too many branches in one function, or nested loops that stack up, usually means the implementation should be split (helpers, smaller functions, clearer data structures). Call this out in code review when you see it; refactor before it spreads.
- **Hard or overly complex unit tests** — If tests are difficult to write or become very complex, the code under test is likely poorly structured. Improve structure and boundaries so tests stay simple.
- **Unnecessary `else`** — If you can express the logic without an `else`, do so (e.g. early returns, guard clauses, or separate branches instead of deep if/else chains).
- **A flag on a collaborator that tells its caller what work to do** — for example `needs_expensive_signal = False`, read by the caller to decide whether to go fetch something. That is a reverse dependency: the collaborator is describing the caller's job rather than doing its own. The tell is that a second such flag produces combinations that are meaningless. Either the collaborator should obtain what it needs itself, or the requirement should be declared as data the caller resolves generically — not as a boolean the caller branches on.
- **A pass-through adapter** — a collaborator whose whole implementation is "return what you were given" usually means the boundary was drawn one step too late, and the interesting work sits on the wrong side of it.

## Unit tests

Treat test code with the same standards as production code: naming, structure, clarity, and scope discipline.

### Isolation and I/O

- Prefer **not** calling real external services from unit tests when you can avoid it. Use **mocking**, **stubs**, and tools like **VCR** (or equivalent) so tests stay fast, deterministic, and offline-friendly.

### Fixtures and data

- **Large or complex fixtures** (big YAML/JSON blobs, huge inline dicts) belong in a **separate file** (or dedicated factory/module), not pasted in the middle of a test module.
- **Do not fabricate fields nothing reads.** A shared builder that invents realistic-looking data the unit never consults adds constraints without adding coverage — and those constraints break unrelated cases later (an id coerced to `int` for a `_source` payload no one reads will reject a descriptive id a sibling test wants).

### Parameterization

- **Parameterized tests** and **`subTest`** (or the test runner's equivalent) are encouraged when **cases** differ (inputs and expected values): one clear act, explicit expectations per case. Use them for scenario matrices, not to fold unrelated tests together or hide assertion logic.

### Data setup with Django / Factory Boy

- Prefer **factories** over hand-built model graphs. Use **traits** (and related Factory Boy patterns) to express variations ("with orders", "vegan customer", etc.) instead of copy-pasting setup.

### What kind of test is this?

- **HTTP / API endpoints:** Treat these more like **integration tests**: exercise the real route, then assert on status, shape, and key fields of the response.
- **Classes and pure functions:** Treat these as **unit tests**: build minimal inputs (often via factories), call the unit, assert on return value or side effects you control.

### Shape of a good test

Aim for the same story every time: **starting state** (arrange) → **run the code under test** (act) → **verify outcomes** (assert). Readers should see what went in and what should come out without hunting.

### When a test changes subject

Moving a test to a newly extracted unit is not a copy operation.

- **Re-derive the assertion; do not translate it.** The context that justified the old assertion may not have moved with the test. Restate the property in the new subject's terms and work out what it should be, rather than transliterating the previous line into the new API.
- **Assert the property, not a stronger claim that happens to sit nearby.** "This candidate survives into the final set" and "this candidate ranks first" are different statements. The second is easy to reach for when the first no longer typechecks against the new unit, and it is often simply false.
- **Compute the expected value before asserting it.** If the assertion is arithmetic or ordering, work the numbers — by hand or in a scratch script — instead of reasoning about which way it should come out.
- **Name the range an ordering assertion depends on.** If the expected order only holds for certain tunable values, say so in the docstring, along with where it flips. Otherwise the next person to change a default gets a mystery failure.

### Class scope for stable values and shared mock data

- **Static literals for the class** (fixed IDs, constant payloads, frozen timestamps, default kwargs that every test in the class uses the same way) belong at **class scope**: class attributes, `setUpTestData`, or setup in `setUp` / `setUpClass`—not redefined at the top of every test method.
- **Builders and reusable mock data** (factories, `MagicMock` graphs, canned API responses) that multiple tests in the class need should live at **class scope** too: helper methods on the test class, shared setup, or small private methods like `_make_order_payload()` so each test body stays a short, linear story.
- **Per-test-only** values stay in the test method.

### Mixins

- **No `test_*` methods on mixin classes.** A test mixin should only provide **helpers**, **fixtures** (e.g. `setUp` / `setUpTestData` patterns), and **shared setup**—not runnable tests.
- **Tests live on concrete child classes.** That keeps discovery, naming, and "what this class proves" obvious at the leaf; mixins stay invisible infrastructure.

### Complexity and assertions

- **Very low cyclomatic complexity** in unit tests: avoid branching and nested logic in test bodies. If a test needs loops, conditionals, or layered helpers to "drive" assertions, split into more tests or simplify setup.
- **Repeating assertions across tests is fine.** Do not extract assertion blocks into shared helpers or indirection layers just to DRY tests—readers should see expectations spelled out next to the act. Reserve shared helpers for **building data**, not for **asserting outcomes**.
- **Parameterized tests / `subTest`** still make sense when the **cases** differ (inputs and expected outputs), not as a way to hide duplicated assertion structure behind generic machinery.
- **Prefer asserting behaviour over asserting a declaration.** "Patch the client, run the unit, assert it was never called" survives a refactor that deletes the flag; `assertFalse(thing.needs_client)` does not, and proves less.

## Working together

### Division of labor on verification

Cris runs the pre-commit tooling himself: formatter, linter, type checker, and the test suite. Do not duplicate that work, and do not end a response with a list of those commands for him to run.

Do the verification tooling cannot do:

- **Semantic equivalence on bulk rewrites.** After a scripted rename or signature change, prove the change is what it claims to be — canonicalize both versions and diff them, so "rename only" is a demonstrated fact rather than an assertion.
- **Reference sweeps before deleting.** "This is dead" is a claim that needs evidence. Check the whole repo, including string references, config blobs, and callers outside the app.
- **Cross-file invariants.** Registry keys against the values that select them, cache-key shapes, abstract base signatures against every implementation, values duplicated between code and config.
- **Call-site audits before scripting a change.** Learn the real shapes first. Single-line regexes undercount multi-line calls; counts derived that way will be low.
- **Behaviour audit when extracting or moving code.** A structural comparison shows the main job survived. List what the original *also* did — caching, ordering guarantees, early returns, logging, timing instrumentation — and confirm each one landed. A dropped one-time cache leaves no trace in a diff of shapes.

### Know what your check can prove

Static sweeps — grep, AST walks, import graphs — answer *do these symbols resolve and line up with each other*. They say nothing about whether a value survives a call.

Name-and-shape analysis and value-and-behaviour analysis catch disjoint sets of defects. A clean structural pass is not evidence the code runs. Typical escapes: a validator that rejects an input shape it should accept, a renamed attribute nothing statically resolves, arithmetic asserted rather than computed.

So: **name the kind of verification performed**, and do not let a structural result stand in for a behavioural one.

**Simulate pure logic rather than reasoning about it.** When the changed logic is arithmetic, ordering, or set manipulation, lift it into a throwaway script with no framework dependencies and run it. That option exists even when the real suite cannot be run locally. "I could not run the tests" is rarely a reason not to compute the answer.

### Verify where changes might be, not where you expected them

A check that only inspects the files you meant to touch cannot find the ones you missed. Walk the whole tree. Descend into nested scopes — classes and functions defined inside other functions are real code and will break at runtime.

**Build the search set from what could break, not from what you touched.** A method whose body is unchanged but whose parameter type moved is still a breaking change for every caller. Enumerating candidates from the diff misses exactly those.

When a verification script reports success, sanity-check the script itself. Self-contradictory output (a "mismatch" whose two sides print identically) means the checker is wrong, not the code.

**Sanity-check it on failures too.** Before acting on a finding — or waving one away as a false positive — prove which side is wrong. A name-to-type map built per file rather than per scope will collide on common local names like `response` or `self.client` and invent problems; the fix is to make the checker precise and re-run it, not to eyeball its output and decide.

### Diagnosing a change in a measured number

A metric moving between two runs is not evidence about the change under test until the runs are shown comparable. Check the conditions before trusting the delta: same environment, same input set, same warm state. A local-environment baseline and a since-changed environment's rerun are not comparable no matter how close the numbers land — find whatever field names the environment (or infer it from context) before drawing a conclusion from the gap between them.

Correlate a suspicious metric against run order before blaming the change under test. A value that starts high and decays toward a flat tail over the course of a run is describing warm-up — connections, caches, JIT — not the logic being measured, and that shape will be absent from a baseline run's own ordering. Bucket the sequence and compare; a strongly one-sided correlation in the new run and near-zero in the old one confirms it.

Failing completely and losing on ranking are different diagnoses, and call for different fixes. When an expected match is entirely absent from the result — not merely outranked — something upstream failed to fire or never retrieved it; no downstream weight or boost can manufacture a match that never happened. Confirm the mechanism actually engaged for the failing case (find at least one instance where it fired) before adjusting its magnitude. An identical before/after result — same failure, same example — on a change that only touched a magnitude is confirmation the mechanism never fired, not a sign the change was too small.

### Scope discipline

Make the smallest reasonable change. No opportunistic cleanups, however tempting — mention them and move on. Code that looks redundant is often load-bearing: guards may exist for failure modes not visible from the current call path, and a test may be deliberately pinning that behavior. Removing one can turn a graceful degradation into an outage.

### Design tradeoffs

When there is a clean-design option and a low-churn option, lead with the clean one and state the churn plainly. Cris will generally pay a large mechanical test diff to close a seam properly. Do not pre-emptively soften a proposal to reduce the diff.

Distinguish *the same value reaching two places* from *two sources of truth*. The first is usually fine. Only the second is a defect worth restructuring for.

Prefer deriving state over passing it again: if an object can read what it needs from a collaborator it already holds, divergence becomes unrepresentable instead of merely discouraged.

When a design is meant to accommodate something not built yet, state the acceptance test for it: "can the planned thing be added without editing this file?" That converts a claim about extensibility into something checkable now.

### Reporting work

Own mistakes directly and say what the consequence was. Report the checks that were run and, just as importantly, what could not be verified and why — an honest gap is more useful than an implied guarantee. Skip recaps of steps already visible; lead with the outcome and the decisions that need attention.

Be precise about the strength of a claim. "The key sets match" and "the behaviour is equivalent" are different statements; reporting the first while implying the second is how a gap becomes a surprise later.

## Commit messages

Cut through the noise. A reviewing engineer should understand what was done in seconds. Be direct: the change, then its impact.

```
<TICKET>: <the change>

<the impact>
```

Examples:

```
ISA-3078: Flag only the test's origin in the production report read-flag test

Fixes a flaky test.
```

```
ISA-3078: Fix return types of the swap and availability-facts stubs

Prevents crashes in swap and CYO callers when the read flag flips.
```

- **Subject:** ticket key, colon, the change as a plain imperative phrase. No trailing period.
- **Body:** the impact, in one short sentence. Say what is now true or what is prevented, not how.
- **Fewest words that carry the meaning.** No filler ("this change", "in order to", "now properly"), no restating the subject, no hedging.
- **No bullet lists, file inventories, or test summaries.** The diff shows the details.
- **Describe the result, not the session.** No "Step 2", "fixes from review", or "as discussed".

