#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# A simple example demonstrating use of JSONSerializer.

import argparse
from uuid import uuid4
from six.moves import input
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
#from confluent_kafka.schema_registry import *
import pandas as pd
from typing import List

FILE_PATH = "/Users/thestupidmonk/Downloads/StreamingData/Region.csv"

API_KEY = 'KD73MFTA43GJGYAU'
ENDPOINT_SCHEMA_URL  = 'https://psrc-zy38d.ap-southeast-1.aws.confluent.cloud'
API_SECRET_KEY = 'mg1tiAkfVaAodK7smAbnDbZCsirKQeL/eHSW0XashWO+ScwTjICCwzx82MPLkNIZ'
BOOTSTRAP_SERVER = 'pkc-1dkx6.ap-southeast-1.aws.confluent.cloud:9092'
SECURITY_PROTOCOL = 'SASL_SSL'
SSL_MACHENISM = 'PLAIN'
SCHEMA_REGISTRY_API_KEY = 'UQLMVUN3TEKX74QF'
SCHEMA_REGISTRY_API_SECRET = 'lTjW6qT5HeAoOE4Hv9pk8syDO7uHFmPRUJqQREjBC/rE5Qzlk1eUAFIswzG/oav6'


def sasl_conf():

    sasl_conf = {'sasl.mechanism': SSL_MACHENISM,
                 # Set to SASL_SSL to enable TLS support.
                #  'security.protocol': 'SASL_PLAINTEXT'}
                'bootstrap.servers':BOOTSTRAP_SERVER,
                'security.protocol': SECURITY_PROTOCOL,
                'sasl.username': API_KEY,
                'sasl.password': API_SECRET_KEY
                }
    return sasl_conf



def schema_config():
    return {'url':ENDPOINT_SCHEMA_URL,
    
    'basic.auth.user.info':f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"

    }


class Region:   
    def __init__(self,record:dict):
        for k,v in record.items():
            setattr(self,k,v)
        
        self.record=record
   
    @staticmethod
    def dict_to_region(data:dict,ctx):
        return Region(record=data)

    def __str__(self):
        return f"{self.record}"


def get_region_instance(file_path):
    df=pd.read_csv(file_path)
    columns=list(df.columns)
    df=df.iloc[:,0:]
    regions:List[Region]=[]
    for data in df.values:
        region=Region(dict(zip(columns,data)))
        regions.append(region)
        yield region

def region_to_dict(region:Region, ctx):
    """
    Returns a dict representation of a User instance for serialization.
    Args:
        user (User): User instance.
        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.
    Returns:
        dict: Dict populated with user attributes to be serialized.
    """

    # User._address must not be serialized; omit from dict
    return region.record


def delivery_report(err, msg):
    """
    Reports the success or failure of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    """

    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def main(topic):

    schema_registry_conf = schema_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    string_serializer = StringSerializer('utf_8')
    my_schema = schema_registry_client.get_latest_version(topic + '-value').schema.schema_str

    json_serializer = JSONSerializer(my_schema, schema_registry_client, region_to_dict)
    producer = Producer(sasl_conf())

    valuee = schema_registry_client.get_latest_version(topic + '-value').schema.schema_str
    print("Version --------------------->", valuee)
    get_region_instance(file_path=FILE_PATH).__str__()

    print("Producing user records to topic {}. ^C to exit.".format(topic))

    producer.poll(0.0)
    try:
        for idx, region in enumerate(get_region_instance(file_path=FILE_PATH)):
            print(region)
            producer.produce(topic=topic,
                             key=string_serializer(str(uuid4()), region_to_dict),
                             value=json_serializer(region, SerializationContext(topic, MessageField.VALUE)),
                             on_delivery=delivery_report)
            
            # if idx==10:
            #   break
    except KeyboardInterrupt:
        pass
    except ValueError:
        print("Invalid input, discarding record...")
        pass


    print("\nFlushing records...")
    producer.flush()

main("Region_Topic")

