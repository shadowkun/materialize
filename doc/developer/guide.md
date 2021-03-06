# Developer guide

This guide details what you'll need to contribute to Materialize.

Materialize is written in [Rust] and should compile on any recent stable
version.

Materialize can be connected to many different types of event sources:

* Local files with line-by-line textual events, where structured data can be
  extracted via regular expressions or CSV parsing.
* Custom Kafka topics, where events are encoded with Protobuf or Avro, with
  support for additional encoding formats coming soon.
* Kafka topics managed by a CDC tool like Debezium, where events adhere to a
  particular "envelope" format that distinguishes updates from insertions and
  deletions.
* Streaming HTTP sources? Apache Pulsar sources? With a bit of elbow grease,
  support for any message bus can be added to Materialize!

Note that local file sources are intended only for ad-hoc experimentation and
analysis. Production use cases are expected to use Kafka sources, which have a
better availability and durability story.

## Installing

### C components

Materialize depends on several components that are written in C, so you'll need
a working C compiler. You'll also need to install the [CMake] build system.

On macOS, if you install [Homebrew], you'll be guided through the process of
installing Apple's developer tools, which includes a C compiler. Then it's a
cinch to install CMake:

```
brew install cmake
```

On Debian-based Linux variants, it's even easier:

```shell
sudo apt update
sudo apt install build-essential cmake
```

On other platforms, you'll have to figure out how to get these tools yourself.

### Rust

Install Rust via [rustup]:

```shell
curl https://sh.rustup.rs -sSf | sh
```

Rustup will automatically select the correct toolchain version specified in
[materialize/rust-toolchain](/rust-toolchain).

We recommend that you do _not_ install Rust via your system's package manager.
We closely track the most recent version of Rust. The version of Rust in your
package manager is likely too old to build Materialize.

### Confluent Platform

The [Confluent Platform] bundles [Apache ZooKeeper] and [Apache Kafka] with
several non-free Confluent tools, like the [Confluent Schema Registry] and
[Control Center]. For local development, the [Confluent CLI] allows easy
management of these services.

**Confluent Platform is only required if you need to test Kafka sources and
sinks against a *local* Kafka installation.** If possible, we recommend that you
avoid installing the Confluent Platform, as the installation is tricky and the
stack is very memory hungry.

#### macOS

You will need JDK 8 or 11. The easiest way to install this is via homebrew:

```shell
brew cask install homebrew/cask-versions/adoptopenjdk8
```

Homebrew no longer contains confluent packages, so you'll need to follow the
[manual instructions][confluent-install].

At the time of this writing, that means:

```shell
curl -O http://packages.confluent.io/archive/6.0/confluent-6.0.0.tar.gz
tar -xf confluent-6.0.0.tar.gz
CONFLUENT_HOME=./confluent-6.0.0 ./confluent-6.0.0/bin/confluent local services start
```

#### Linux

On Debian-based Linux variants, it's a tad more involved:

```shell
curl http://packages.confluent.io/deb/5.2/archive.key | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://packages.confluent.io/deb/5.2 stable main"
sudo apt update
sudo apt install openjdk-8-jre-headless confluent-community-2.12
```

On other Linux variants, you'll need to make your own way through [Confluent's
installation instructions][confluent-install]. Note that, at the time of
writing, only Java 8 and 11 are supported.

### Confluent CLI

As of November 2020 you can run:

```shell
curl -L --http1.1 https://cnfl.io/cli | sh -s -- -b /usr/local/bin
```

However, if this ever stops working, check out these great docs on the
[Confluent CLI].

## Building Materialize

Materialize is fully integrated with Cargo, so building it is dead simple:

```shell
git clone git@github.com:MaterializeInc/materialize.git
cd materialize
cargo run --release -- --workers 2
```

Because the MaterializeInc organization requires two-factor authentication
(2FA), you'll need to clone via SSH as indicated above, or [configure a personal
access token for use with HTTPS][github-https].

## Prepping Confluent

As mentioned above, **Confluent Platform is only required need to test Kafka
sources and sinks against a *local* Kafka installation.** If possible, we
recommend that you don't run the Confluent Platform if you don't need it, as it
is very memory hungry.

If you do need the Confluent Platform running locally, execute the following
commands:

```shell
confluent local start kafka     # Also starts Zookeeper.
confluent local start schema-registry
```

You can also use the included `confluent` CLI command to start and stop
individual services. For example:

```shell
confluent local status        # View what services are currently running.
confluent local start kafka   # Start Kafka and any services it depends upon.
confluent local log kafka     # View Kafka log file.
```

Beware that the CLI is fairly buggy, especially around service management.
Putting your computer to sleep often causes the service status to get out of
sync. In other words, trust the output of `confluent local log` and `ps ... |
grep` over the output of `confluent local status`. Still, it's reliable enough
to be more convenient than managing each service manually.

