#!/usr/bin/env python3
# Copyright Materialize, Inc. All rights reserved.
#
# Use of this software is governed by the Business Source License
# included in the LICENSE file at the root of this repository.
#
# As of the Change Date specified in that file, in accordance with
# the Business Source License, use of this software will be governed
# by the Apache License, Version 2.0.

"""async_tail

Module showing an example for how to asynchronously TAIL a Materialized view.
"""

import argparse
import asyncio

import websockets

async def stream_view(args):
    """Continuously print batches to a Materialize View, as presented by the web server."""
    uri = f"ws://{args.host}:{args.port}/api/v1/stream/{args.view}"
    async with websockets.connect(uri) as websocket:
        while 1:
            batch = await websocket.recv()
            print(batch)

def main():
    """Parse arguments and run tail query."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host", help="Web server hostname", default="localhost", type=str
    )
    parser.add_argument(
        "-p", "--port", help="Web server port number", default=6875, type=int
    )

    parser.add_argument("view", help="Name of the view to TAIL", type=str)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(stream_view(args))
    loop.close()


if __name__ == "__main__":
    main()
