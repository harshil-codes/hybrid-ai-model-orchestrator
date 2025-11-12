import requests
import json

url = "https://interest-rate-loan-rate-model.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/v2/models/interest-rate/infer"
payload = {
    "inputs": [{
        "name": "input:0",
        "shape": [1, 5],
        "datatype": "FP32",
        "data": [650, 250000, 150000, 60, 0.04]
    }]
}

response = requests.post(url, json=payload, verify=False)
print(json.dumps(response.json(), indent=2))