## Symbiosis mode

For the convenience of developers, Materialize has a semi-secret "symbiosis"
mode that turns Materialize into a full HTAP system, rather than an OLAP system
that must sit atop a OLTP system via a CDC pipeline. In other words, where
you would normally need to plug MySQL into Debezium into Kafka into Materialize,
and run all the Confluent services that that entails, you can instead run:

    $ materialized --symbiosis postgres://localhost:5432

When symbiosis mode is active, all DDL statements and all writes will be routed
to the specified PostgreSQL server. `CREATE TABLE`, for example, will create
both a table in PostgreSQL and a source in Materialize that mirrors that table.
`INSERT`, `UPDATE`, and `DELETE` statements that target that table will be
reflected in Materialize for the next `SELECT` statement.

Symbiosis mode is not suitable for production use, as its implementation is
very inefficient. It is, however, excellent for manually taking Materialize
for a spin without the hassle of setting up various Kafka topics and Avro
schemas. It also powers our sqllogictest runner.

See the [symbiosis crate documentation](https://mtrlz.dev/api/symbiosis) for
more details.

**Note:** As of August 2020, we're laying the groundwork to phase out symbiosis
mode with [tables](https://materialize.com/docs/sql/create-table). But we're
stuck with symbiosis mode until tables support `UPDATE` and `DELETE`—at the time
of writing they only support [`INSERT`](https://materialize.com/docs/sql/insert).

## Web UI

Materialize embeds a web UI, which it serves from port 6875. If you're running
Materialize locally, you can view the web UI at http://localhost:6875.

Developing the web UI can be painful, as by default the HTML, CSS, and JS source
code for the UI gets baked into the binary, and so making a change requires a
full rebuild of the binary.

To speed up the development cycle, you can enable the `dev-web` feature like so:

```shell
cd src/materialized
cargo run -- --features=dev-web --dev -w1
```

In this mode, every request for a static file will reload the file from disk.
Changes to standalone CSS and JS files will be reflected immediately upon
reload, without requiring a recompile!

Note that `dev-web` can only hot-reload the the files in
`src/materialized/src/static`. The HTML templates in
`src/materialized/src/templates` use a compile-time templating library called
[`askama`], and so changes to those templates necessarily require a recompile.

For details about adding a new JavaScript/CSS dependency, see the comment in
[`src/materialized/build/npm.rs`](/src/materialized/build/npm.rs).

## Testing

Materialize's testing philosophy is sufficiently complex that it warrants its
own document. See [Developer guide: testing](guide-testing.md).

## Style

CI performs the lawful evil task of ensuring "good code style" with the
following tools:

Tool      | Use                     | Run locally with
----------|-------------------------|-------------------
[Clippy]  | Rust semantic nits      | `./bin/check`
[rustfmt] | Rust code formatter     | `cargo fmt`
Linter    | General formatting nits | `./bin/lint`

See also the [style guide](style.md) for some additional soft
recommendations.

## Submitting and reviewing changes

See [Developer guide: submitting and reviewing changes](guide-changes.md).

## Other repositories

Several components of Materialize are maintained in separate Git repositories.
Where possible, we prefer to keep things in the main repository (a "monorepo"
approach), but when forking existing packages, maintaining a separate repository
makes it easier to integrate changes from upstream.

Some notable repositories include:

  * **[rust-sasl]**, Cyrus SASL bindings for Rust
  * **[rust-krb5-src]**, Rust build system integration for libkrb5, MIT's
    Kerberos implementation.

As mentioned before, because the MaterializeInc organization requires two-factor
authentication (2FA), to clone these repositories you'll need to use either SSH
or [configure a personal access token for use with HTTPS][github-https].

[Apache Kafka]: https://kafka.apache.org
[Apache ZooKeeper]: https://zookeeper.apache.org
[askama]: https://github.com/djc/askama
[Clippy]: https://github.com/rust-lang/rust-clippy
[CMake]: https://cmake.org
[Confluent CLI]: https://docs.confluent.io/current/cli/installing.html#scripted-installation
[Confluent Platform]: https://www.confluent.io/product/confluent-platform/
[Confluent Schema Registry]: https://www.confluent.io/confluent-schema-registry/
[confluent-install]: https://docs.confluent.io/current/installation/installing_cp/index.html
[Control Center]: https://www.confluent.io/confluent-control-center/
[github-https]: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line
[Homebrew]: https://brew.sh
[rust-krb5-src]: https://github.com/MaterializeInc/rust-krb5-src
[rust-sasl]: https://github.com/MaterializeInc/rust-sasl
[Rust]: https://www.rust-lang.org
[rustfmt]: https://github.com/rust-lang/rustfmt
[rustup]: https://www.rust-lang.org/tools/install
[sqlparser]: https://github.com/MaterializeInc/sqlparser
