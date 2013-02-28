class Assets(dict):
    """
    Collection of asset bundles.
    """
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def build_all(self):
        """
        Build all registered bundles.
        """
        for name, bundle in self.iteritems():
            bundle.build_bundle()

    def init_app(self, app):
        """
        Initialise Flask app with this Assets environment.
        """
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['assets'] = self

        @app.context_processor
        def assets():
            return dict(assets=self)

    def register(self, name, bundle):
        """
        Register a bundle with the specified name.
        """
        self[name] = bundle
