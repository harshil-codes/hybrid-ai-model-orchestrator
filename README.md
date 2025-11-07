* Request GCP Blank Environment on RHDP
* Follow the steps here to install a Cluster on GCP (https://docs.redhat.com/en/documentation/openshift_container_platform/4.10/html/installing/installing-on-gcp)
* Enable API's for artifactory, pub/sub, bigquery  
* Give the right service accounts correct privileges, for the demo set to admin  
* Build the app image and push to artifactory. App is here(loan-data-app)
* Create a pub/sub topic in GCP
* Test the app locally and publish messages to pub/sub   
* Create project, create GCP service account secret 
* Deploy the app on OCP and verify messages are being pushed to pub/sub topic
* Create Dataset and table Schema in BigQuery
* Create A Subscription to write from Pub Sub to bigquery (gcloud-manifests)
* Verify table in BigQuery (gcloud-manifests/loan_data_table)
* Create a table to have a synthetic column for loan\_approval\_status, this is the column where trainig will be done on
* Query for creating table is here(gcloud-manifests/bq_training_data.sql)
* Create a Tablular type dataset in Vertex AI, Configure the dataset location as the bq table created above  
* Using Vertex AI AutoML train the model on this dataset, Model training target column is loan\_approval\_status.  
* After Model training is done, Deploy the model to an Endpoint in vertex AI
* Create a Sample Request and query the model (gcloud-manifests/query.txt)

OpenShift

* Install OCP AI from Operatorhub, create Data Science Cluster  
* Install OCP Service mesh operator  
* Install OCP Serverless Operator  
* Create Workbench, train the model  
* Deploy the model and Serve using OpenShift AI  
* Deploy the backend app to consume both the models  
* Deploy frontend app to connect to the backend

