FIXED3 changes:
- removes .venv/node_modules/dist/__pycache__ again AFTER tests/build
- allows deletion of legacy tracked generated files
- blocks only unsafe files that would be added/modified
- keeps rollback branch and test/build gates
