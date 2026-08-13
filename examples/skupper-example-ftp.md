<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Accessing an FTP server using Skupper

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Securely connect to an FTP server on a remote Kubernetes cluster

This example is part of a [suite of examples][examples] showing the
different ways you can use [Skupper][website] to connect services
across cloud providers, data centers, and edge sites.

[website]: https://skupper.io/
[examples]: https://skupper.io/examples/index.html

#### Contents

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Sites](#sites)
* [Step 1: Install the Skupper command-line tool](#step-1-install-the-skupper-command-line-tool)
* [Step 2: Access your Kubernetes clusters](#step-2-access-your-kubernetes-clusters)
* [Step 3: Install Skupper on your Kubernetes clusters](#step-3-install-skupper-on-your-kubernetes-clusters)
* [Step 4: Create your sites](#step-4-create-your-sites)
* [Step 5: Link your sites](#step-5-link-your-sites)
* [Step 6: Deploy the FTP server](#step-6-deploy-the-ftp-server)
* [Step 7: Expose the FTP server to the Virtual Application Network](#step-7-expose-the-ftp-server-to-the-virtual-application-network)
* [Step 8: Run the FTP client for put operation](#step-8-run-the-ftp-client-for-put-operation)
* [Step 9: Run the FTP client for get operation](#step-9-run-the-ftp-client-for-get-operation)
* [Step 10: Cleaning Up](#step-10-cleaning-up)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example shows you how you can use Skupper to connect an FTP
client on one Kubernetes cluster to an FTP server on another.

It demonstrates use of Skupper with multi-port services such as FTP.
It uses FTP in passive mode (which is more typical these days) and a
[restricted port range][ports] that simplifies Skupper
configuration.

[ports]: https://github.com/skupperproject/skupper-example-ftp/blob/main/server/kubernetes.yaml#L25-L28

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

## Step 1: Install the Skupper command-line tool

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

## Step 2: Access your Kubernetes clusters

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

## Step 4: Create your sites

A Skupper _site_ is a location where components of your
application are running.  Sites are linked together to form a
network for your application.  In Kubernetes, a site is associated
with a namespace.

Use the kubectl apply command to declaratively create sites in the kubernetes
namespaces. This deploys the Skupper router. Then use kubectl get site to see
the outcome.

**Note:** If you are using Minikube, you need to [start minikube
tunnel][minikube-tunnel] before you configure skupper.

[minikube-tunnel]: https://skupper.io/start/minikube.html#running-minikube-tunnel

_**Public:**_

~~~ shell
kubectl apply -f ./public-crs/site.yaml
kubectl wait --for condition=Ready --timeout=3m site/public
~~~

_Sample output:_

~~~ console
$ kubectl wait --for condition=Ready --timeout=3m site/public
site.skupper.io/public created
site.skupper.io/public condition met
~~~

_**Private:**_

~~~ shell
kubectl apply -f ./private-crs/site.yaml
kubectl wait --for condition=Ready --timeout=3m site/private
~~~

_Sample output:_

~~~ console
$ kubectl wait --for condition=Ready --timeout=3m site/private
site.skupper.io/private created
site.skupper.io/private condition met
~~~

## Step 5: Link your sites

A Skupper _link_ is a channel for communication between two sites.
Links serve as a transport for application connections and
requests.

Creating a link requires use of two `skupper` commands in
conjunction, `skupper token issue` and `skupper token redeem`.

The `skupper token issue` command generates a secret token that
signifies permission to create a link.  The token also carries the
link details.  Then, in a remote site, The `skupper token
redeem` command uses the token to create a link to the site
that generated it.

**Note:** The link token is truly a *secret*.  Anyone who has the
token can link to your site.  Make sure that only those you trust
have access to it.

First, use `skupper token issue` in public to generate the
token.  Then, use `skupper token redeem` in private to link the
sites.

_**Public:**_

~~~ shell
skupper token issue ~/public.token
~~~

_**Private:**_

~~~ shell
skupper token redeem ~/public.token
~~~

If your terminal sessions are on different machines, you may need
to use `scp` or a similar tool to transfer the token securely.  By
default, tokens expire after a single use or 15 minutes after
creation.  User skupper link status command to check link is in operational state.

## Step 6: Deploy the FTP server

In Private, use `kubectl apply` to deploy the FTP server.

_**Private:**_

~~~ shell
kubectl apply -f ./private-crs/ftp_service.yaml
~~~

_Sample output:_

~~~ console
$ kubectl apply -f ./private-crs/ftp_service.yaml
deployment.apps/ftp-server created
~~~

## Step 7: Expose the FTP server to the Virtual Application Network

Create Skupper listeners and connectors to expose the FTP service to the public cluster.
The vsftp app used in this example uses port 21 as the control port, which is utilized
to send commands to the FTP servier like login, list and get.   Port 21100 is used to 
transfer data between the FTP client and server.  In private, we will create two connectors. 
Then, in public, we will create two listeners.

_**Private:**_

~~~ shell
kubectl apply -f ./private-crs/connector.yaml
~~~

_Sample output:_

~~~ console
$ kubectl apply -f ./private-crs/connector.yaml
connector.skupper.io/ftp-server created
connector.skupper.io/ftp-passive created
~~~

_**Public:**_

~~~ shell
kubectl apply -f ./public-crs/listener.yaml
~~~

_Sample output:_

~~~ console
$ kubectl apply -f ./public-crs/listener.yaml
listener.skupper.io/ftp-server created
listener.skupper.io/ftp-passive created
~~~

Status of the listeners and connectors can be verified using `show connector status` and
`show listener status`.

## Step 8: Run the FTP client for put operation

In Public, use `kubectl run` and the `curl` image to perform FTP put operations.

_**Public:**_

~~~ shell
echo "Hello!" | kubectl run ftp-client --stdin --rm --image=docker.io/curlimages/curl --restart=Never -- -s -T - ftp://example:example@ftp-server/greeting
~~~

_Sample output:_

~~~ console
$ echo "Hello!" | kubectl run ftp-client --stdin --rm --image=docker.io/curlimages/curl --restart=Never -- -s -T - ftp://example:example@ftp-server/greeting
pod "ftp-client" deleted
~~~

## Step 9: Run the FTP client for get operation

In Public, use `kubectl run` and the `curl` image to perform FTP get operations.

_**Public:**_

~~~ shell
kubectl run ftp-client --attach --rm --image=docker.io/curlimages/curl --restart=Never -- -s ftp://example:example@ftp-server/greeting
~~~

_Sample output:_

~~~ console
$ kubectl run ftp-client --attach --rm --image=docker.io/curlimages/curl --restart=Never -- -s ftp://example:example@ftp-server/greeting
Hello!
pod "ftp-client" deleted
~~~

## Step 10: Cleaning Up

To test remove Skupper and the other resources from this exercise, use
the following commands.

_**Private:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/ftp-server
~~~

_**Public:**_

~~~ shell
skupper site delete --all
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
