"""Web server entrypoint for CC2 Editor"""

import argparse
from typing import Optional, List
from . import server

parser = argparse.ArgumentParser(description=__doc__)


def run(args: Optional[List[str]] = None) -> None:
    parser.parse_args(args)
    server.app.run("127.0.0.1", port=4422, debug=True)

