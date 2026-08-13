<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Podman-to-Podman Link

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Hello World frontend/backend using Sketcher with Podman sites and static linking

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
* [Step 6: Deploy the backend service](#step-6-deploy-the-backend-service)
* [Step 7: Deploy the frontend service](#step-7-deploy-the-frontend-service)
* [Step 8: Access the frontend service](#step-8-access-the-frontend-service)
* [Cleaning up](#cleaning-up)
* [Summary](#summary)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example demonstrates linking two Podman-based Skupper sites
running on the same host using static link files.

It contains two services:

* A backend service that exposes an `/api/hello` endpoint running in the
  east Podman namespace.

* A frontend service that sends greetings to the backend running in the
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
The west site enables link acceptance and creates a listener for the backend service.

_**West:**_

~~~ shell
skupper system apply -n west -f west/site.yaml
skupper system apply -n west -f west/listener-podman.yaml
~~~

## Step 2: Bootstrap the west site

Bootstrap the west site using Podman. This creates the Skupper
router and makes the site ready to accept links.

_**West:**_

~~~ shell
skupper system start -n west
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
The east site connects out to west and creates a connector for the backend service.

_**East:**_

~~~ shell
skupper system apply -n east -f east/site.yaml
skupper system apply -n east -f east/connector-podman.yaml
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

## Step 6: Deploy the backend service

Run the backend container in the east namespace using Podman.
The backend listens on port 8080 and returns greetings.

_**East:**_

~~~ shell
podman run -d \
  --name backend \
  -l app=backend \
  -p 8081:8080 \
  quay.io/skupper/hello-world-backend
~~~

## Step 7: Deploy the frontend service

Run the frontend container in the west namespace using Podman.
The frontend connects to "backend:8080" which resolves through the
Skupper network to the east backend.

_**West:**_

~~~ shell
podman run -d \
  --name frontend \
  -p 8888:8080 \
  quay.io/skupper/hello-world-frontend
~~~

## Step 8: Access the frontend service

The frontend is now accessible at http://localhost:8888.
Open a browser and navigate to that URL to see the hello-world
application working across the two Podman sites.

Test manually:
curl http://localhost:8888/api/health
curl http://localhost:8888/

The frontend in west will send requests to the backend in east
via the Skupper link. You should see greetings from the backend pods.

When ready, proceed to cleanup.

## Cleaning up

To remove the Skupper sites and containers, use the following commands:

_**West:**_

~~~ shell
skupper system stop -n west
podman rm -f frontend
~~~

_**East:**_

~~~ shell
skupper system stop -n east
podman rm -f backend
~~~

## Summary

This example demonstrates Podman-to-Podman linking using static link files.
The west site enables linkAccess which auto-generates RouterAccess and creates
static link files at runtime. These files contain Link CRs with TCP endpoints
(127.0.0.1:55671 and 127.0.0.1:45671) plus TLS Secrets for mutual authentication.

The east site includes the copied static link file in its input resources before
bootstrapping. When skupper system start runs, it reads the link file and
establishes a connection to west using the embedded mTLS credentials.

Since both sites run on the same host, the link file uses 127.0.0.1. For sites
on different machines, replace 127.0.0.1 with the actual IP/hostname of the
accepting site before copying the link file.

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
