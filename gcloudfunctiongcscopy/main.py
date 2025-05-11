#!/usr/bin/python
# -*- coding: utf-8 -*-
# main.py
# It handles a Google Cloud Function that copies an object when it appears in a Cloud Storage bucket to another Cloud Storage bucket.

import functions_framework
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.exceptions import Forbidden

@functions_framework.cloud_event
def gcs_copy(cloud_event):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
            cloud_event (CloudEvent): The CloudEvent that triggered this function.
    """
    # Get the event data
    event = cloud_event.data

    DESTINATION_BUCKET = 'destinationbucket'   # Destination Bucket name

    file = event

    source_bucket_name = file['bucket']
    source_blob_name = file['name']
    destination_bucket_name = "bucketdestinationtest"
    destination_blob_name = "agentes-IA.jpg"

    print('From - bucket:', source_bucket_name)
    print('From - object:', source_blob_name)
    print('To - bucket:  ', destination_bucket_name)
    print('To - object:  ', destination_blob_name)

    print('Copying object ...')
    
    # Instantiate the client.
    client = storage.Client()
    
    #Imprimo la instanciacion
    print(client)

    try:
        # Get the source bucket.
        source_bucket = client.get_bucket(source_bucket_name)
        # Instantiate the source object.
        source_blob = source_bucket.blob(source_blob_name)
        # Get the destination bucket.
        destination_bucket = client.get_bucket(destination_bucket_name)
        # Copies a blob from one bucket to another one.
        source_bucket.copy_blob(source_blob, destination_bucket, destination_blob_name)
        print('\nCopied')
    except NotFound:
        print('Error: Bucket/Blob does NOT exists!!')
        pass
    except Forbidden:
        print('Error: Forbidden, you do not have access to it!!')
        pass
