# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cothrom'
copyright = '2026, The Problem Solving Association CLG.'
author = 'The Problem Solving Association CLG.'
release = 'v0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx_rtd_theme', 'sphinx-prompt']

templates_path = ['_templates']
exclude_patterns = ["snippets"]

from sphinx.util.docfields import Field, GroupedField, TypedField

def setup(app):
    app.add_object_type(
        directivename="datafile",
        rolename="datafile",
        indextemplate="pair: %s; datafile",
        doc_field_types=[
            Field(name="directory",
                  names=("directory",),
                  label="Directory"),
            Field(name="source",
                  names=("source",),
                  label="Source"),
            GroupedField(name="usedby",
                         names=("usedby",),
                         label="Used by",
                         rolename="script")
        ]
    )

    # TODO add types to arguments?
    app.add_object_type(
        directivename="script",
        rolename="script",
        indextemplate="pair: %s; script",
        doc_field_types=[
            Field(name="usage",
                  names=("usage",),
                  label="Usage"),
            GroupedField(name="arg",
                         names=("arg",),
                         label="Arguments"),
            GroupedField(name="env",
                         names=("env",),
                         label="Environment variables",
                         rolename="envvar"),
            TypedField(name="conf",
                       names=("conf",),
                       typenames=("type",),
                       label="Configuration values",
                       rolename="confval"),
            GroupedField(name="input",
                         names=("input",),
                         label="Input data",
                         rolename="datafile"),
            GroupedField(name="output",
                         names=("output",),
                         label="Output data",
                         rolename="datafile")
        ]
    )

    app.add_object_type(
            directivename="maketarget",
            rolename="maketarget",
            indextemplate="pair: %s; maketarget",
            doc_field_types=[
                Field(name="usage",
                      names=("usage",),
                      label="Usage"),
                GroupedField(name="dependency",
                             names=("dependency",),
                             label="Dependencies",
                             rolename="maketarget")
            ]
        )



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {"version_selector": True}
html_static_path = ['_static']
