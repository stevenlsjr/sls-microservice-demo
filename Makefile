KIND_CONTEXT_NAME:=kind-kind

.PHONY: keycloak-image install kube-context

kube-context:
	kubectx $(KIND_CONTEXT_NAME)

keycloak-image:
	podman build -t stevenlsjr/keycloak:latest ./compose -f ./compose/keycloak.dockerfile

install: kube-context
	kubectl apply -f kubernetes/operators
	kubectl apply -k kubernetes/kind