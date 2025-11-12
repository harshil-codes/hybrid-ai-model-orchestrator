## Hybrid AI Model Orchestration

This project demonstrates an end-to-end hybrid AI architecture combining Google Vertex AI and OpenShift AI to automate loan decisioning. The frontend collects applicant data and sends it to a backend (FastAPI on OpenShift), which first queries a Vertex AI model for loan approval prediction and confidence scoring. If approved, it then calls an OpenShift AI ONNX model to determine the personalized interest rate. The system integrates seamlessly with a conversational Llama-based chatbot running on Red Hat AI Inference Server to provide applicants personalized financial guidance and loan insights. 

## Steps to Recreate the environment

* Request GCP Blank Environment on RHDP
* [Follow the steps here to install a Cluster on GCP](https://docs.redhat.com/en/documentation/openshift_container_platform/4.10/html/installing/installing-on-gcp)
* Enable Google Cloud API's for artifactory, pub/sub, bigquery  
* Give the right service accounts correct privileges, for the demo set to admin
* Login to Google Cloud via CLI
``` gcloud auth login ``` 
* Build the [App](loan-data-app) publishing historical loan data and push to artifactory
```
podman build --platform linux/amd64 -t us-docker.pkg.dev/openenv-7mhsq/asa-demo/loan-app:v1 .
podman push us-docker.pkg.dev/openenv-7mhsq/asa-demo/loan-app:v1
```
* [Create a pub/sub topic in GCP](gcloud-manifests/pubsub_topics.json)
* Test the app locally and publish messages to pub/sub   
* Create GCP service account secret 
* Deploy the app on OCP and verify messages are being pushed to pub/sub topic
``` oc apply -f loan-data-app/k8s-manifests/. ```
* [Create Dataset and table Schema in BigQuery](gcloud-manifests/bq_schema.json)
* [Create A Subscription to write from Pub Sub to bigquery](gcloud-manifests/pubsub_subscriptions.json)
* [Verify table in BigQuery](gcloud-manifests/bq_table.txt)
* Create a table to have a synthetic column for loan\_approval\_status, this is the column where trainig will be done on
* Query for creating table is [here](gcloud-manifests/bq_training_data_table.sql)
* [Verify the new table in BigQuery](gcloud-manifests/bq_table_trained.txt)
* Create a Tablular type dataset in Vertex AI, Configure the dataset location as the bq table created above  
* Using Vertex AI AutoML train the model on this dataset, Model training target column is loan\_approval\_status.  
* After Model training is done, Deploy the model to an Endpoint in vertex AI
* Modify the query script [here](gcloud-manifests/query.sh) and run the script

OpenShift

* Install OCP AI from Operatorhub, create Data Science Cluster  
* Install OCP Service mesh operator  
* Install OCP Serverless Operator  
* Create Workbench, train the model  
* Deploy the model and Serve using OpenShift AI  
* Deploy the backend app to consume both the models  
* Deploy frontend app to connect to the backend

