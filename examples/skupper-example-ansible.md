<!-- NOTE: This file is generated from skewer.yaml.  Do not edit it directly. -->

# Skupper Hello World using Ansible

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
* [Step 1: Install the Skupper Ansible collection](#step-1-install-the-skupper-ansible-collection)
* [Step 2: Access your Kubernetes clusters](#step-2-access-your-kubernetes-clusters)
* [Step 3: Install Skupper on your Kubernetes clusters](#step-3-install-skupper-on-your-kubernetes-clusters)
* [Step 4: Set up your clusters](#step-4-set-up-your-clusters)
* [Step 5: Inspect the inventory file](#step-5-inspect-the-inventory-file)
* [Step 6: Run the setup playbook](#step-6-run-the-setup-playbook)
* [Step 7: Access the frontend service](#step-7-access-the-frontend-service)
* [Step 8: Run the teardown playbook](#step-8-run-the-teardown-playbook)
* [Next steps](#next-steps)
* [About this example](#about-this-example)

## Overview

This example is a variant of [Skupper Hello World][hello-world] that
is deployed using the [Skupper Ansible collection][skupper-ansible].

It contains two services:

* A backend service that exposes an `/api/hello` endpoint.  It
  returns greetings of the form `Hi, <your-name>.  I am <my-name>
  (<pod-name>)`.

* A frontend service that sends greetings to the backend and
  fetches new greetings in response.

In this scenario, each service runs in a different Kubernetes
cluster.  The frontend runs in a namespace on cluster 1 called West,
and the backend runs in a namespace on cluster 2 called East.

<img src="images/entities.svg" width="640"/>

Skupper enables you to place the backend in one cluster and the
frontend in another and maintain connectivity between the two
services without exposing the backend to the public internet.

The [Skupper Ansible collection][skupper-ansible] is used in this example
to connect two sites running on Kubernetes, but the collection can also be
used to manage the lifecycle of sites running on Podman, Docker or Linux.

[hello-world]: https://github.com/skupperproject/skupper-example-hello-world/tree/v2/
[skupper-ansible]: https://galaxy.ansible.com/ui/repo/published/skupper/v2/

## Prerequisites

* Access to at least one Kubernetes cluster, from [any provider you
  choose][kube-providers].

* The `kubectl` command-line tool, version 1.15 or later
  ([installation guide][install-kubectl]).

[kube-providers]: https://skupper.io/start/kubernetes.html
[install-kubectl]: https://kubernetes.io/docs/tasks/tools/install-kubectl/
* Ansible, version 2.15 or later ([installation guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html))

## Sites

This example uses the following sites:

_**Terminal:**_

~~~ shell
export KUBECONFIG=~/.kube/config-west
kubectl config set-context --current --namespace west
~~~

_**East:**_

~~~ shell
export KUBECONFIG=~/.kube/config-east
kubectl config set-context --current --namespace east
~~~

## Step 1: Install the Skupper Ansible collection

Use the `ansible-galaxy` command to install the
`skupper.v2` collection.

_**Terminal:**_

~~~ shell
ansible-galaxy collection install skupper.v2
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

_**Terminal:**_

~~~ shell
export KUBECONFIG=$PWD/ansible/kubeconfigs/west
<provider-specific login command>
~~~

_**East:**_

~~~ shell
export KUBECONFIG=$PWD/ansible/kubeconfigs/east
<provider-specific login command>
~~~

**Note:** The login procedure varies by provider.

## Step 3: Install Skupper on your Kubernetes clusters

Using Skupper on Kubernetes requires the installation of the
Skupper custom resource definitions (CRDs) and the Skupper
controller.

For each cluster, use `kubectl apply` with the Skupper
installation YAML to install the CRDs and controller.

_**Terminal:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

_**East:**_

~~~ shell
kubectl apply -f https://skupper.io/v2/install.yaml
~~~

## Step 4: Set up your clusters

This example uses two clusters.  The clusters are accessed using
two kubeconfig files:

~~~
<project-dir>/ansible/kubeconfigs/east
<project-dir>/ansible/kubeconfigs/west
~~~

For each kubeconfig, set the `KUBECONFIG` environment variable
to the file path and run the login command for your cluster.
This updates the kubeconfig with the required credentials.

**Note:** The cluster login procedure varies by provider.  See
the documentation for yours:

* [Minikube](https://skupper.io/start/minikube.html#cluster-access)
* [Amazon Elastic Kubernetes Service (EKS)](https://skupper.io/start/eks.html#cluster-access)
* [Azure Kubernetes Service (AKS)](https://skupper.io/start/aks.html#cluster-access)
* [Google Kubernetes Engine (GKE)](https://skupper.io/start/gke.html#cluster-access)
* [IBM Kubernetes Service](https://skupper.io/start/ibmks.html#cluster-access)
* [OpenShift](https://skupper.io/start/openshift.html#cluster-access)

_**Terminal:**_

~~~ shell
cd <project-dir>
export KUBECONFIG=$PWD/ansible/kubeconfigs/west
# Enter your provider-specific login command for cluster 1
export KUBECONFIG=$PWD/ansible/kubeconfigs/east
# Enter your provider-specific login command for cluster 2
~~~

## Step 5: Inspect the inventory file

Before we start running commands, let's examine the inventory
file.  Although it is not mandatory to have an inventory file, you can have
the kubeconfig file, the namespace and the path to the resources defined per
inventory host.

[ansible/inventory.yml](ansible/inventory.yml):

~~~ yaml
all:
  vars:
    ansible_connection: local
  hosts:
    west:
      kubeconfig: "{{ inventory_dir }}/kubeconfigs/west"
      namespace: west
      resources_path: "{{ playbook_dir }}/kubernetes/west.yaml"
    east:
      kubeconfig: "{{ inventory_dir }}/kubeconfigs/east"
      namespace: east
      resources_path: "{{ playbook_dir }}/kubernetes/east.yaml"
~~~

The playbooks that follow use this inventory data to set up and
tear down the Skupper network.

For more information about inventory files, see the [Ansible
inventory guide][ansible-inventory].

[ansible-inventory]: https://docs.ansible.com/ansible/latest/inventory_guide/index.html

## Step 6: Run the setup playbook

Now let's look at the setup playbook.

[ansible/setup.yml](ansible/setup.yml):

~~~ yaml
- hosts: all
  connection: local
  tasks:
    - name: Apply site resources
      skupper.v2.resource:
        path: "{{ resources_path }}"
        kubeconfig: "{{ kubeconfig }}"
        namespace: "{{ namespace }}"

- hosts: west
  connection: local
  tasks:
    - name: Create a token to the west site
      skupper.v2.token:
        name: "west"
        kubeconfig: "{{ kubeconfig }}"
        namespace: "{{ namespace }}"
      register: accesstoken

- hosts: east
  connection: local
  tasks:
    - name: Link east site to west
      skupper.v2.resource:
        def: "{{ hostvars['west']['accesstoken']['token'] }}"
        kubeconfig: "{{ kubeconfig }}"
        namespace: "{{ namespace }}"
~~~

The first task applies all needed resources on both west and east namespaces.
Those resources contain the whole example definition, including: the workloads (backend and frontend apps)
along with all the Skupper V2 resources needed.
We apply those resources using the `skupper.v2.resource` module, see the
[Resource module documentation][resource-doc].

The second task is performed against the west inventory host only and it generates
an AccessGrant named `west`, returning its respective AccessToken, which is registered
to the host variable `accesstoken`. This task uses the `skupper.v2.token` module for that, see
the [Token module documentation][token-doc].

The last task is to link the east site to the west, using the `skupper.v2.resource` module again,
and applying the AccessToken registered into the west host variables as `accesstoken.token`.

Use the `ansible-playbook` command to run the playbook:

[resource-doc]: https://galaxy.ansible.com/ui/repo/published/skupper/v2/content/module/resource/
[token-doc]: https://galaxy.ansible.com/ui/repo/published/skupper/v2/content/module/token/

_**Terminal:**_

~~~ shell
ansible-playbook -i ansible/inventory.yml ansible/setup.yml
~~~

_Sample output:_

~~~ console
$ ansible-playbook -i ansible/inventory.yml ansible/setup.yml
[...]
PLAY RECAP *********************************************************************************************
east             : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
west             : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
~~~

**Note:** The collection also requires some Python modules to be present
on the target node, in case you have problems, you will need to install
the [collection requirements][collection-requirements], in example:

~~~
pip install -r https://raw.githubusercontent.com/skupperproject/skupper-ansible/refs/heads/main/requirements.txt
~~~

[collection-requirements]: https://raw.githubusercontent.com/skupperproject/skupper-ansible/refs/heads/main/requirements.txt

## Step 7: Access the frontend service

In order to use and test the application, we need external access
to the frontend.

Use `kubectl port-forward` to make the frontend available at
`localhost:8080`.

_**Terminal:**_

~~~ shell
export KUBECONFIG=$PWD/ansible/kubeconfigs/west
kubectl -n west port-forward deployment/frontend 8080:8080
~~~

You can now access the web interface by navigating to
[http://localhost:8080](http://localhost:8080) in your browser.

## Step 8: Run the teardown playbook

To clean everything up, run the teardown playbook.

[ansible/teardown.yml](ansible/teardown.yml):

~~~ yaml
- hosts: all
  connection: local
  tasks:
    - name: Delete site resources
      skupper.v2.resource:
        state: absent
        path: "{{ resources_path }}"
        kubeconfig: "{{ kubeconfig }}"
        namespace: "{{ namespace }}"
~~~

The `skupper.v2.resource` modules from the `skupper.v2` collection
is called for both west and east resources using action `absent`, which
removes the definitions provided through the YAML files.

_**Terminal:**_

~~~ shell
ansible-playbook -i ansible/inventory.yml ansible/teardown.yml
~~~

_Sample output:_

~~~ console
$ ansible-playbook -i ansible/inventory.yml ansible/teardown.yml
[...]

PLAY RECAP *********************************************************************************************
east             : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
west             : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
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
