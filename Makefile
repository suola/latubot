
REGION="europe-west3"
FUNCTIONS = load_updates_http load_updates_pubsub notify_http notify_pubsub
DEPLOY_CMD = gcloud functions deploy
DEPLOY_ARGS = --runtime python38 --region ${REGION}

deploy-load:
	${DEPLOY_CMD} load_updates_http ${DEPLOY_ARGS} --trigger-http --allow-unauthenticated
	${DEPLOY_CMD} load_updates_pubsub ${DEPLOY_ARGS} --trigger-topic cron-topic

deploy-notify:
	${DEPLOY_CMD} notify_http ${DEPLOY_ARGS} --trigger-http --allow-unauthenticated
	${DEPLOY_CMD} notify_pubsub ${DEPLOY_ARGS} --trigger-topic notify-topic

deploy: deploy-load deploy-notify

.PHONY: deploy-load deploy-notify deploy
