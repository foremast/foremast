#!/bin/bash
IMAGE='gcr.io/spinnaker-marketplace/halyard:stable'

# Let's do some sanity checking before we proceed.
if [[ -z ${KUBECONFIG} ]]; then
    echo '$KUBECONFIG environment variable is not defined.'
    exit 1
fi

docker pull "${IMAGE}"

docker run --detach \
    --name halyard --rm \
    -v "${PWD}/hal:/home/spinnaker/.hal" \
    -v "${KUBECONFIG}:/home/spinnaker/.kube/config" \
    -it \
    "${IMAGE}"

docker exec -it halyard bash
