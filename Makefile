
REGION="europe-west3"
FUNCTIONS = load_updates_http notify_http
DEPLOY_CMD = gcloud functions deploy
DEPLOY_ARGS = --runtime python38 --region ${REGION}

deploy-load:
	${DEPLOY_CMD} load_updates_http ${DEPLOY_ARGS} --trigger-http --allow-unauthenticated

deploy-notify:
	${DEPLOY_CMD} notify_http ${DEPLOY_ARGS} --trigger-http --allow-unauthenticated

deploy: deploy-load deploy-notify

.PHONY: deploy-load deploy-notify deploy
