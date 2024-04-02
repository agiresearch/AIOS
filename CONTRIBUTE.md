# How to contribute to AIOS
Thank you for your interest in our project! 
Here's a guide to get you started.

## 1. Get Started
### Fork the repository

At first, you need to fork this copy and create your own version of repo. 

### Clone the repository and install the dependencies.

### Installing dependencies with pip
```bash
pip install -r requirements.txt
```

### Installing pre-commit
We strongly recommend installing pre-commit to ensure proper formatting during development

## 2. Developing and Testing
### Create a branch

Create a new branch for your awesome changes. 

```shell
git checkout -b your-feature
```

### Make changes and testing

You can develop new features and then you need to make sure everything works as expected. Run our provided tests and make sure the existing ones go well and customize new tests are highly encouraged!

### Run tests

Running tests via pytest, you are encourged to add your test code into the `tests/` directory and test.
```
pytest -s tests
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

1. Visit [AIOS](https://github.com/agiresearch/AIOS) and click "New Pull Request" button.
2. Choose the base branch (`main`) and the compare branch (your feature branch).
3. Write a title and describe your changes in the description. 

## 4. Review and Approval
Our maintainers, will take a look and might suggest some cool upgrades or ask for more details. After they approve, your commitment can be incorporated into AIOS!