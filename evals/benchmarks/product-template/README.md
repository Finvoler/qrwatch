# Product Benchmark Template

This directory is a template for phase-three product-specific evals. It is intentionally not a runnable benchmark because universal scaffold tasks should not pretend to know a target product.

To create a product benchmark:

1. Copy this directory to `evals/benchmarks/<benchmark-id>/`.
2. Rename `benchmark.template.json` to `benchmark.json`.
3. Rename `task.template.json` to `task.json`.
4. Replace every `PROJECT_PLACEHOLDER(...)` value with facts from the target project.
5. Run the suite locally:

```bash
python tools/run_evals.py --suite product-smoke --no-baseline
```

6. After a known-good pass, create the baseline:

```bash
python tools/run_evals.py --suite product-smoke --update-baseline
```

## Suggested Suites

- `product-smoke`: one tiny safe task that proves the harness can modify and validate the real project.
- `product-regression`: known historical bugs or workflows that should not break again.
- `product-quality`: reviewer-scored or rubric-scored checks that need human interpretation.
- `product-cost-latency`: execute-mode benchmarks with explicit cost and runtime budgets.

Product benchmarks should name their sandbox, approval, cost, and rollback expectations before being used in CI.
