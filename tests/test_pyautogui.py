from test_common import install_headless_stubs

install_headless_stubs()

from test_gui import *  # noqa: F401,F403
from test_unit import *  # noqa: F401,F403
