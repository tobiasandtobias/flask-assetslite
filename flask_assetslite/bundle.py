import json
import pipes
import hashlib
from os import stat
from glob import glob
from utils import listify
from flask import current_app
from os.path import getmtime, join, realpath, isfile
from cStringIO import StringIO
from tempfile import NamedTemporaryFile


class Bundle(object):
    """
    A Bundle takes a bunch of files (or other bundles) and combines them
    together. A bundle can also optionally run filters on the combined
    data.

    If an output filename is specified through the `output` parameter,
    the bundle will write its contents to the file each build.
    """
    def __init__(self, contents, output=None, filters=[], static_folder='',
                 static_url_path='', debug=None, build=True, cache_file=''):

        self.filters = filters if type(filters) is list else [filters]

        self.build = build

        self._output = output
        self._contents = contents
        self._cache_file = cache_file

        self._debug = debug
        self._static_folder = static_folder
        self._static_url_path = static_url_path

    def _resolve_sources(self, sources):
        """
        Add a file, glob pattern or another bundle to this bundle's
        contents.
        """
        sources = listify(sources)

        contents = []

        for source in sources:
            # Glob pattern, so expand into files
            if isinstance(source, str) and '*' in source:
                contents.extend(self._resolve_sources(glob(join(self.static_folder, source))))
            # Nested bundles are cool
            elif type(source) is Bundle:
                contents.append(source)
            # Files are fine; check the static_folder
            elif isfile(realpath(join(self.static_folder, source))):
                contents.append(realpath(join(self.static_folder, source)))
            # Check for direct path
            elif isfile(realpath(source)):
                contents.append(realpath(source))
            else:
                raise Exception('Cannot find file \'%s\'' % source)

        return contents

    @property
    def _unchanged(self):
        """
        Returns True if we can verify (via cache) if this bundle can avoid
        regeneration. It does this by checking the last modified timestamps of
        the resolved source files.
        """
        print '[cache] file %s ' % self.cache_file
        if not isfile(self.cache_file):
            print '[cache] file not found'
            return False

        try:
            # Attempt to parse JSON file
            file = open(self.cache_file)
            data = json.load(file)
            files = data.keys()
        except Exception, e:
            print '[cache] ERROR: Unable to load and parse JSON file %s' % e
            return False

        # Check each file with the mtime from the cache
        for file in self.sources:
            file = join(self.static_folder, file)
            if file not in files:
                return False
            try:
                if stat(file).st_mtime > data[file]['mtime']:
                    return False
            except Exception, e:
                print '[cache] ERROR: error checking mtime: %s' % e
                return False

        return True

    def _urlize_paths(self, paths):
        """
        Return a list of URLs for the given paths.
        """
        paths = listify(paths)
        static_folder = realpath(self.static_folder)

        url_paths = []
        for path in paths:
            # Ensure this is a full, real path (ie. not relative)
            path = realpath(path)
            # Strip off path to the static folder from the beginning
            if path.startswith(static_folder):
                path = path[len(static_folder):]
            # Prefix with the static folder URL path
            path = self.static_url_path + path
            url_paths.append(path)

        return url_paths

    @property
    def contents(self):
        """
        Return a list of all resolved paths for this bundle's contents.
        """
        return self._resolve_sources(self._contents)

    @property
    def combined(self):
        """
        Returns the last successfully compiled combined output file.
        """
        if not self._output:
            return None

        if not '%s' in self._output:
            return self.output_filename

        # Search for latest file
        combined_files = glob(self.output_filename_glob_pattern)
        if not combined_files:
            return None

        return sorted(combined_files, key=lambda x: getmtime(x), reverse=True)[0]

    @property
    def data(self):
        """
        Return the StringIO handle containing data for this bundle.
        This will trigger a build if the bundle hasn't yet been built.
        """
        if hasattr(self, '_data'):
            return self._data
        else:
            return self.read()

    @property
    def debug(self):
        if current_app and self._debug is None:
            return current_app.debug
        else:
            return self._debug

    @property
    def output_filename(self):
        """
        Return the output filename with the hash. Will trigger a read().
        """
        if not self._output:
            return None
        elif not '%s' in self._output:
            return join(self.static_folder, self._output)
        else:
            # Read in all data so it can be hashed
            return join(self.static_folder, self._output % self.hash(self.data.getvalue()))

    @property
    def output_filename_glob_pattern(self):
        """
        Return the output filename with a glob pattern.
        """
        if '%s' in self._output:
            return join(self.static_folder, self._output % '????????')
        else:
            return join(self.static_folder, self._output)

    @property
    def sources(self):
        """
        Return list of files from all sources in this bundle. If other
        bundles are nested within this bundle's sources, their source
        files will be in this list too.
        """
        files = []
        for source in self.contents:
            if type(source) is Bundle:
                files.extend(source.sources)
            else:
                files.append(source)
        return files

    @property
    def static_folder(self):
        if current_app and not self._static_folder:
            return current_app.static_folder
        else:
            return self._static_folder

    @property
    def static_url_path(self):
        if current_app and not self._static_url_path:
            return current_app.static_url_path
        else:
            return self._static_url_path

    @property
    def cache_file(self):
        if self._cache_file:
            return join(self.static_folder, self._cache_file)
        else:
            return ''

    @classmethod
    def hash(self, data):
        """
        Return a hash of the specified data.
        """
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()[:8]

    def build_bundle(self):
        """
        Trigger a build for this bundle. A build reads all source data,
        combines it, runs any filters over it, outputs it to a file (if
        one has been specified) and then returns a file-like handle.
        """
        if not self.build:
            return None

        if self._unchanged:
            print 'Skipping build, source files unchanged...'
            return None

        print 'Building bundle, woot!'

        # Read in all source data
        print 'Reading data from source files...'
        self.read()

        # Run filters
        print 'Running filters...'
        self.run_filters()

        # Write output file
        print 'Writing output file, if there is one...'
        self.write()

        # Cache last modified of source files
        if self.cache_file:
            print '[cache] saving timestamps'
            data = {}
            for file in self.sources:
                file = join(self.static_folder, file)
                data[file] = {'mtime': stat(file).st_mtime}
            with open(self.cache_file, 'w+') as cache_file:
                json.dump(data, cache_file)

        # Return data handle
        self.data.seek(0)
        return self.data

    def read(self):
        """
        Read in and combine data from all sources (files and other
        bundles).
        """
        data = StringIO()

        # Read and combine all source data
        for source in self.contents:
            if type(source) is Bundle:
                # Bundle; get contents
                handle = source.build_bundle()
                if handle:
                    data.write(handle.read())
            else:
                # File; open and read it
                f = open(source, 'r')
                data.write(f.read())
                f.close()

        # Save and return
        self._data = data
        return data

    def run_filters(self):
        """
        Run this bundle's filters over the specified data. `data` is a
        file-like object. A file-like object is returned.
        """
        if self.filters:
            # Create temporary file for output
            tmpfile = NamedTemporaryFile()

            # Construct a pipe of chained filters
            pipe = pipes.Template()
            for filter in self.filters:
                for step in filter:
                    pipe.append(*step)

            # Write data through the pipe
            print '[filters] Writing data through pipe into tmpfile...'
            w = pipe.open(tmpfile.name, 'w')
            self.data.seek(0)
            w.write(self.data.read())
            w.close()

            # Read tmpfile back in
            print '[filters] Reading tmpfile...'
            tmpfile.seek(0)
            self.data.truncate(0)
            self.data.write(tmpfile.read())
            tmpfile.close()

        return self.data

    def urls(self, debug=None):
        """
        Return a list of static file URLs. Depending on whether debug is
        True or not, this will either return a list of URLs to all the
        source files in this bundle's contents, or a list of a single
        URL which is the combined version.
        """
        debug = debug if debug is not None else self.debug
        if debug:
            # Print source paths
            return self._urlize_paths(self.sources)
        else:
            # Print combined path
            if self.combined:
                return self._urlize_paths(self.combined)
            else:
                # Fall back to the debug/source paths if we can't find
                # a combined file (ie. build has never run).
                return self.urls(debug=True)

    def write(self):
        """
        Write out the bundle's data to its output file, if one has been
        set.
        """
        if self._output:
            handle = open(self.output_filename, 'w')
            self.data.seek(0)
            handle.write(self.data.read())
            handle.close()
