<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Accessing an ActiveMQ message broker using Skupper

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Use public cloud resources to process data from a private message broker

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
* [Step 3: Install Skupper on your Kubernetes clusters](#step-3-install-skupper-on-your-kubernetes-clusters)
* [Step 4: Install the Skupper command-line tool](#step-4-install-the-skupper-command-line-tool)
* [Step 5: Deploy the message broker](#step-5-deploy-the-message-broker)
* [Step 6: Create your sites](#step-6-create-your-sites)
* [Step 7: Link your sites](#step-7-link-your-sites)
* [Step 8: Expose the message broker](#step-8-expose-the-message-broker)
* [Step 9: Run the client](#step-9-run-the-client)
* [Cleaning up](#cleaning-up)
* [Summary](#summary)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a simple message application that shows how you can
use Skupper to access an ActiveMQ broker at a remote site without
exposing it to the public internet.

It contains two services:

* An ActiveMQ broker named `broker1` running in a private data center.
  The broker has a queue named `queue1`.

* An AMQP client running in the public cloud.  It sends 10 messages
  to `queue1` and then receives them back.

The example uses two Kubernetes namespaces, `private` and `public`,
to represent the private data center and public cloud.

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

## Step 3: Install Skupper on your Kubernetes clusters

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

## Step 4: Install the Skupper command-line tool

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

## Step 5: Deploy the message broker

_**Private:**_

~~~ shell
kubectl apply -f broker1.yaml
~~~

## Step 6: Create your sites

Use `skupper site create` to configure each location.  Enable link
access on Public so it can issue tokens.  Disable ingress on
Private to keep the broker hidden from the internet.

_**Public:**_

~~~ shell
skupper site create public --enable-link-access
~~~

_**Private:**_

~~~ shell
skupper site create private
~~~

## Step 7: Link your sites

Use `skupper token issue` in Public to generate a token, then use
`skupper token redeem` in Private to create the link.  The token is
a secret; handle it carefully.

_**Public:**_

~~~ shell
skupper token issue ~/public.token
~~~

_**Private:**_

~~~ shell
skupper token redeem ~/public.token
~~~

## Step 8: Expose the message broker

Create a listener in Public where the client runs.  Create a
connector in Private so the broker workload is reachable on the
network under the service name `broker1`.

_**Public:**_

~~~ shell
skupper listener create broker1 5672
~~~

_**Private:**_

~~~ shell
skupper connector create broker1 5672
~~~

## Step 9: Run the client

_**Public:**_

~~~ shell
kubectl run client --attach --rm --restart Never --image quay.io/skupper/activemq-example-client --env SERVER=broker1 --pod-running-timeout=5m
~~~

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands.

_**Public:**_

~~~ shell
skupper site delete --all
~~~

_**Private:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/broker1
~~~

## Summary

Skupper creates a virtual application network that lets the client in
`public` reach the broker in `private` without exposing the broker to
the internet.  The listener in `public` makes `broker1` appear local,
and the connector in `private` forwards the traffic to the actual
Artemis deployment.

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
