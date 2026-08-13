<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Hello World using cluster policy

[![main](https://github.com/pwright/sketcher/actions/workflows/main.yaml/badge.svg)](https://github.com/pwright/sketcher/actions/workflows/main.yaml)

#### Use policy to control site linking and service exposure

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
* [Step 3: Enable Skupper cluster policy](#step-3-enable-skupper-cluster-policy)
* [Step 4: Deploy the frontend and backend](#step-4-deploy-the-frontend-and-backend)
* [Step 5: Create your sites](#step-5-create-your-sites)
* [Step 6: Attempt to link your sites and expose the backend](#step-6-attempt-to-link-your-sites-and-expose-the-backend)
* [Step 7: Grant permission to link your sites and expose the backend](#step-7-grant-permission-to-link-your-sites-and-expose-the-backend)
* [Step 8: Link your sites and expose the backend](#step-8-link-your-sites-and-expose-the-backend)
* [Step 9: Access the frontend service](#step-9-access-the-frontend-service)
* [Cleaning up](#cleaning-up)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a variant of [Skupper Hello World][hello-world] that
uses [Skupper cluster policy][policy] to restrict site linking and
service exposure.

It contains two services:

* A backend service that exposes an `/api/hello` endpoint.  It
  returns greetings of the form `Hi, <your-name>.  I am <my-name>
  (<pod-name>)`.

* A frontend service that sends greetings to the backend and
  fetches new greetings in response.

The frontend and backend run in different sites, on different
clusters.  The example shows you how you can explicitly allow
linking of the two sites and exposure of the backend service.

[hello-world]: https://github.com/skupperproject/skupper-example-hello-world
[policy]: https://skupper.io/docs/policy/index.html

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

## Step 3: Enable Skupper cluster policy

To enable Skupper cluster policy, you install a Custom Resource
Definition (CRD) named `SkupperClusterPolicy`.  Installing the
CRD requires cluster admin privileges.

The presence of the CRD in a cluster tells Skupper to enforce
cluster policy.  The default policy (an "empty" policy with
nothing explicitly allowed) denies all site linking and service
exposure.

_**Warning:**_ Once the CRD is installed, any existing Skupper
sites on the cluster will stop working because Skupper cluster
policy denies all operations not explicitly allowed in the
policy configuration.  Be careful to define working policy rules
before you enable policy for existing sites.

Use `kubectl apply` to install the CRD in each cluster.

_**West:**_

~~~ shell
kubectl apply -f https://raw.githubusercontent.com/skupperproject/skupper/main/api/types/crds/skupper_cluster_policy_crd.yaml
~~~

_Sample output:_

~~~ console
$ kubectl apply -f https://raw.githubusercontent.com/skupperproject/skupper/main/api/types/crds/skupper_cluster_policy_crd.yaml
customresourcedefinition.apiextensions.k8s.io/skupperclusterpolicies.skupper.io created
clusterrole.rbac.authorization.k8s.io/skupper-service-controller created
~~~

_**East:**_

~~~ shell
kubectl apply -f https://raw.githubusercontent.com/skupperproject/skupper/main/api/types/crds/skupper_cluster_policy_crd.yaml
~~~

_Sample output:_

~~~ console
$ kubectl apply -f https://raw.githubusercontent.com/skupperproject/skupper/main/api/types/crds/skupper_cluster_policy_crd.yaml
customresourcedefinition.apiextensions.k8s.io/skupperclusterpolicies.skupper.io created
clusterrole.rbac.authorization.k8s.io/skupper-service-controller created
~~~

## Step 4: Deploy the frontend and backend

Deploy the Hello World components, placing the frontend on one
cluster and the backend on the other.

Use `kubectl create deployment` to deploy the frontend in West
and the backend in East.

_**West:**_

~~~ shell
kubectl create deployment frontend --image quay.io/skupper/hello-world-frontend
~~~

_**East:**_

~~~ shell
kubectl create deployment backend --image quay.io/skupper/hello-world-backend --replicas 3
~~~

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
skupper init
skupper status
~~~

_Sample output:_

~~~ console
$ skupper init
Waiting for LoadBalancer IP or hostname...
Waiting for status...
Skupper is now installed in namespace 'west'.  Use 'skupper status' to get more information.

$ skupper status
Skupper is enabled for namespace west" (with policies). It is not connected to any other sites. It has no exposed services.
~~~

_**East:**_

~~~ shell
skupper init
skupper status
~~~

_Sample output:_

~~~ console
$ skupper init
Waiting for LoadBalancer IP or hostname...
Waiting for status...
Skupper is now installed in namespace 'east'.  Use 'skupper status' to get more information.

$ skupper status
Skupper is enabled for namespace "east" (with policies). It is not connected to any other sites. It has no exposed services.
~~~

Note that the status output shows the sites enabled "with
policies".

## Step 6: Attempt to link your sites and expose the backend

Let's first try to link our sites and expose the backend service
without permission.

Use `skupper token create` in West to generate the token.  This
is the first step in attempting to link the two sites.

Use `skupper expose` to attempt to expose the backend service in
East.

_**West:**_

~~~ shell
skupper token create ~/secret.token
~~~

_Sample output:_

~~~ console
$ skupper token create ~/secret.token
Error: Failed to create token: Policy validation error: incoming links are not allowed
~~~

_**East:**_

~~~ shell
skupper expose deployment/backend --port 8080
~~~

_Sample output:_

~~~ console
$ skupper expose deployment/backend --port 8080
Error: Policy validation error: deployment/backend cannot be exposed
~~~

Because Skupper cluster policy is enabled, these operations are
denied.

## Step 7: Grant permission to link your sites and expose the backend

With policy enabled, we need to explicitly allow the site link
and service exposure required by the Hello World application.

To enable linking from East to West, use `allowIncomingLinks:
true` in West and `allowOutgoingLinksHostnames: ["*"]` in East.

This example uses an asterisk in the list of allowed outgoing
hostnames, which allows any hostname.  You can also specify a
narrow range of hostnames using regular expressions.

To enable exposure of the backend, use `allowedServices:
[backend]` in West.  Then, in East, use `allowedServices:
[backend]` and `allowedExposedResources: [deployment/backend]`.

See [Skupper cluster policy][policy] for more information about
policy configuration.

#### Policy in West

[west/policy.yaml](west/policy.yaml):

~~~ yaml
apiVersion: skupper.io/v1alpha1
kind: SkupperClusterPolicy
metadata:
  name: west
spec:
  namespaces: [west]
  allowIncomingLinks: true
  allowedServices: [backend]
~~~

#### Policy in East

[east/policy.yaml](east/policy.yaml):

~~~ yaml
apiVersion: skupper.io/v1alpha1
kind: SkupperClusterPolicy
metadata:
  name: east
spec:
  namespaces: [east]
  allowedOutgoingLinksHostnames: ["*"]
  allowedExposedResources: [deployment/backend]
  allowedServices: [backend]
~~~

Use the `kubectl apply` command with the policy resources for
each site.

_**West:**_

~~~ shell
kubectl apply -f west/policy.yaml
~~~

_**East:**_

~~~ shell
kubectl apply -f east/policy.yaml
~~~

## Step 8: Link your sites and expose the backend

Now that we have permission granted, let's try again.

Use `skupper token create` in West to generate the token.  Then,
use `skupper link create` in East to link the sites.

Use `skupper expose` to expose the backend service in East to
the frontend in West.

_**West:**_

~~~ shell
skupper token create ~/secret.token
~~~

_Sample output:_

~~~ console
$ skupper token create ~/secret.token
Token written to ~/secret.token
~~~

_**East:**_

~~~ shell
skupper link create ~/secret.token
skupper expose deployment/backend --port 8080
~~~

_Sample output:_

~~~ console
$ skupper link create ~/secret.token
Site configured to link to <endpoint> (name=link1)
Check the status of the link using 'skupper link status'.

$ skupper expose deployment/backend --port 8080
deployment backend exposed as backend
~~~

## Step 9: Access the frontend service

In order to use and test the application, we need external access
to the frontend.

Use `kubectl port-forward` to make the frontend available at
`localhost:8080`.

_**West:**_

~~~ shell
kubectl port-forward deployment/frontend 8080:8080
~~~

You can now access the web interface by navigating to
[http://localhost:8080](http://localhost:8080) in your browser.

## Cleaning up

To remove Skupper and the other resources from this exercise, use
the following commands:

_**West:**_

~~~ shell
skupper delete
kubectl delete service/frontend
kubectl delete deployment/frontend
kubectl delete -f west/policy.yaml
~~~

_**East:**_

~~~ shell
skupper delete
kubectl delete deployment/backend
kubectl delete -f east/policy.yaml
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
