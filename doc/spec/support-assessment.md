# Support Assessment Dashboard: Infrastructure

(Related discussions: https://github.com/aquarist-labs/forum/discussions/24)

## Problem Description

The support assessment dashboard is a feature that gives end-users insight
into how well their cluster conforms to a support envelope based on
continuously measuring and evaluating system state. This document
proposes infrastructure to effectively do this.

We can roughly divide the problem into:
1. Data sources measuring system state
2. Data gathering, preparation, and joining multiple sources
3. Rule evaluation
4. User interface (alerts, notifications, dashboard)

The document focuses on 2. 3. while touching 1.

## Challenges

- When gathering and joining data we must take into account that
  keeping a copy of all state in memory won't scale
- We must join data from diverse sources like the manger, Prometheus,
  cluster maps, Aquarium, Ceph orchestrator. All having different schema.
- Rules are subject to configuration and change. Changes here must be easy.

## Proposed Change

Use Prometheus to gather, prepare, join and evaluate rules on numeric
metrics. Rules are Prometheus alerts, written in PromQL and tested
with the [`promtool`](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules)

Begin with readily-available metrics from Prometheus node exporter and
Ceph manager's Prometheus exporter. Implement custom Prometheus
exporters where necessary. Abstract complex queries behind simple
numeric metrics where appropriate and necessary due to the lack of a
string metric type. Example: Metric `outdated_client 42`
instead of metrics `client{version="23.42"} 42`.

Rules on data from logs and audit events will require another approach
and are out of scope of this change.

A Bubbles Extra[^1] manages and configures Prometheus and collects alerts
for presentation.

[^1]: Bubbles extension mechanism for non-upstream code ([Source ](https://github.com/ceph/bubbles/tree/main)).

### Bubbles

A Bubbles extra manages the Prometheus life cycle using the manager API
to the orchestrator module. Handler for manager commands allow a
service on the Prometheus container to poll configuration directly
from the Bubbles extra.

### Prometheus

Containerized and run using the custom container feature of cephadm.
This Prometheus is separate from the one shipped with cephadm.

Our container runs once per cluster with its state stored on a RBD
image with ext4. On start the containers receive a `ceph.conf` and
credentials to interact with the cluster. Adapter service
daemons running beside Prometheus facilitate runtime configuration
from the Bubbles module reaching Prometheus.

#### Target Discovery

Discover targets by using [HTTP service discovery](https://prometheus.io/docs/prometheus/latest/http_sd/)

Run a simple local service daemon that translates HTTP SD requests
into RADOS manager commands handled by Bubbles.

#### Rule Configuration

Prometheus can't load rules from HTTP SD; it requires a local file and
a signal or HTTP call to update.

Similar to the target discovery use a local service daemon either
polling Bubbles via manager commands or watch RADOS objects.

#### Storage

We use the default local file backed to persist metric data.
Considering Ceph as the only storage option, we can either use CephFS
or RBD. Exchanging one for the other later is trivial.

Since we do not need concurrent file access and Prometheus actually discourages non-local
filesystems (See warning in the [docs](https://prometheus.io/docs/prometheus/latest/storage/)), RBD is the
best choice for now.

#### The Case for Running a Second Prometheus

Cephadm already runs Prometheus to aggregate metrics for the Dashboard
and Grafana, since our use case is similar we could use that
Prometheus as well. It is beneficial to run a second Prometheus with
little drawbacks. Key arguments are:
- We don't require long data retention, minimizing disk space
  requirements
- Running on shared store, we can migrate it between hosts giving us a
  simple availability story. On fail over we would use freshness, but
  maintain consistency. (The alternative would be multiple instances
  with varying staleness)
- Simplified configuration

### Dashboard

The dashboard part is out of scope for this proposal. Initially we have
a simple JSON HTTP endpoint exporting support assessment data.

### Custom Exporter

We will add or extend existing Prometheus exporters where necessary.

Where we create new exporters we may want to consider adding
additional `/detail/$metric_name`-style endpoints. Bubbles could query
them to receive additional information for human consumption not
available from Prometheus directly.

## Alternatives

### Cephadm Configchecks

Configuration checks build into the Ceph cephadm manager module
([`pybind/mgr/cephadm/configchecks.py`](https://github.com/ceph/ceph/blob/master/src/pybind/mgr/cephadm/configchecks.py)).
Tightly integrated with the module for rule execution and command
handling. Creates an in memory copy of relevant cluster state. Has no
query or rule engine abstraction on top of the gathered data. Checks
are Python code processing the gathered data directly. Failing checks
raise Ceph health warnings. Manager commands can enable and disable
individual checks. Check code is part of the checker.

Supported checks:
- Consistent kernel security modules
- Host subscription state
- Hosts connected to the Ceph cluster public network
- Common MTUs and link speeds
- Hosts have the cluster and public networks configured
- Consistent kernel and Ceph versions

### Build Our Own Gathering and Rule Execution Framework

Similar to how configchecks lives in cephadm build a data gathering and
rule execution framework in a Bubbles module.

Rule execution might be done with rational queries or
even unification. There are Python rule engine libraries, but
possibly nothing as battle tested as Prometheus. A MiniKanren
implementation and Durable Rules was briefly evaluated and considered
too risky.

Data gathering is also challenging: Sources may change formats,
joining is not always straight forward because of different
naming schemes. Keeping the memory footprint low and supporting
historical queries is challenging.

## Why Prometheus?

Prometheus is a de facto industry standard time series database and
alerting system. It is stable and has good performance. We can
leverage [many](https://prometheus.io/docs/instrumenting/exporters/) existing exporters. PromQL is widely understood and
allows interactive rule development. Custom exporters are easy to
write.

There are synergetic effects with Ceph, especially when adding more
and more interesting metrics.

## Consequences

Going with Prometheus saves us from building our own rule engine or
writing a lot of code to process state into alert conditions
(configchecks.py). Writing rules will become easier the more we have
and the more data sources we integrate. We will loose some flexibility, as
we can't "just" query arbitrary string state data without processing
it first.

## Status

Proposed. [Prototype demoed](https://github.com/aquarist-labs/forum/discussions/24#discussioncomment-1947494).

## Milestones

1. PoC and Design Doc
2. PoC -> MVP: Code in repository, deployable, reasonable test coverage, initial set of rules
   written, basic dashboard contain {red, amber, green} and 'why?'
1337. Profit
