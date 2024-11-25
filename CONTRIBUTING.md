# Contributing to OpenF1

OpenF1's mission is to democratize Formula 1 data by making it open and accessible to everyone.<br />
We welcome all contributions that help advance this goal!

## Current contribution opportunities

Looking for ways to help? Check out our list of open items [here](https://github.com/br-g/openf1/discussions/127)
to see where your contributions are needed.

## How to contribute code

Follow these steps to submit your code contributions effectively.

### 1. Open an issue

Before making changes, we recommend opening an issue (if one doesn’t already exist) to
discuss your proposed updates. This allows us to provide feedback and validate the changes early.<br />
For minor fixes (e.g., small bug fixes or documentation updates), feel free to skip this
step and directly create a pull request (PR).

### 2. Make your changes

1. Fork the repository: Start by forking the OpenF1 repository.
2. Set up your environment: Set up a development environment and ensure that you can run the unit tests locally.
3. Implement your changes: Make the necessary changes in your forked repository.

### 3. Create a pull request (PR)

When your changes are ready, create a PR from your fork’s branch to the `dev` branch of
the official OpenF1 repository.<br />
Make sure to include a clear description of the changes and reference the issue (if applicable).

### 4. Code review

A reviewer will evaluate your PR and provide feedback.<br />
There may be several rounds of comments and code changes before the pull request gets
approved by the reviewer.

### 5. Merging

Once your PR is approved, a team member will handle the merging process.<br />
Your changes will first be merged into the `dev` branch and later into the `main` branch
after further testing.

## 🛠️ Code style guidelines

OpenF1 uses Black for formatting and Ruff for linting.<br />
Please refer to [testing_requirements.txt](https://github.com/br-g/openf1/blob/main/testing_requirements.txt)
for the required versions.

Please ensure your code adheres to these standards before submitting a PR.<br />
Run the following commands in the repository’s root directory to check for issues:

```
ruff --format=github --ignore=E501 --target-version=py310 .
black --check --diff --color .
```
