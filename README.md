### tts_netflow_b

Usage:

```
    python -m tts_netflow_b -i input.xlsx -o solution.xlsx
```

Multi-commodity network flow Tidy, Tested, Safe demonstration repository.

We demonstrate the Agile development process with three releases that advance functionality or fix bugs.
  1. [0.0.1](https://github.com/ticdat/tts_netflow_b/releases/tag/0.0.1) is a no-math release with a dummy `solve` 
  function. The purpose of this release is to demonstrate the input schema (to include data validation rules) to 
  the user. This release is capable of validating input data and nothing more.
  1. [0.0.2](https://github.com/ticdat/tts_netflow_b/releases/tag/0.0.2) In response to user request, we changed the 
  input schema to have distinct supply and demand tables, with an integrity rule that the tables don't overlap.
  We retain the original input schema as an alternate modeling schema. 
  1. [0.0.3](https://github.com/ticdat/tts_netflow_b/releases/tag/0.0.3) Now that the input schemas
  have been sorted out, we actually implement the optimization math. The public interface of `tts_netflow_b`
  supports solving from either schema.
