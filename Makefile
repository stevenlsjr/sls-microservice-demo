.PHONY: keycloak-image install

keycloak-image:
	podman build -t stevenlsjr/keycloak:latest ./compose -f ./compose/keycloak.dockerfile

install:
	kubectl apply -f kubernetes/operators
	kubectl apply -k kubernetes/kind