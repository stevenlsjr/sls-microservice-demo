ROOTDIR=$(realpath $(dirname $0))

APICURIO_NAMESPACE=apicurio-registry
APICURIO_VERSION=3.2.6
curl -sSL "https://raw.githubusercontent.com/Apicurio/apicurio-registry/$APICURIO_VERSION/operator/install/install.yaml" | sed "s/PLACEHOLDER_NAMESPACE/$APICURIO_NAMESPACE/g" > $ROOTDIR/operators/03-apicurio.yaml