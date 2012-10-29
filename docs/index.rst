flask-assets-lite
=================

flask-assets-lite is a lightweight replacement for
`Flask-Assets <http://elsdoerfer.name/docs/flask-assets/>`_/
`webassets <https://github.com/miracle2k/webassets>`_.

Example Usage
-------------

Registering bundles is familiar:

.. code-block:: python

    from flask import Flask
    from flask.ext.assets import Assets, Bundle

    app = Flask(__name__)

    # Create environment and register to Flask app
    environment = Assets(app)

    # Register bundle
    environment.register('css', Bundle('css/*.css', output='assets/css/default.%s.css'))

And in your template:

.. code-block:: jinja

    {% for url in assets['css'].urls() %}
    <link rel="stylesheet" href="{{ url }}" media="all" />
    {%- endfor %}

Building
--------

Building the bundles doesn't happen automatically. You must do this as part of
your build process. For example, with
`Flask-Script <http://flask-script.readthedocs.org/en/latest/>`_ and `manage.py`
you might do:

.. code-block:: python

    from myapp import app
    from flask.ext.script import Manager

    manager = Manager(app)

    @manager.command
    def build():
        app.extensions['assets'].build_all()

    if __name__ == "__main__":
        manager.run()

Filters
-------

Filters are simple to create, and can be applied to bundles::

    from flask.ext.assets import Filter, Step

    # Create a cssmin filter
    cssmin = Filter(Step('/bin/cssmin', '--'))

    environment.register('css', Bundle('css/*.css',
                                       filters=cssmin,
                                       output='assets/css/default.%s.min.css'))

Filters use `pipes <http://hg.python.org/cpython/file/2.7/Lib/pipes.py>`_ to
filter data through external commands. This makes it quick and easy to implement
custom filters.

Versioning
----------

Bundles include builtin versioning for the output filename. Simply add `%s` to
the `output` argument when creating a bundle:

.. code-block:: python

     Bundle('css/*.css', output='assets/css/default.%s.css'))

The resulting output filename will then include the MD5 hash of the bundle's
contents (trimmed to the first 8 characters). This means you can build a bundle
multiple times and filename will remain the same if the content is unchanged:

>>> bundle = Bundle('css/*.css', output='assets/css/default.%s.css') 
>>> bundle.output_filename
'/path/to/app/static/assets/css/default.6e80caa9.css'
