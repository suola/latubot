
REGION="europe-west3"

deploy:
	gcloud functions deploy load_updates_http --entry-point load_updates_http --runtime python38 --trigger-http --allow-unauthenticated --region ${REGION}
