<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Patient Portal

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### A simple database-backed web application that runs in the public cloud but keeps its data in a private database

This example is part of a [suite of examples][examples] showing the
different ways you can use [Skupper][website] to connect services
across cloud providers, data centers, and edge sites.

[website]: https://skupper.io/
[examples]: https://skupper.io/examples/index.html

#### Contents

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Sites](#sites)
* [Step 1: Access your Kubernetes clusters](#step-1-access-your-kubernetes-clusters)
* [Step 2: Create your Kubernetes namespaces](#step-2-create-your-kubernetes-namespaces)
* [Step 3: Set up your Podman environment](#step-3-set-up-your-podman-environment)
* [Step 4: Install Skupper on your Kubernetes clusters](#step-4-install-skupper-on-your-kubernetes-clusters)
* [Step 5: Install the Skupper command-line tool](#step-5-install-the-skupper-command-line-tool)
* [Step 6: Deploy the application](#step-6-deploy-the-application)
* [Step 7: Create your sites](#step-7-create-your-sites)
* [Step 8: Link your sites](#step-8-link-your-sites)
* [Step 9: Expose application services](#step-9-expose-application-services)
* [Cleaning up](#cleaning-up)
* [Step 11: Cleaning up](#step-11-cleaning-up)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a simple database-backed web application that shows
how you can use Skupper to access a database at a remote site
without exposing it to the public internet.

It contains three services:

  * A PostgreSQL database running on a bare-metal or virtual
    machine in a private data center.

  * A payment-processing service running on Kubernetes in a private
    data center.

  * A web frontend service running on Kubernetes in the public
    cloud.  It uses the PostgreSQL database and the
    payment-processing service.

The example uses two Kubernetes namespaces, `private` and `public`,
to represent the Kubernetes cluster in the private data center and
the cluster in the public cloud.  It uses Podman to run the
database.

<img src="diagram.png" width="640"/>

## Prerequisites

* Access to at least one Kubernetes cluster, from [any provider you
  choose][kube-providers].

* The `kubectl` command-line tool, version 1.15 or later
  ([installation guide][install-kubectl]).

[kube-providers]: https://skupper.io/start/kubernetes.html
[install-kubectl]: https://kubernetes.io/docs/tasks/tools/install-kubectl/

## Sites

This example uses the following sites:

_**Public:**_

~~~ shell
export KUBECONFIG=~/.kube/config-public
kubectl config set-context --current --namespace public
~~~

_**Private:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private
kubectl config set-context --current --namespace private
~~~

_**Podman:**_

~~~ shell
export SKUPPER_PLATFORM=podman
~~~

## Step 1: Access your Kubernetes clusters

Skupper is designed for use with multiple Kubernetes clusters.
The `skupper` and `kubectl` commands use your
[kubeconfig][kubeconfig] and current context to select the cluster
and namespace where they operate.

[kubeconfig]: https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/

This example uses multiple cluster contexts at once. The
`KUBECONFIG` environment variable tells `skupper` and `kubectl`
which kubeconfig to use.

For each cluster, open a new terminal window.  In each terminal,
set the `KUBECONFIG` environment variable to a different path and
log in to your cluster.

_**Public:**_

~~~ shell
export KUBECONFIG=~/.kube/config-public
<provider-specific login command>
~~~

_**Private:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private
<provider-specific login command>
~~~

**Note:** The login procedure varies by provider.

## Step 2: Create your Kubernetes namespaces

The example application has different components deployed to
different Kubernetes namespaces.  To set up our example, we need
to create the namespaces.

For each cluster, use `kubectl create namespace` and `kubectl
config set-context` to create the namespace you wish to use and
set the namespace on your current context.

_**Public:**_

~~~ shell
kubectl create namespace public
kubectl config set-context --current --namespace public
~~~

_**Private:**_

~~~ shell
kubectl create namespace private
kubectl config set-context --current --namespace private
~~~

## Step 3: Set up your Podman environment

Open a new terminal window and set the `SKUPPER_PLATFORM`
environment variable to `podman`.  This sets the Skupper platform
to Podman for this terminal session.

The `skupper system install` enables the Podman API
service (using systemctl) if that service is not already running.
The `skupper system install` command also creates the
Skupper controller container for the current user.

_**Podman:**_

~~~ shell
export SKUPPER_PLATFORM=podman
skupper system install
~~~

If `skupper system install` fails, it is typically due to a systemctl issue. You can try the `podman
system service` command instead:

~~~
podman system service --time 0 unix://$XDG_RUNTIME_DIR/podman/podman.sock &
~~~

## Step 4: Install Skupper on your Kubernetes clusters

Using Skupper on Kubernetes requires the installation of the
Skupper custom resource definitions (CRDs) and the Skupper
controller.

For each cluster, use `kubectl apply` with the Skupper
installation YAML to install the CRDs and controller.

_**Public:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

_**Private:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

## Step 5: Install the Skupper command-line tool

This example uses the Skupper command-line tool to create Skupper
resources.  You need to install the `skupper` command only once
for each development environment.

On Linux or Mac, you can use the install script (inspect it
[here][install-script]) to download and extract the command:

~~~ shell
curl https://skupper.io/v2/install.sh | sh
~~~

The script installs the command under your home directory.  It
prompts you to add the command to your path if necessary.

For Windows and other installation options, see [Installing
Skupper][install-docs].

[install-script]: https://github.com/skupperproject/skupper-website/blob/main/input/install.sh
[install-docs]: https://skupper.io/#installation

## Step 6: Deploy the application

Use `kubectl apply` to deploy the frontend and payment processor
on Kubernetes.  Use `podman run` to start the database on your
local machine.

**Note:** It is important to name your running container using
`--name` to avoid a collision with the container that Skupper
creates for accessing the service.

**Note:** You must use `--network skupper` with the `podman run`
command.

_**Public:**_

~~~ shell
kubectl apply -f frontend/kubernetes.yaml
~~~

_**Private:**_

~~~ shell
kubectl apply -f payment-processor/kubernetes.yaml
~~~

_**Podman:**_

~~~ shell
podman network create skupper
podman run --name database-target --detach --rm -p 5432:5432 quay.io/skupper/patient-portal-database
~~~

## Step 7: Create your sites

Use `skupper site create` to configure each location.  Enable
link access on Public so it can issue tokens for the other sites.
Disable ingress on Private and Podman.

_**Public:**_

~~~ shell
skupper site create public --enable-link-access
~~~

_**Private:**_

~~~ shell
skupper site create private
~~~

_**Podman:**_

~~~ shell
skupper system install
skupper site create podman
skupper system start
~~~

## Step 8: Link your sites

Use `skupper token issue` in Public to generate a token that can
be redeemed by both Private and Podman.  Then, use `skupper token
redeem` from each remote site to create the links.

_**Public:**_

~~~ shell
skupper token issue --redemptions-allowed 2 ~/secret.token
~~~

_**Private:**_

~~~ shell
skupper token redeem ~/secret.token
~~~

_**Podman:**_

~~~ shell
skupper token redeem ~/secret.token
~~~

## Step 9: Expose application services

Use listeners at the consumer site and connectors where each
service runs.

In Public, create listeners for the payment processor and
database.  In Private, create a connector to the
payment-processor workload.  In Podman, create a connector to
the database container.

**Note:** Podman sites do not automatically replicate services
to remote sites.  You need to define the listener on each site
where you wish to make a service available.

_**Public:**_

~~~ shell
skupper listener create payment-processor 8080
skupper listener create database 5432
~~~

_**Private:**_

~~~ shell
skupper connector create payment-processor 8080
~~~

_**Podman:**_

~~~ shell
skupper connector create database 5432 --host database-target
~~~

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands.

_**Public:**_

~~~ shell
skupper delete
~~~

_**Private:**_

~~~ shell
skupper delete
~~~

_**Podman:**_

~~~ shell
skupper delete
~~~

## Step 11: Cleaning up

_**Public:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/frontend
~~~

_**Private:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/payment-processor
~~~

_**Podman:**_

~~~ shell
skupper site delete --all
podman stop database-target
~~~

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
