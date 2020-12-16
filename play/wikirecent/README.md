# Real Time View of Top10 Wikipedia Editors using Python and Javascript

This directory contains a demonstration application showing how to build an event-driven data
pipeline. The example application comes from our [Getting Started Guide][], where Materialize is
configured with three `MATERIALIZED VIEWS` that update as new edits are appended to the
`wikirecent` source. The three views are:

- `counter`: The count all edits that have ever been observed.
- `useredits`: The count of all edits observed, grouped by user.
- `top10`: The top-10 users, where top means most edits by count. This view is a `MATERIALIZED
  VIEW` on top of `useredits`.

[Getting Started Guide]: https://materialize.com/docs/get-started/

The Python web application then serves a basic page that renders both the current value for
`counter` and a visualization of the `top10` table. These counts and visualization are updated
as the underlying `MATERIALIZED VIEWS` are updated, using the [TAIL][] command.

[TAIL]: https://materialize.com/docs/sql/tail/

## Running it Yourself

To run this demo using Docker Compose, run `mzconduct up`:

    ./bin/mzconduct up wikirecent -w demo

To view the web app in your local browser, run the `mzconduct web`:

    ./bin/mzconduct web wikirecent app

Once you're done, run `mzconduct down` to stop services and delete the associated volumes:

    ./bin/mzconduct down wikirecent -v

## How This Works

This application is written as an event-driven application. This means that no components are
configured to repeatedly query or poll other applications. Instead, each application is
subscribing to updates from their dependencies. Updates are minimal in size and are expressed
soley as transformations from previous state. This has two major benefits:

- Real-time push notifications. Applications are notified as soon as data changes and are not
  required to repeatedly poll for the same information over and over again.

- Economy of resources required. Each result set only contains information about datum that have
  changed. Fewer bytes are sent over the network and processing updates is more efficient.

### Services and Service Dependency

There are 4 major components that comprise this stack:

- `stream`: A service to curl [Wikimedia's Recent Change Stream][] and write append the
  results to a file called `recentchanges`.
- `materialized`: An instance of `materialized` configured to `TAIL` the `recentchanges` file and
  maintain the `counter`, `useredits` and `top10` `MATERIALIZED VIEWS`.
- `app`: A Python web server, written as an asynchronous application using [tornado-web][] and
  [psycopg3][], to `TAIL` the `counter` and `top10` views and present updates to these views over
  websockets.
- The user's web browser. The webpage rendered by `app` includes Javascript code that opens two
  websockets to `app`. Each message, pushed by `app`, contains an update that is then rendered by
  the user's web browser.

[Wikimedia's Recent Change Stream]: https://stream.wikimedia.org/v2/stream/recentchange
[tornado-web]: https://www.tornadoweb.org/en/stable/
[psycopg3]: https://www.psycopg.org/psycopg3/

Thus, the flow of data looks like this:

    Wikimedia --> stream --> recentchanges --> materialized --> app --> browser

Contrast this with a "typical web app" backed by a SQL database, where each application is making
repeated requests to upstream systems:

    Wikimedia <-- stream --> database <-- app <-- browser

## Debugging / Utilities

There are multiple ways to debug the data between transferred between the various components in
this stack.

### Open a psql client to Materialize

The Materialize database is not exposed on a well-numbered port and instead docker-compose chooses
a random high-numbered port. To open a Postgres REPL, connected to the Materialized instance
running as part of this demo, run:

    psql -h localhost -p $(./bin/mzconduct list-port wikirecent materialized) materialize

### Streaming top10 from Materialize to your console

To view the data sent from Materialize server to the browser, use the `tail-top10` workflow:

    ./bin/mzconduct run wikirecent -w stream-top10

The output from this script corresponds to the row-oriented results returned by materialized to
the web server. The implementation of this script in
[app/utils/async_tail.py](./app/utils/async_tail.py).

### Streaming top10 from the Python Web Server to your console

To view the data sent from the web server to the browser, use the `stream-top10` workflow:

    ./bin/mzconduct run wikirecent -w stream-top10

The output corresponds to the batch oriented, JSON results returned by the web server to the
Javascript client. The implementation of this script in
[app/utils/async_stream.py](./app/utils/async_stream.py).