Overview
========


Deploy Your Project Locally
===========================

1. Start Airflow on your local machine by running 'astro dev start'.

This command will spin up 4 Docker containers on your machine, each for a different Airflow component:

- Postgres: Airflow's Metadata Database
- Webserver: The Airflow component responsible for rendering the Airflow UI
- Scheduler: The Airflow component responsible for monitoring and triggering tasks
- Triggerer: The Airflow component responsible for triggering deferred tasks

2. Verify that all 4 Docker containers were created by running 'docker ps'.

Note: Running 'astro dev start' will start your project with the Airflow Webserver exposed at port 8080 and Postgres exposed at port 5432. If you already have either of those ports allocated, you can either stop your existing Docker containers or change the port.

3. Access the Airflow UI for your local Airflow project. To do so, go to http://localhost:8080/ and log in with 'admin' for both your Username and Password.

You should also be able to access your Postgres Database at 'localhost:5432/postgres'.



## Local Kubernetes Setup
Use K8s via Docker Desktop as described here:
https://docs.astronomer.io/learn/kubepod-operator. Change the cluster's server to: `server: https://kubernetes.docker.internal:6443`

To test the image hosted in our private github image repository follow this guide to set up the needed github credential:
https://docs.astronomer.io/astro/kubernetespodoperator#run-images-from-a-private-registry


## Debug Kubernetes
Open shell on temporary pod to test network
```bash
kubectl run -i --tty --rm debug --image=busybox --restart=Never -- sh
```

initiate DNS lookup:
```bash
nslookup gn92733.eu-central-1.snowflakecomputing.com
```

Inspect log:
```bash
kubectl logs --namespace=kube-system -l k8s-app=kube-dns
```

DNS on Docker Desktop > 2.24.2 seems to be unreliable for the internet. See [issue](https://github.com/docker/for-win/issues/13768). But, you can run the latest Docker desktop and patch `coredns` like this:
```bash
kubectl patch deployment coredns -n kube-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"coredns","image":"registry.k8s.io/coredns/coredns:v1.10.0"}]}}}}'
```
