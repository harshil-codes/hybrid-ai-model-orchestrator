# main.py
import json
import time
import uuid
import random
import os
from datetime import datetime, timedelta, timezone

# Pub/Sub client
from google.cloud import pubsub_v1

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "<YOUR_GCP_PROJECT>")
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "loan-events")
PUBLISH_INTERVAL_SECONDS = int(os.environ.get("PUBLISH_INTERVAL_SECONDS", "3"))
NUM_ENTITIES = int(os.environ.get("NUM_ENTITIES", "1450"))  # 400-500 entities

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def gen_uuid():
    return str(uuid.uuid4())


def generate_entities(num_entities=450):
    """Generate a mix of business and individual borrowers"""
    entities = []
    
    # Split 60% individual, 40% business
    num_individuals = int(num_entities * 0.6)
    num_businesses = num_entities - num_individuals
    
    # Generate individual entities
    for i in range(num_individuals):
        entity_id = f"IND-{2000 + i}"
        entities.append({
            "entity_id": entity_id,
            "entity_type": "individual",
            "credit_score": random.randint(580, 800),
            "annual_income": float(random.randint(30000, 200000)),
            "employment_status": random.choice(["salaried", "contractor", "self-employed"]),
            "region": random.choice(["us-east1", "us-west1", "us-central1", "europe-west1"]),
            "loan_id": f"LN-IND-{2000 + i}",
            "requested_amount": float(random.randint(5000, 80000)),
            "tenor": random.choice([12, 24, 36, 48, 60])
        })
    
    # Generate business entities
    for i in range(num_businesses):
        entity_id = f"BUS-{1000 + i}"
        entities.append({
            "entity_id": entity_id,
            "entity_type": "business",
            "credit_score": random.randint(620, 780),
            "annual_income": float(random.randint(100000, 2000000)),
            "employment_status": "owner",
            "region": random.choice(["us-east1", "us-west1", "us-central1", "europe-west1"]),
            "loan_id": f"LN-BUS-{1000 + i}",
            "requested_amount": float(random.randint(50000, 1000000)),
            "tenor": random.choice([36, 60, 84, 120])
        })
    
    return entities


def build_repayment_event(entity, base_time, months_ago=0, missed=False):
    t = (base_time - timedelta(days=30 * months_ago)).replace(tzinfo=timezone.utc)
    payment_due = round(entity["requested_amount"] / entity["tenor"], 2)
    payment_amount = 0.0 if missed else payment_due
    outstanding = max(0.0, entity.get("requested_amount", 0) - payment_due * (months_ago))
    return {
        "event_id": gen_uuid(),
        "event_type": "repayment",
        "timestamp": t.isoformat(),
        "entity_type": entity["entity_type"],
        "entity_id": entity["entity_id"],
        "loan_id": entity["loan_id"],
        "requested_amount": entity["requested_amount"],
        "requested_tenor_months": entity["tenor"],
        "payment_due": payment_due,
        "payment_amount": payment_amount,
        "payment_method": random.choice(["ACH", "Card", "Check"]),
        "outstanding_balance": round(outstanding, 2),
        "num_past_due": 1 if missed else 0,
        "credit_score": entity["credit_score"],
        "annual_income": entity["annual_income"],
        "employment_status": entity["employment_status"],
        "region": entity["region"],
        "metadata": {"note": "historical repayment" if months_ago > 0 else "current repayment"}
    }


def build_application_event(entity):
    return {
        "event_id": gen_uuid(),
        "event_type": "application",
        "timestamp": iso_now(),
        "entity_type": entity["entity_type"],
        "entity_id": entity["entity_id"],
        "loan_id": entity["loan_id"],
        "requested_amount": entity["requested_amount"],
        "requested_tenor_months": entity["tenor"],
        "payment_due": None,
        "payment_amount": None,
        "outstanding_balance": None,
        "num_past_due": 0,
        "credit_score": entity["credit_score"],
        "annual_income": entity["annual_income"],
        "employment_status": entity["employment_status"],
        "region": entity["region"],
        "metadata": {"note": "new loan application"}
    }


def publish_message(payload: dict):
    data = json.dumps(payload).encode("utf-8")
    future = publisher.publish(topic_path, data, use_case="loan_event", entity_id=payload["entity_id"])
    message_id = future.result()
    print(f"Published message id={message_id} event_type={payload['event_type']} entity={payload['entity_id']} ts={payload['timestamp']}")


def main():
    print(f"Starting loan-events publisher for {NUM_ENTITIES} entities...")
    entities = generate_entities(NUM_ENTITIES)
    print(f"Generated {len(entities)} entities")
    
    # Count by type
    individuals = [e for e in entities if e["entity_type"] == "individual"]
    businesses = [e for e in entities if e["entity_type"] == "business"]
    print(f"  - {len(individuals)} individuals")
    print(f"  - {len(businesses)} businesses")

    # 1) Publish historical bursts for each entity (simulate past 6 months)
    print("\nPublishing historical data (6 months)...")
    now = datetime.now(timezone.utc)
    for idx, ent in enumerate(entities):
        if (idx + 1) % 50 == 0:
            print(f"  Progress: {idx + 1}/{len(entities)} entities processed")
        
        for m in range(6, 0, -1):  # last 6 months historical
            missed = random.random() < 0.08  # 8% chance a payment was missed historically
            ev = build_repayment_event(ent, now, months_ago=m, missed=missed)
            publish_message(ev)
            time.sleep(0.01)  # small gap to avoid rate-limiting
    
    print(f"\nHistorical data published for all {len(entities)} entities")
    
    # 2) Publish a sample application event for a subset of entities
    print("\nPublishing initial application events...")
    sample_applicants = random.sample(entities, min(50, len(entities)))  # 50 random applications
    for ent in sample_applicants:
        app_ev = build_application_event(ent)
        publish_message(app_ev)
        time.sleep(0.01)
    
    print(f"\nPublished {len(sample_applicants)} initial applications")
    
    # 3) Start continuous stream
    print("\nStarting continuous streaming mode...")
    tick = 0
    while True:
        tick += 1
        
        # Randomly select a subset of entities to publish repayments for this cycle
        # (simulates that not all entities have activity every cycle)
        active_entities = random.sample(entities, k=random.randint(50, 150))
        
        for ent in active_entities:
            missed = random.random() < 0.03  # 3% chance missed for streaming period
            ev = build_repayment_event(ent, datetime.now(timezone.utc), months_ago=0, missed=missed)
            publish_message(ev)
            time.sleep(0.01)

        # Publish applications for random entities
        if tick % 5 == 0:
            num_apps = random.randint(3, 10)
            applicants = random.sample(entities, k=num_apps)
            for ent in applicants:
                app_ev = build_application_event(ent)
                publish_message(app_ev)
                time.sleep(0.01)
            print(f"Cycle {tick}: Published {len(active_entities)} repayments and {num_apps} applications")
        else:
            print(f"Cycle {tick}: Published {len(active_entities)} repayments")

        time.sleep(PUBLISH_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
