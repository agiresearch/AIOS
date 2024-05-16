# How to contribute to AIOS
Thank you for your interest in AIOS!
Here's a guide to help you contribute to this project.

## 1. Get Started
### Fork the repository

At first, you need to fork this copy and create your own version of repo.

### Clone the repository and install the dependencies.

### Installing dependencies with pip
```bash
pip install -r requirements.txt
```

### Installing pre-commit
We strongly recommend installing [pre-commit](https://pre-commit.com/) to ensure proper formatting during development

## 2. Developing and Testing
### Create a branch

Create a new branch for developing your creative features

```shell
git checkout -b your-feature
```

### Make changes and testing

You can develop new features and then you need to make sure everything works as expected. Run our provided tests and make sure the existing ones go well. Your new tests are encouraged.

### Run tests

Add your test code into the `tests/` directory if any, then run test via [pytest](https://docs.pytest.org/en/8.0.x/)
```
pytest -v tests/
```
sample output
```
============================================================================================================================= test session starts ==============================================================================================================================
platform darwin -- Python 3.11.9, pytest-8.1.1, pluggy-1.5.0 -- ""
cachedir: .pytest_cache
rootdir: ""
plugins: anyio-4.3.0
collected 9 items                                                                                                                                                                                                                                                              

tests/test_infinite_memory.py::test_infinite_memory PASSED                                                                                                [ 11%]
tests/test_jit_streaming.py::test_jit_streaming PASSED                                                                                                    [ 22%]
tests/test_llms.py::test_closed_llm PASSED                                                                                                                [ 33%]
tests/test_llms.py::test_open_llm PASSED                                                                                                                  [ 44%]
tests/test_lru_k_replacer.py::test_update_access_history PASSED                                                                                           [ 55%]
tests/test_lru_k_replacer.py::test_evict PASSED                                                                                                           [ 66%]
tests/test_lru_k_replacer.py::test_set_evictable PASSED                                                                                                   [ 77%]
tests/test_lru_k_replacer.py::test_invalid_block_id PASSED                                                                                                [ 88%]
tests/test_memory.py::test_mem_alloc PASSED                                                                                                               [100%]
```

## 3. Submitting Changes

### Code format check
Please ensure your code is formatted correctly using pre-commit

### Git commit format
We strongly recommend your git commit follows the format below
```bash
git commit -m <type>: <subject>
```

| <type> | <subject>                                     |
|-------------|--------------------------------------------------|
| `feat`      | Add new features                                 |
| `fix`       | Fix bugs                                         |
| `docs`      | Modify documents like README, CONTRIBUTE         |
| `style`     | Modify code format like space and comma without changing code logic |
| `refactor`  | Refactor code structure without adding new features or fixing new bugs |
| `perf`      | Improve performance or user experience                              |
| `test`      | Test features, including unit test and integration test |
| `chore`     | Change the build procedure or add dependencies   |
| `revert`    | Revert to the previous version                   |

### Create a Pull Request

1. Visit your forked AIOS repository on GitHub and click the "Compare & pull request" button to initiate the process of submitting your changes to the original repository for review and potential merging.
2. Choose the base branch and the compare branch (your feature branch).💡 Note that when you add new features, it is recommended to choose the (`dev`) branch and if your change does not affect original functions, you may consider choosing the (`main`) branch.
3. Write a title and describe your changes in the description. And it is recommended to select the label of the change to make it more clear.

## 4. Review and Approval
Our maintainers will have a review of that and might give some suggestions or ask for more details. After they approve, your commitment can be incorporated into AIOS!
