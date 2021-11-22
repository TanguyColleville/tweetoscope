"""
The aim of this code is predict the number of retweet thanks to the estimated 
parameters.
"""


import argparse                   # To parse command line arguments
import json                       # To parse and dump JSON
from kafka import KafkaConsumer   # Import Kafka consumer
from kafka import KafkaProducer   # Import Kafka producer
import numpy as np

import predictor_tools as prd
import logger

if __name__=="__main__": 

    logger = logger.get_logger('predictor', broker_list="localhost::9092",debug=True)
    ################################################
    #######         Kafka Part              ########
    ################################################

    topic_reading="cascadeproperties"
    topic_reading_2="models"
    topic_writing_sample="samples"
    topic_writing_alert="alerts"
    topic_writing_stats="stats"

    logger.info("Setting up kafka consumer & producer for predictor part...")


    parser = argparse.ArgumentParser()
    parser.add_argument('--broker-list', type=str, help="the broker list", default="localhost:9092")
    args = parser.parse_args()  # Parse arguments

    consumer = KafkaConsumer(topic_reading,                   # Topic name
      bootstrap_servers = args.broker_list,                        # List of brokers passed from the command line
      value_deserializer=lambda v: json.loads(v.decode('utf-8')),  # How to deserialize the value from a binary buffer
      key_deserializer= lambda v: v.decode()                       # How to deserialize the key (if any)
    )

    producer = KafkaProducer(
      bootstrap_servers = args.broker_list,                     # List of brokers passed from the command line
      value_serializer=lambda v: json.dumps(v).encode('utf-8'), # How to serialize the value to a binary buffer
      # key_serializer=str.encode                                 # How to serialize the key
    )

    

    ################################################
    #####         Prediction Part              #####
    ################################################
    logger.info("Start reading in cascade properties topic...")
    for msg in consumer : 
        msg=msg.value # which will be remplaced by our object in a near future 
        my_params=np.array(msg["params"])
        cid=msg["cid"]

        logger.info(f"Predictions computation for {cid} ...")
        # modifier predictions afin d'avoir G1 en valeur de sortie aussi et N_star
        N,N_star,G1= prd.predictions(params=my_params, history = msg["tweets"], alpha=2.016,mu=1)
      
        send_sample= {
          'type': 'sample',
          'cid': cid,
          'params': my_params,
          'X': [msg["beta"],N_star,G1],
          'W' : (msg["n_supp"]-msg["n_obs"])*(1-N_star)/G1,# based on true result
          }
        producer.send(topic_writing_sample, key =msg["T_obs"], value = send_sample)

        # to be tuned to make it nicer
        send_alert={
          'type': 'alert',
          'to display' :'very hot topic, follow up with it',
          'cid': cid,
          'n_tot': N,
        }

        producer.send(topic_writing_alert, key =msg["T_obs"], value = send_alert)
        

        error = 0 # to be implemented
        send_stats={
          'type': 'stats',
          'cid' :cid, 
          'T_obs': msg["T_obs"],
          'ARE' : error, 
        }
        producer.send(topic_writing_stats, key =None, value = send_stats)
        logger.info(f"Messages sended post predictions for {cid}...")