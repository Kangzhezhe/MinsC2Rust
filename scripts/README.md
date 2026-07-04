# Scripts

Repository-level entrypoints for the public smoke workflow.

- `smoke_test.sh`: run the reference-aligned `arraylist` smoke test.
- `run.sh`: convenience wrapper around `smoke_test.sh`.

Both scripts derive the repository root from their own location, so they can be
executed from any current working directory.

For larger public benchmarks, run the tool directly with one of:

```bash
cd Tool
./run.sh ../configs/config_c_algorithm.ini
./run.sh ../configs/config_crown.ini
```
