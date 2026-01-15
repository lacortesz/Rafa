from confluent_kafka import Producer, Consumer
import os
import json

##--- KAFKA FUNCTIONS AND HELPERS

def init_kafka_consumer(bootstrap_server, group_id, topics):
    """
    Create kafka consumer
    parameters:
        bootstrap_server
        group_id
        topics
    return:
        consumer object
    """

    consumer_conf = {
      "bootstrap.servers": bootstrap_server,
        "group.id": group_id,
        "auto.offset.reset": "earliest"  
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe(["process_data"])

    return consumer

##-- UPDATE REPORT FUNCTIONS:
def update_report(payload):
    symbol = payload.get("symbol")
    timeframe = payload.get("timeframe")
    
    if payload.get("symbol") == None or payload.get("timeframe") == None:
        print(f"data recibida de process_data erronea")
        return "error"
    


    


##-- DATABASE FUNCTIOSN AND HELPERS
