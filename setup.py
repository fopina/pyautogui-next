from io import StringIO

from setuptools import Distribution as SetuptoolsDistribution
from setuptools import setup

OBSOLETES_DIST_HEADER = 'Obsoletes-Dist: pyautogui'


class Distribution(SetuptoolsDistribution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        write_pkg_file = self.metadata.write_pkg_file

        def write_pkg_file_with_obsoletes_dist(file):
            # Setuptools does not expose Obsoletes-Dist in PEP 621 metadata.
            metadata_buffer = StringIO()
            write_pkg_file(metadata_buffer)
            metadata = metadata_buffer.getvalue()

            header, separator, body = metadata.partition('\n\n')
            if OBSOLETES_DIST_HEADER not in header.splitlines():
                header = f'{header}\n{OBSOLETES_DIST_HEADER}'

            file.write(f'{header}{separator}{body}')

        self.metadata.write_pkg_file = write_pkg_file_with_obsoletes_dist


setup(distclass=Distribution)
