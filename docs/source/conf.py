import os
import sys
sys.path.insert(0, os.path.abspath('../../'))
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
    'show-inheritance': True,
    'inherited-members': True,
    'member-order': 'bysource',
    'show-inheritance-diagram': True,
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

# -- Options for EPUB output
# epub_show_urls = 'footnote'
