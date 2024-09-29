# AIOS documentation

## Build the docs

```bash
# Install dependencies.
pip install -r requirements-docs.txt

# Build the docs.
make clean
make html
```

## Open the docs with your browser

```bash
python -m http.server -d build/html/
```
Launch your browser and open localhost:8000.

## Guides of how to write the docs
We use the readthedocs to build documentation, the guideline is [here](https://docs.readthedocs.io/en/stable/). The theme we used is [spinx-book](https://sphinx-book-theme.readthedocs.io/en/stable/). 

