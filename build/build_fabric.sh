#!/bin/bash 

export VERSION=1.4.0
# if ca version not passed in, default to latest released version
export CA_VERSION=$VERSION
# current version of thirdparty images (couchdb, kafka and zookeeper) released
export THIRDPARTY_IMAGE_VERSION=0.4.14
export ARCH=$(echo "$(uname -s|tr '[:upper:]' '[:lower:]'|sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')")
export MARCH=$(uname -m)

CA_TAG="${CA_VERSION}"
FABRIC_TAG="${VERSION}"

requirementsFabric() {

  echo "========================================================="
  echo "Installind Go"
  echo "========================================================="

  sudo apt install -y golang-go

  mkdir $HOME/go
  mkdir $HOME/go/bin
  mkdir $HOME/go/src
  mkdir $HOME/go/pkg

  sudo echo 'export GOPATH=$HOME/go' >> ~/.profile
  sudo echo 'export GOBIN=$HOME/go/bin' >> ~/.profile
  sudo echo 'export PATH=$PATH:/usr/local/go/bin:$GOBIN' >> ~/.profile

  source ~/.profile

  echo "========================================================="
  echo "Installind Fabric Python SDK"
  echo "========================================================="

  mkdir git
  git clone https://github.com/hyperledger/fabric-sdk-py git/fabric-sdk-py
  cd git/fabric-sdk-py
  git checkout 5949c1d # version from umbra VM
  sudo python3.7 setup.py install
  cd - 
}

dockerFabricPull() {
  local FABRIC_TAG=$1
#   for IMAGES in peer orderer ccenv tools; do
  for IMAGES in peer orderer; do
      echo "==> FABRIC IMAGE: $IMAGES"
      echo
      docker pull hyperledger/fabric-$IMAGES:$FABRIC_TAG
      docker tag hyperledger/fabric-$IMAGES:$FABRIC_TAG hyperledger/fabric-$IMAGES
  done
}

dockerThirdPartyImagesPull() {
  local THIRDPARTY_TAG=$1
  for IMAGES in couchdb kafka zookeeper; do
      echo "==> THIRDPARTY DOCKER IMAGE: $IMAGES"
      echo
      docker pull hyperledger/fabric-$IMAGES:$THIRDPARTY_TAG
      docker tag hyperledger/fabric-$IMAGES:$THIRDPARTY_TAG hyperledger/fabric-$IMAGES
  done
}

dockerCaPull() {
      local CA_TAG=$1
      echo "==> FABRIC CA IMAGE"
      echo
      docker pull hyperledger/fabric-ca:$CA_TAG
      docker tag hyperledger/fabric-ca:$CA_TAG hyperledger/fabric-ca
}

dockerImages() {
  which docker >& /dev/null
  NODOCKER=$?
  if [ "${NODOCKER}" == 0 ]; then
	  echo "========================================================="
      echo "===> Pulling fabric Images"
      echo "========================================================="
	  dockerFabricPull ${FABRIC_TAG}
	  echo "===> Pulling fabric ca Image"
	  dockerCaPull ${CA_TAG}
	#   echo "===> Pulling thirdparty docker images"
	#   dockerThirdPartyImagesPull ${THIRDPARTY_TAG}
	  echo
	  echo "===> List out hyperledger docker images"
	  docker images | grep hyperledger*
  else
    echo "========================================================="
    echo "Docker not installed, bypassing download of Fabric images"
    echo "========================================================="
  fi
}


upgradeDockerImages() {
  local TAG=$1
  which docker >& /dev/null
  NODOCKER=$?
  if [ "${NODOCKER}" == 0 ]; then
    for IMAGES in peer; do
        echo "========================================================="
        echo "==> Upgrading FABRIC IMAGE: $IMAGES:$TAG"
        echo "========================================================="
        echo
        docker run -d --name $IMAGES hyperledger/fabric-$IMAGES:$TAG
        docker exec $IMAGES bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping iperf3 && apt clean'  
        docker commit $IMAGES hyperledger/fabric-$IMAGES:$TAG.1
        echo "-- Committed docker image: hyperledger/fabric-$IMAGES:$TAG.1 --"
        docker stop -t0 $IMAGES
        docker rm $IMAGES 
      done

    echo "========================================================="
    echo "==> Upgrading FABRIC IMAGE: fabric-orderer:$TAG"
    echo "========================================================="
    echo
    docker run -d --name fabric-orderer hyperledger/fabric-orderer:$TAG
    docker exec fabric-orderer bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping iperf3 && apt clean && rm -R /var/hyperledger/*'
    docker commit fabric-orderer hyperledger/fabric-orderer:$TAG.1
    echo "-- Committed docker image: hyperledger/fabric-orderer:$TAG.1 --"
    docker stop -t0 fabric-orderer
    docker rm fabric-orderer


    echo "========================================================="
    echo "==> Upgrading FABRIC IMAGE: fabric-ca:$TAG"
    echo "========================================================="
    echo
    docker run -d --name fabric-ca hyperledger/fabric-ca:$TAG
    docker exec fabric-ca bash -c 'apt update && apt install -y net-tools iproute2 inetutils-ping iperf3 && apt clean'
    docker commit fabric-ca hyperledger/fabric-ca:$TAG.1
    echo "-- Committed docker image: hyperledger/fabric-ca:$TAG.1 --"
    docker stop -t0 fabric-ca
    docker rm fabric-ca

  else
    echo "========================================================="
    echo "Docker not installed, bypassing Upgrade of Fabric images"
    echo "========================================================="
  fi
}

requirementsFabric
dockerImages
upgradeDockerImages ${FABRIC_TAG}

echo "========================================================="
echo "Adds configtxgen and cryptogen to PATH env"
echo "========================================================="

mkdir -p $HOME/hl/bin
cp ../umbra/design/fabric/bin/* $HOME/hl/bin/
sudo echo 'export PATH=$PATH:$HOME/hl/bin' >> ~/.profile
source ~/.profile

mkdir -p ../examples/fabric/fabric_configs
chmod -R 775 ../examples/fabric/fabric_configs
