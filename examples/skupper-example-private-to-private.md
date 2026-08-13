<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Hello World private to private

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Connect services in isolated on-prem sites

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
* [Step 3: Deploy the frontend and backend](#step-3-deploy-the-frontend-and-backend)
* [Step 4: Install Skupper on your Kubernetes clusters](#step-4-install-skupper-on-your-kubernetes-clusters)
* [Step 5: Install the Skupper command-line tool](#step-5-install-the-skupper-command-line-tool)
* [Step 6: Create your sites](#step-6-create-your-sites)
* [Step 7: Link your sites](#step-7-link-your-sites)
* [Step 8: Expose the backend service](#step-8-expose-the-backend-service)
* [Step 9: Access the frontend service](#step-9-access-the-frontend-service)
* [Cleaning up](#cleaning-up)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a basic multi-service HTTP application deployed
across two Kubernetes clusters, each in its own private data center.

It contains two services:

* A backend service that exposes an `/api/hello` endpoint.  It
  returns greetings of the form `Hi, <your-name>.  I am <my-name>
  (<pod>)`.

* A frontend service that connects to the backend.  It sends
  greetings to the backend and fetches new greetings in response.

The backend service runs in on-prem cluster "private1", and the
frontend service runs in on-prem cluster "private2".  The private
sites are linked by a relay site in the public cloud.  Skupper
enables the frontend to connect to the backend over a secure
dedicated application network.

<img src="images/entities.svg" style="max-width: 100%;"/>

## Prerequisites

* Access to at least one Kubernetes cluster, from [any provider you
  choose][kube-providers].

* The `kubectl` command-line tool, version 1.15 or later
  ([installation guide][install-kubectl]).

[kube-providers]: https://skupper.io/start/kubernetes.html
[install-kubectl]: https://kubernetes.io/docs/tasks/tools/install-kubectl/

## Sites

This example uses the following sites:

_**Private 1:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private1
kubectl config set-context --current --namespace private1
~~~

_**Private 2:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private2
kubectl config set-context --current --namespace private2
~~~

_**Relay:**_

~~~ shell
export KUBECONFIG=~/.kube/config-relay
kubectl config set-context --current --namespace relay
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

_**Private 1:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private1
<provider-specific login command>
~~~

_**Private 2:**_

~~~ shell
export KUBECONFIG=~/.kube/config-private2
<provider-specific login command>
~~~

_**Relay:**_

~~~ shell
export KUBECONFIG=~/.kube/config-relay
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

_**Private 1:**_

~~~ shell
kubectl create namespace private1
kubectl config set-context --current --namespace private1
~~~

_**Private 2:**_

~~~ shell
kubectl create namespace private2
kubectl config set-context --current --namespace private2
~~~

_**Relay:**_

~~~ shell
kubectl create namespace relay
kubectl config set-context --current --namespace relay
~~~

## Step 3: Deploy the frontend and backend

Deploy the Hello World components, placing the frontend on one
cluster and the backend on the other.

Use `kubectl create deployment` to deploy the frontend in Private 1
and the backend in Private 2.

_**Private 1:**_

~~~ shell
kubectl create deployment frontend --image quay.io/skupper/hello-world-frontend
~~~

_**Private 2:**_

~~~ shell
kubectl create deployment backend --image quay.io/skupper/hello-world-backend --replicas 3
~~~

## Step 4: Install Skupper on your Kubernetes clusters

Using Skupper on Kubernetes requires the installation of the
Skupper custom resource definitions (CRDs) and the Skupper
controller.

For each cluster, use `kubectl apply` with the Skupper
installation YAML to install the CRDs and controller.

_**Private 1:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

_**Private 2:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

_**Relay:**_

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

## Step 6: Create your sites

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

_**Private 1:**_

~~~ shell
skupper site create private1
~~~

_**Private 2:**_

~~~ shell
skupper site create private2
~~~

_**Relay:**_

~~~ shell
skupper site create relay --enable-link-access
~~~

You can use `skupper site status` at any time to check the status
of your site.

## Step 7: Link your sites

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

First, use `skupper token issue` in Relay to generate a token
for each private site.  Then, use `skupper token redeem` in
Private 1 and 2 to link the sites.

_**Relay:**_

~~~ shell
skupper token issue ~/relay1.token
skupper token issue ~/relay2.token
~~~

_**Private 1:**_

~~~ shell
skupper token redeem ~/relay1.token
~~~

_**Private 2:**_

~~~ shell
skupper token redeem ~/relay2.token
~~~

If your terminal sessions are on different machines, you may need
to use `scp` or a similar tool to transfer the token securely.  By
default, tokens expire after a single use or 15 minutes after
being issued.

## Step 8: Expose the backend service

We now have our sites linked to form a Skupper network, but no
services are exposed on it.

Skupper uses _listeners_ and _connectors_ to expose services
across sites inside a Skupper network.  A listener is a local
endpoint for client connections, configured with a routing key.  A
connector exists in a remote site and binds a routing key to a
particular set of servers.  Skupper routers forward client
connections from local listeners to remote connectors with
matching routing keys.

In Private 1, use the `skupper listener create` command to create a
listener for the backend.  In Private 2, use the `skupper connector
create` command to create a matching connector.

_**Private 1:**_

~~~ shell
skupper listener create backend 8080
~~~

_Sample output:_

~~~ console
$ skupper listener create backend 8080
Waiting for create to complete...
Listener "backend" is ready
~~~

_**Private 2:**_

~~~ shell
skupper connector create backend 8080
~~~

_Sample output:_

~~~ console
$ skupper connector create backend 8080
Waiting for create to complete...
Connector "backend" is ready
~~~

The commands shown above use the name argument, `backend`, to also
set the default routing key and pod selector.  You can use the
`--routing-key` and `--selector` options to set specific values.

<!-- You can also use `--workload` -- more convenient! -->

## Step 9: Access the frontend service

In order to use and test the application, we need external access
to the frontend.

Use `kubectl port-forward` to make the frontend available at
`localhost:8080`.

_**Private 1:**_

~~~ shell
kubectl port-forward deployment/frontend 8080:8080
~~~

You can now access the web interface by navigating to
[http://localhost:8080](http://localhost:8080) in your browser.

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands:

_**Private 1:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/frontend
~~~

_**Private 2:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/backend
~~~

_**Relay:**_

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
