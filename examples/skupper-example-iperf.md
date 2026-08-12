<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# iPerf

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Perform real-time network throughput measurements while using iPerf3

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
* [Step 5: Create your sites](#step-5-create-your-sites)
* [Step 6: Link your sites](#step-6-link-your-sites)
* [Step 7: Deploy the iperf3 servers](#step-7-deploy-the-iperf3-servers)
* [Step 8: Create connectors for the iperf3 servers](#step-8-create-connectors-for-the-iperf3-servers)
* [Step 9: Create listeners for the iperf3 services](#step-9-create-listeners-for-the-iperf3-services)
* [Step 10: Run benchmark tests across the clusters](#step-10-run-benchmark-tests-across-the-clusters)
* [Cleaning up](#cleaning-up)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This tutorial demonstrates how to perform real-time network throughput measurements across Kubernetes 
using the iperf3 tool.
In this tutorial you:
* deploy iperf3 in two separate clusters
* run iperf3 client test instances

## Prerequisites

* The `kubectl` command-line tool, version 1.15 or later
([installation guide][install-kubectl])

* Access to two clusters to observe performance. 
As an example, the two clusters might consist of:

* A private cloud cluster running on your local machine (**east**)
* A public cloud cluster running in a public cloud provider (**west**)

## Sites

This example uses the following sites:

_**West:**_

~~~ shell
export KUBECONFIG=~/.kube/config-west
kubectl config set-context --current --namespace west
~~~

_**East:**_

~~~ shell
export KUBECONFIG=~/.kube/config-east
kubectl config set-context --current --namespace east
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

_**West:**_

~~~ shell
export KUBECONFIG=~/.kube/config-west
<provider-specific login command>
~~~

_**East:**_

~~~ shell
export KUBECONFIG=~/.kube/config-east
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

_**West:**_

~~~ shell
kubectl create namespace west
kubectl config set-context --current --namespace west
~~~

_**East:**_

~~~ shell
kubectl create namespace east
kubectl config set-context --current --namespace east
~~~

## Step 3: Install Skupper on your Kubernetes clusters

Using Skupper on Kubernetes requires the installation of the
Skupper custom resource definitions (CRDs) and the Skupper
controller.

For each cluster, use `kubectl apply` with the Skupper
installation YAML to install the CRDs and controller.

_**West:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

_**East:**_

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

## Step 5: Create your sites

A Skupper _site_ is a location where your application workloads
are running.  Sites are linked together to form a network for your
application.

For each namespace, use `skupper site create` with a site name of
your choice.  This creates the site resource and deploys the
Skupper router to the namespace.

**Note:** If you are using Minikube, you need to [start minikube
tunnel][minikube-tunnel] before you run `skupper site create`.

<!-- XXX Explain enabling link acesss on one of the sites -->

[minikube-tunnel]: https://skupper.io/start/minikube.html#running-minikube-tunnel

_**West:**_

~~~ shell
skupper site create west --enable-link-access
~~~

_Sample output:_

~~~ console
$ skupper site create west --enable-link-access
Waiting for status...
Site "west" is configured. Check the status to see when it is ready
~~~

_**East:**_

~~~ shell
skupper site create east
~~~

_Sample output:_

~~~ console
$ skupper site create east
Waiting for status...
Site "east" is configured. Check the status to see when it is ready
~~~

You can use `skupper site status` at any time to check the status
of your site.

## Step 6: Link your sites

A Skupper _link_ is a channel for communication between two sites.
Links serve as a transport for application connections and
requests.

Creating a link requires the use of two Skupper commands in
conjunction: `skupper token issue` and `skupper token redeem`.
The `skupper token issue` command generates a secret token that
can be transferred to a remote site and redeemed for a link to the
issuing site.  The `skupper token redeem` command uses the token
to create the link.

**Note:** The link token is truly a *secret*.  Anyone who has the
token can link to your site.  Make sure that only those you trust
have access to it.

First, use `skupper token issue` in west to generate the token.
Then, use `skupper token redeem` in east to link the sites.

_**West:**_

~~~ shell
skupper token issue ~/east-to-west.token
~~~

_**East:**_

~~~ shell
skupper token redeem ~/east-to-west.token
~~~

If your terminal sessions are on different machines, you may need
to use `scp` or a similar tool to transfer the token securely.  By
default, tokens expire after a single use or 15 minutes after
being issued.

## Step 7: Deploy the iperf3 servers

After creating the application router network, deploy `iperf3` in each namespace.

_**East:**_

~~~ shell
kubectl apply -f deployment-iperf3-a.yaml
~~~

_**West:**_

~~~ shell
kubectl apply -f deployment-iperf3-b.yaml
~~~

## Step 8: Create connectors for the iperf3 servers

With Skupper v2, connectors run in the namespace where the workload is deployed.
Create a connector for each iperf3 server so the application network can reach the pods.

_**East:**_

~~~ shell
skupper connector create iperf3-server-a 5201 --workload deployment/iperf3-server-a
~~~

_**West:**_

~~~ shell
skupper connector create iperf3-server-b 5201 --workload deployment/iperf3-server-b
~~~

## Step 9: Create listeners for the iperf3 services

Listeners create service endpoints in each namespace so clients can reach those connectors.
Configure listeners for every iperf3 service in each namespace.

_**East:**_

~~~ shell
skupper listener create iperf3-server-a 5201
skupper listener create iperf3-server-b 5201
~~~

_**West:**_

~~~ shell
skupper listener create iperf3-server-a 5201
skupper listener create iperf3-server-b 5201
~~~

## Step 10: Run benchmark tests across the clusters

After deploying the iperf3 servers into the private and public cloud clusters,
the virtual application network enables communications even though they are 
running in separate clusters.

_**East:**_

~~~ shell
kubectl exec $(kubectl get pod -l application=iperf3-server-a -o=jsonpath='{.items[0].metadata.name}') -- iperf3 -c iperf3-server-a > results/east-to-a.log
kubectl exec $(kubectl get pod -l application=iperf3-server-a -o=jsonpath='{.items[0].metadata.name}') -- iperf3 -c iperf3-server-b > results/east-to-b.log
~~~

_**West:**_

~~~ shell
kubectl exec $(kubectl get pod -l application=iperf3-server-b -o=jsonpath='{.items[0].metadata.name}') -- iperf3 -c iperf3-server-a > results/west-to-a.log
kubectl exec $(kubectl get pod -l application=iperf3-server-b -o=jsonpath='{.items[0].metadata.name}') -- iperf3 -c iperf3-server-b > results/west-to-b.log
skupper debug dump
~~~

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands.

_**East:**_

~~~ shell
kubectl delete deployment iperf3-server-a
skupper delete
~~~

_**West:**_

~~~ shell
kubectl delete deployment iperf3-server-b
skupper delete
~~~

## Next steps

- [Find more examples](https://skupper.io/examples/)

## About this example

This example was produced using [Skewer][skewer], a library for
documenting and testing Skupper examples.

[skewer]: https://github.com/skupperproject/skewer

Skewer provides utility functions for generating the README and
running the example steps.  Use the `./plano` command in the project
root to see what is available.

To quickly stand up the example using Minikube, try the `./plano demo`
command.
