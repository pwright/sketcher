<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Hello World

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### A minimal HTTP application deployed across Kubernetes clusters using Skupper

This example is part of a [suite of examples][examples] showing the
different ways you can use [Skupper][website] to connect services
across cloud providers, data centers, and edge sites.

[website]: https://skupper.io/
[examples]: https://skupper.io/examples/index.html

#### Contents

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Sites](#sites)
* [Step 1: Start the Kind load balancer](#step-1-start-the-kind-load-balancer)
* [Step 2: Access your Kubernetes clusters](#step-2-access-your-kubernetes-clusters)
* [Step 3: Create your Kubernetes namespaces](#step-3-create-your-kubernetes-namespaces)
* [Step 4: Deploy the frontend and backend](#step-4-deploy-the-frontend-and-backend)
* [Step 5: Install Skupper on your Kubernetes clusters](#step-5-install-skupper-on-your-kubernetes-clusters)
* [Step 6: Install the Skupper command-line tool](#step-6-install-the-skupper-command-line-tool)
* [Step 7: Create your sites](#step-7-create-your-sites)
* [Step 8: Link your sites](#step-8-link-your-sites)
* [Step 9: Expose the backend service](#step-9-expose-the-backend-service)
* [Step 10: Expose the backend metrics service](#step-10-expose-the-backend-metrics-service)
* [Step 11: Access the frontend service](#step-11-access-the-frontend-service)
* [Cleaning up](#cleaning-up)
* [Summary](#summary)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a very simple multi-service HTTP application
deployed across Kubernetes clusters using Skupper.

It contains two services:

* A backend service that exposes an `/api/hello` endpoint.  It
  returns greetings of the form `Hi, <your-name>.  I am <my-name>
  (<pod-name>)`.

* A frontend service that sends greetings to the backend and
  fetches new greetings in response.

With Skupper, you can place the backend in one cluster and the
frontend in another and maintain connectivity between the two
services without exposing the backend to the public internet.

<img src="images/entities.svg" width="640"/>

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
export KUBECONFIG=~/.kube/config-west
kubectl config set-context --current --namespace west
~~~

_**East:**_

~~~ shell
export KUBECONFIG=~/.kube/config-east
kubectl config set-context --current --namespace east
~~~

## Step 1: Start the Kind load balancer

Kind clusters do not include a cloud load balancer by default.
This example uses `cloud-provider-kind` to provide external addresses for Kubernetes services of type `LoadBalancer`.
Start it before creating the Skupper sites, and leave it running while you work through the example.

_**West:**_

~~~ shell
sudo cloud-provider-kind
~~~

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

## Step 3: Create your Kubernetes namespaces

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

## Step 4: Deploy the frontend and backend

Deploy the Hello World components, placing the frontend on one
cluster and the backend on the other.

Use `kubectl create deployment` to deploy the frontend in West
and the backend in East.

_**West:**_

~~~ shell
kubectl create deployment frontend --image quay.io/pwright/getback:hc
~~~

_**East:**_

~~~ shell
kubectl create deployment backend --image quay.io/pwright/getback:hc --replicas 3
~~~

## Step 5: Install Skupper on your Kubernetes clusters

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

## Step 6: Install the Skupper command-line tool

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

## Step 7: Create your sites

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

## Step 8: Link your sites

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

First, use `skupper token issue` in West to generate the token.
Then, use `skupper token redeem` in East to link the sites.

_**West:**_

~~~ shell
skupper token issue ~/secret.token
~~~

_Sample output:_

~~~ console
$ skupper token issue ~/secret.token
Waiting for token status ...

Grant "west-cad4f72d-2917-49b9-ab66-cdaca4d6cf9c" is ready
Token file /run/user/1000/skewer/secret.token created

Transfer this file to a remote site. At the remote site,
create a link to this site using the "skupper token redeem" command:

	skupper token redeem <file>

The token expires after 1 use(s) or after 15m0s.
~~~

_**East:**_

~~~ shell
skupper token redeem ~/secret.token
~~~

_Sample output:_

~~~ console
$ skupper token redeem ~/secret.token
Waiting for token status ...
Token "west-cad4f72d-2917-49b9-ab66-cdaca4d6cf9c" has been redeemed
You can now safely delete /run/user/1000/skewer/secret.token
~~~

If your terminal sessions are on different machines, you may need
to use `scp` or a similar tool to transfer the token securely.  By
default, tokens expire after a single use or 15 minutes after
being issued.

## Step 9: Expose the backend service

We now have our sites linked to form a Skupper network, but no
services are exposed on it.

Skupper uses _listeners_ and _connectors_ to expose services
across sites inside a Skupper network.  A listener is a local
endpoint for client connections, configured with a routing key.  A
connector exists in a remote site and binds a routing key to a
particular set of servers.  Skupper routers forward client
connections from local listeners to remote connectors with
matching routing keys.

In West, use the `skupper listener create` command to create a
listener for the backend.  In East, use the `skupper connector
create` command to create a matching connector.

_**West:**_

~~~ shell
skupper listener create backend 9091
~~~

_Sample output:_

~~~ console
$ skupper listener create backend 9091
Waiting for create to complete...
Listener "backend" is ready
~~~

_**East:**_

~~~ shell
skupper connector create backend 9091
~~~

_Sample output:_

~~~ console
$ skupper connector create backend 9091
Waiting for create to complete...
Connector "backend" is ready
~~~

The commands shown above use the name argument, `backend`, to also
set the default routing key and pod selector.  You can use the
`--routing-key` and `--selector` options to set specific values.

<!-- You can also use `--workload` -- more convenient! -->

## Step 10: Expose the backend metrics service

The backend also exposes a metrics endpoint on port 9092.
Create a second listener/connector pair to expose the metrics service.

_**West:**_

~~~ shell
skupper listener create backend-metrics 9192 --routing-key backend-metrics
~~~

_Sample output:_

~~~ console
$ skupper listener create backend-metrics 9192 --routing-key backend-metrics
Waiting for create to complete...
Listener "backend-metrics" is ready
~~~

_**East:**_

~~~ shell
skupper connector create backend-metrics 9092 --routing-key backend-metrics --workload deployment/backend
~~~

_Sample output:_

~~~ console
$ skupper connector create backend-metrics 9092 --routing-key backend-metrics --workload deployment/backend
Waiting for create to complete...
Connector "backend-metrics" is ready
~~~

## Step 11: Access the frontend service

In order to use and test the application, we need external access
to the frontend.

Use `kubectl port-forward` to make the frontend available at
`localhost:9093`.

_**West:**_

~~~ shell
kubectl port-forward deployment/frontend 9094:9093
~~~

You can now access the web interface by navigating to
[http://localhost:9093](http://localhost:9093) in your browser.

The backend metrics are also accessible at [http://localhost:9192](http://localhost:9192).

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands:

_**West:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/frontend
~~~

_**East:**_

~~~ shell
skupper site delete --all
kubectl delete deployment/backend
~~~

## Summary

This example locates the frontend and backend services in different
namespaces, on different clusters.  Ordinarily, this means that they
have no way to communicate unless they are exposed to the public
internet.

Introducing Skupper into each namespace allows us to create a virtual
application network that can connect services in different clusters.
Any service exposed on the application network is represented as a
local service in all of the linked namespaces.

The backend service is located in `east`, but the frontend service
in `west` can "see" it as if it were local.  When the frontend
sends a request to the backend, Skupper forwards the request to the
namespace where the backend is running and routes the response back to
the frontend.

<img src="images/sequence.svg" width="640"/>

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
