KIND_CONTEXT_NAME:=kind-kind

.PHONY: keycloak-image install kube-context \
	dashboard  \
	load-images \
	kind-cloud-provider

kube-context:
	kubectx $(KIND_CONTEXT_NAME)

keycloak-image:
	podman build -t stevenlsjr/keycloak:dev ./compose -f ./compose/keycloak.dockerfile

load-images: keycloak-image
	kind load docker-image \
		stevenlsjr/keycloak:dev

# enabled load balancer for kind. must run in `sudo`
cloud-provider-kind:
	cloud-provider-kind --gateway-channel standard

dashboard:
	kubectl --context kind-kind apply \
	 -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml


install: kube-context
	kubectx kind-kind
	kubectl --context kind-kind apply -f kubernetes/operators
	kubectl --context kind-kind apply -k kubernetes/kind