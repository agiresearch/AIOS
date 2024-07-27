import os
import sys
from sphinx.ext import autodoc
sys.path.insert(0, os.path.abspath('../../'))
# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'AIOS'
copyright = '2024, AGI Research'
author = 'AGI Research'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    'sphinx.ext.linkcode'
]

def linkcode_resolve(domain, info):
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    return f"https://github.com/agiresearch/AIOS/blob/main/{filename}.py"


intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': False,
    'inherited-members': False,
    'member-order': 'bysource',
    'show-inheritance-diagram': False,
    # 'source': True,
}

templates_path = ['_templates']

html_theme_options = {
    "repository_url": "https://github.com/agiresearch/AIOS",
    "use_repository_button": True,
    'use_edit_page_button': True
}

html_title = "AIOS"
# -- Options for HTML output

html_theme = 'sphinx_book_theme'

exclude_patterns = ["**/*.template.rst"]

def setup(app):
    from docs.source.generate_tools import generate_tools
    generate_tools()

# -- Options for EPUB output
# epub_show_urls = 'footnote'
# Mock out external dependencies here, otherwise the autodoc pages may be blank.
autodoc_mock_imports = [
    "torch",
    "transformers",
    "psutil",
    "PIL",
    "numpy",
    "tqdm",
]

class MockedClassDocumenter(autodoc.ClassDocumenter):
    """Remove note about base class when a class is derived from object."""

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        if line == "   Bases: :py:class:`object`":
            return
        super().add_line(line, source, *lineno)


autodoc.ClassDocumenter = MockedClassDocumenter

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "typing_extensions":
    ("https://typing-extensions.readthedocs.io/en/latest", None),
    "pillow": ("https://pillow.readthedocs.io/en/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "torch": ("https://pytorch.org/docs/stable", None),
    "psutil": ("https://psutil.readthedocs.io/en/stable", None),
}

autodoc_preserve_defaults = True

navigation_with_keys = False
