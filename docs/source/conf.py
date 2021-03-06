# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

project = "Faculty library"
copyright = "2020 Faculty Science Limited"
author = "Faculty"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]

autodoc_default_options = {"members": True, "undoc-members": True}
autodoc_member_order = "bysource"
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# Use the 'Read the docs' theme
html_theme = "sphinx_rtd_theme"
extensions.append("sphinx_rtd_theme")

# Customise the theme
html_logo = "static/faculty.png"
html_theme_options = {
    "style_nav_header_background": "#1c1c1c",
    "logo_only": True,
}
html_css_files = ["style.css"]

# Disable Sphinx attribution
html_show_sphinx = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["static"]
