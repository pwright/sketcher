<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Podman-to-Podman Link

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### GetBack demo using Sketcher with Podman sites and static linking

This example is part of a [suite of examples][examples] showing the
different ways you can use [Skupper][website] to connect services
across cloud providers, data centers, and edge sites.

[website]: https://skupper.io/
[examples]: https://skupper.io/examples/index.html

#### Contents

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Sites](#sites)
* [Step 1: Apply west site resources](#step-1-apply-west-site-resources)
* [Step 2: Bootstrap the west site](#step-2-bootstrap-the-west-site)
* [Step 3: Generate a link for east](#step-3-generate-a-link-for-east)
* [Step 4: Apply east site resources](#step-4-apply-east-site-resources)
* [Step 5: Bootstrap the east site](#step-5-bootstrap-the-east-site)
* [Step 6: Deploy the getback service](#step-6-deploy-the-getback-service)
* [Step 7: Expose the getback service](#step-7-expose-the-getback-service)
* [Step 8: Expose the getback metrics service](#step-8-expose-the-getback-metrics-service)
* [Step 9: Create listener in west](#step-9-create-listener-in-west)
* [Step 10: Create metrics listener in west](#step-10-create-metrics-listener-in-west)
* [Step 11: Deploy the frontend](#step-11-deploy-the-frontend)
* [Step 12: Access the frontend service](#step-12-access-the-frontend-service)
* [Cleaning up](#cleaning-up)
* [Summary](#summary)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example demonstrates linking two Podman-based Skupper sites
running on the same host using static link files.

It contains the GetBack application:

* A getback service that exposes an HTTP endpoint running in the
  east Podman namespace.

* A client that sends requests to the getback service running in the
  west Podman namespace.

The sites use static link files for connection - west accepts links
and generates a static link file, which east uses to connect.

## Prerequisites

* Access to at least one Kubernetes cluster, from [any provider you
  choose][kube-providers].

* The `kubectl` command-line tool, version 1.15 or later
  ([installation guide][install-kubectl]).

[kube-providers]: https://skupper.io/start/kubernetes.html
[install-kubectl]: https://kubernetes.io/docs/tasks/tools/install-kubectl/

## Sites

This example uses the following sites:

_**West:**_

~~~ shell
export SKUPPER_PLATFORM=podman
~~~

_**East:**_

~~~ shell
export SKUPPER_PLATFORM=podman
~~~

## Step 1: Apply west site resources

Apply the west site resources using skupper system apply.
The west site enables link acceptance.

_**West:**_

~~~ shell
skupper system apply -n west -f west/site.yaml
~~~

## Step 2: Bootstrap the west site

Bootstrap the west site using Podman. This creates the Skupper
router and makes the site ready to accept links.

_**West:**_

~~~ shell
skupper system start -n west
sleep 3
~~~

_Sample output:_

~~~ console
$ skupper system start -n west
Site "west" is ready
~~~

## Step 3: Generate a link for east

Generate a link file that east can use to connect to west.
The `skupper link generate` command creates a Link CR with endpoints
(127.0.0.1:55671 and 127.0.0.1:45671) plus a Secret with mTLS credentials.

_**West:**_

~~~ shell
skupper link generate -n west > ./east/link-to-west.yaml
~~~

## Step 4: Apply east site resources

Apply the east site resources using skupper system apply.
The east site connects out to west.

_**East:**_

~~~ shell
skupper system apply -n east -f east/site.yaml
skupper system apply -n east -f east/link-to-west.yaml
~~~

## Step 5: Bootstrap the east site

Bootstrap the east site using Podman. The site will start and establish
a mutual TLS connection to west using the link credentials.

_**East:**_

~~~ shell
skupper system start -n east
~~~

_Sample output:_

~~~ console
$ skupper system start -n east
Site "east" is ready
Link to "west" is ready
~~~

## Step 6: Deploy the getback service

Run the getback container in the east namespace using Podman.
The container listens on ports 9091 (API) and 9092 (metrics), published to 127.0.0.1:19091 and 127.0.0.1:19092.

_**East:**_

~~~ shell
podman run -d --replace --name getback-east -p 19091:9091 -p 19092:9092 quay.io/pwright/getback:hc
~~~

## Step 7: Expose the getback service

Expose the getback service in east using the skupper CLI with routing key "getback".

_**East:**_

~~~ shell
skupper connector create getback 19091 --routing-key getback --host 127.0.0.1 -n east
~~~

## Step 8: Expose the getback metrics service

Expose the getback metrics service (port 9092) in east using the skupper CLI with routing key "getback-metrics".

_**East:**_

~~~ shell
skupper connector create getback-metrics 19092 --routing-key getback-metrics --host 127.0.0.1 -n east
~~~

## Step 9: Create listener in west

Create a listener in west on port 9191 binding to 0.0.0.0 for the getback service.

_**West:**_

~~~ shell
skupper listener create getback 9191 --host 0.0.0.0 --routing-key getback -n west
~~~

## Step 10: Create metrics listener in west

Create a listener in west on port 9192 binding to 0.0.0.0 for the getback metrics service.

_**West:**_

~~~ shell
skupper listener create getback-metrics 9192 --host 0.0.0.0 --routing-key getback-metrics -n west
~~~

## Step 11: Deploy the frontend

Run the getback frontend container in the west namespace using Podman.
The frontend listens on port 9093 and will connect to the getback service via the listener at localhost:9191.

_**West:**_

~~~ shell
podman run -d --replace --name getback-west --network host -e BACKEND_URL=http://localhost:9191 quay.io/pwright/getback:hc
~~~

## Step 12: Access the frontend service

The frontend is now accessible at http://localhost:9093.
Test the application:

_**West:**_

~~~ shell
~~~

You can access the web interface at [http://localhost:9093](http://localhost:9093).

The frontend sends requests to localhost:9191, which the Skupper listener
forwards to the getback service in east via the Skupper link.

You can also access the metrics endpoint at [http://localhost:9192](http://localhost:9192).

When ready, proceed to cleanup.

## Cleaning up

To remove the Skupper sites and containers, use the following commands:

_**West:**_

~~~ shell
skupper site delete -n west
podman rm -f getback-west
~~~

_**East:**_

~~~ shell
skupper site delete -n east
podman rm -f getback-east
~~~

## Summary

This example demonstrates Podman-to-Podman linking using static link files
with the GetBack application.

The west site enables linkAccess which auto-generates RouterAccess and creates
static link files at runtime. These files contain Link CRs with TCP endpoints
(127.0.0.1:55671 and 127.0.0.1:45671) plus TLS Secrets for mutual authentication.

The east site includes the copied static link file in its input resources before
bootstrapping. When skupper system start runs, it reads the link file and
establishes a connection to west using the embedded mTLS credentials.

The getback service is exposed in east using "skupper connector" with routing key "getback",
and west creates a listener on 0.0.0.0:9191 using "skupper listener" to forward traffic.

The frontend container runs with --network host so it can reach the listener at localhost:9191.

Since both sites run on the same host, the link file uses 127.0.0.1. For sites
on different machines, replace 127.0.0.1 with the actual IP/hostname of the
accepting site before copying the link file.

## Port Conflict Prevention

This example includes a 3-second sleep after starting the west site before
generating the link. This ensures router ports have stabilized and prevents
the link file from containing stale port numbers if the router changed ports
due to conflicts.

## Next steps

Check out the other [examples][examples] on the Skupper website.

## About this example

This example was produced using [Skewer][skewer], a library for
documenting and testing Skupper examples.

[skewer]: https://github.com/skupperproject/skewer

Skewer provides utility functions for generating the README and
running the example steps.  Use the `./plano` command in the project
root to see what is available.

To quickly stand up the example using Minikube, try the `./plano demo`
command.
