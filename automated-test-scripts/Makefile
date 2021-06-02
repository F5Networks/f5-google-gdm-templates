#!make
current_dir := $(shell pwd)
# Create an environmental script and refernce it here (.gitignore set to ignore env.sh)
# example: export GOOGLE_PROJECT_ID=my_project_id
# option 1 all env variables refrenced in rules need be defined in env.sh
# option 2 have env vars set prior to running make rule
include env.sh
.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo " 'gce_standalone' using dewdrop docker image:stable, runs standalone test defined in env varable GCP_TEMPLATE_TEST_URL/GCP_TEMPLATE_TEST_PARMS"
	@echo " 'gce_failover_api' using dewdrop docker image:stable, runs standalone test defined in env varable GCP_TEMPLATE_TEST_URL_API/GCP_TEMPLATE_TEST_PARAMS_API"
	@echo " 'gce_failover_lb' using dewdrop docker image:stable, runs standalone test defined in env varable GCP_TEMPLATE_TEST_URL_LB/GCP_TEMPLATE_TEST_PARAMS_LB"

.PHONY: gce
env:
	env
# GCE V1
gce_standalone:
	docker run -it -v ${current_dir}:/automated-test-scripts -v ${current_dir}:/f5-google-gdm-templates -e SSH_KEY="${DEWPT_PRIVATE_KEY}" -e GOOGLE_PROJECT_ID="${GOOGLE_PROJECT_ID}" -e GOOGLE_PRIVATE_KEY_ID="${GOOGLE_PRIVATE_KEY_ID}" -e GOOGLE_CLIENT_EMAIL="${GOOGLE_CLIENT_EMAIL}" -e STACK_TYPE="${STACK_TYPE}" -e GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" -e GOOGLE_PRIVATE_KEY="${GOOGLE_PRIVATE_KEY}" -e TEMPLATE_URL="${GCP_TEMPLATE_TEST_URL}" -e TEMPLATE_PARAMETERS="${GCP_TEMPLATE_TEST_PARAMS}" artifactory.f5net.com/ecosystems-cloudsolutions-docker-dev/dewdrop:stable
gce_failover_api:
	docker run -it -v ${current_dir}:/automated-test-scripts -v ${current_dir}/../../f5-google-gdm-templates:/f5-google-gdm-templates -e SSH_KEY="${DEWPT_PRIVATE_KEY}" -e GOOGLE_PROJECT_ID="${GOOGLE_PROJECT_ID}" -e GOOGLE_PRIVATE_KEY_ID="${GOOGLE_PRIVATE_KEY_ID}" -e GOOGLE_CLIENT_EMAIL="${GOOGLE_CLIENT_EMAIL}" -e STACK_TYPE="${STACK_TYPE}" -e GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" -e GOOGLE_PRIVATE_KEY="${GOOGLE_PRIVATE_KEY}" -e TEMPLATE_URL="${GCP_TEMPLATE_TEST_URL_API}" -e TEMPLATE_PARAMETERS="${GCP_TEMPLATE_TEST_PARAMS_API}" artifactory.f5net.com/ecosystems-cloudsolutions-docker-dev/dewdrop:stable
gce_failover_lb:
	docker run -it -v ${current_dir}:/automated-test-scripts -v ${current_dir}/../../f5-google-gdm-templates:/f5-google-gdm-templates -e SSH_KEY="${DEWPT_PRIVATE_KEY}" -e GOOGLE_PROJECT_ID="${GOOGLE_PROJECT_ID}" -e GOOGLE_PRIVATE_KEY_ID="${GOOGLE_PRIVATE_KEY_ID}" -e GOOGLE_CLIENT_EMAIL="${GOOGLE_CLIENT_EMAIL}" -e STACK_TYPE="${STACK_TYPE}" -e GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" -e GOOGLE_PRIVATE_KEY="${GOOGLE_PRIVATE_KEY}" -e TEMPLATE_URL="${GCP_TEMPLATE_TEST_URL_LB}" -e TEMPLATE_PARAMETERS="${GCP_TEMPLATE_TEST_PARAMS_LB}" artifactory.f5net.com/ecosystems-cloudsolutions-docker-dev/dewdrop:stable
# GCE V2
gce_network:
	docker run -it -v ${current_dir}:/automated-test-scripts -v ${current_dir}/../../f5-google-gdm-templates-v2:/f5-google-gdm-templates-v2 -e SSH_KEY="${DEWPT_PRIVATE_KEY}" -e GOOGLE_PROJECT_ID="${GOOGLE_PROJECT_ID}" -e GOOGLE_PRIVATE_KEY_ID="${GOOGLE_PRIVATE_KEY_ID}" -e GOOGLE_CLIENT_EMAIL="${GOOGLE_CLIENT_EMAIL}" -e STACK_TYPE="${STACK_TYPE}" -e GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" -e GOOGLE_PRIVATE_KEY="${GOOGLE_PRIVATE_KEY}" -e TEMPLATE_URL="${GCP_TEMPLATE_TEST_URL_NETWORK}" -e TEMPLATE_PARAMETERS="${GCP_TEMPLATE_TEST_PARAMS_NETWORK}" artifactory.f5net.com/ecosystems-cloudsolutions-docker-dev/dewdrop:stable
gce_application_mod:
	docker run -it -v ${current_dir}:/automated-test-scripts -v ${current_dir}/../../f5-google-gdm-templates-v2:/f5-google-gdm-templates-v2 -e SSH_KEY="${DEWPT_PRIVATE_KEY}" -e GOOGLE_PROJECT_ID="${GOOGLE_PROJECT_ID}" -e GOOGLE_PRIVATE_KEY_ID="${GOOGLE_PRIVATE_KEY_ID}" -e GOOGLE_CLIENT_EMAIL="${GOOGLE_CLIENT_EMAIL}" -e STACK_TYPE="${STACK_TYPE}" -e GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" -e GOOGLE_PRIVATE_KEY="${GOOGLE_PRIVATE_KEY}" -e TEMPLATE_URL="${GCP_TEMPLATE_TEST_URL_APPLICATION_MOD}" -e TEMPLATE_PARAMETERS="${GCP_TEMPLATE_TEST_PARAMS_APPLICATION_MOD}" artifactory.f5net.com/ecosystems-cloudsolutions-docker-dev/dewdrop:stable


