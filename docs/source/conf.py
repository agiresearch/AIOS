# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'AIOS'
copyright = '2024, AGIResearch Team'
author = 'the AGIResearch Team'

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
    "sphinx.ext.viewcode"
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

html_theme_options = {
    "repository_url": "https://github.com/agiresearch/AIOS",
    "use_repository_button": True,
    'use_edit_page_button': True
}

html_title = "AIOS"
# -- Options for HTML output

html_theme = 'sphinx_book_theme'

# -- Options for EPUB output
# epub_show_urls = 'footnote'
