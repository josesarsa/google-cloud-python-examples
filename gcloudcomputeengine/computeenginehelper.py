#!/usr/bin/python
# -*- coding: utf-8 -*-
# computeenginehelper.py
# It has methods for managing Google Cloud Compute Engine VM instances.

import sys
import os
import time
from googleapiclient import discovery
from google.oauth2 import service_account
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
required_vars = [
    'GCP_ZONE',
    'GCP_PROJECT_ID',
    'GCP_IMAGE_NAME',
    'GCP_IMAGE_PROJECT',
    'GCP_INSTANCE_TYPE',
    'GCP_INSTANCE_NAME',
    'GCP_VPC_NETWORK',
    'GCP_VPC_SUBNET',
    'GOOGLE_APPLICATION_CREDENTIALS'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"  - {var}")
    sys.exit(1)

# Load configuration from environment
ZONE_NAME           = os.getenv('GCP_ZONE')            # Zone name
PROJECT_NAME        = os.getenv('GCP_PROJECT_ID')      # Project name
IMAGE_NAME          = os.getenv('GCP_IMAGE_NAME')      # Image name
IMAGE_PROJECT_NAME  = os.getenv('GCP_IMAGE_PROJECT')   # Image project name
INSTANCE_TYPE       = os.getenv('GCP_INSTANCE_TYPE')   # Instance type
INSTANCE_NAME       = os.getenv('GCP_INSTANCE_NAME')   # Name of the instance

# Validate credentials file exists
credentials_path = os.path.expanduser(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
if not os.path.exists(credentials_path):
    print(f"Error: Credentials file not found at {credentials_path}")
    sys.exit(1)


def list_instances():
    """
    List all Compute Engine VM instances associated with an Google Cloud account
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Listing VM instances ...')

    # Describe instances
    response = compute.instances().list(project=PROJECT_NAME, zone=ZONE_NAME).execute()
    print('Instances in project "%s" and zone "%s":' % (PROJECT_NAME, ZONE_NAME))
    if (response.get('items')):
        for instance in response['items']:
            print(' - Id:           ' + instance['id'])
            print('   Name:         ' + instance['name'])
            print('   Status:       ' + instance['status'])
            print('   Machine type: ' + instance['machineType'])
    else:
        print('NO instances')

    return


def create_instance():
    """
    Create a Compute Engine VM instance
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Creating VM instance ...')

    # Get the latest image
    image_response = compute.images().getFromFamily(
                              project=IMAGE_PROJECT_NAME, family=IMAGE_NAME).execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    #machine_type = 'zones/' + ZONE_NAME + '/machineTypes/' + INSTANCE_TYPE
    machine_type = 'zones/%s/machineTypes/%s' % (ZONE_NAME, INSTANCE_TYPE)

    config = {
          'name': INSTANCE_NAME,
          'machineType': machine_type,

          # Specify the boot disk and the image to use as a source.
          'disks': [
              {
                  'boot': True,
                  'autoDelete': True,
                  'initializeParams': {
                      'sourceImage': source_disk_image,
                  }
              }
          ],

          # Specify the VPC network without public IP
          'networkInterfaces': [{
              'network': os.getenv('GCP_VPC_NETWORK'),
              'subnetwork': os.getenv('GCP_VPC_SUBNET')  # You'll need to add this to your .env file
          }],

          # Allow the instance to access cloud storage and logging.
          'serviceAccounts': [{
              'email': 'default',
              'scopes': [
                  'https://www.googleapis.com/auth/devstorage.read_write',
                  'https://www.googleapis.com/auth/logging.write'
              ]
          }]
    }

    response = compute.instances().insert(project=PROJECT_NAME,
                              zone=ZONE_NAME,
                              body=config).execute()

    print('Instance Id: ' + response['targetId'])

    return response['targetId']


def list_instance(instance_id):
    """
    List a Compute Engine VM instance
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Listing VM instance ...')
    print('Instance Id: ' + instance_id)

    # List the VM instance
    response = compute.instances().get(project=PROJECT_NAME, zone=ZONE_NAME, instance=INSTANCE_NAME).execute()

    print(' - Id:           ' + response['id'])
    print('   Name:         ' + response['name'])
    print('   Status:       ' + response['status'])
    print('   Machine type: ' + response['machineType'])

    return


def start_instance(instance_id):
    """
    Start a Compute Engine VM instance
    """
    try:
        # Build and initialize the API
        compute = googleapiclient.discovery.build('compute', 'v1')

        print('Starting VM instance ...')
        print(f'Project: {PROJECT_NAME}')
        print(f'Zone: {ZONE_NAME}')
        print(f'Instance Name: {INSTANCE_NAME}')
        print(f'Instance Id: {instance_id}')

        # Get instance status before starting
        instance = compute.instances().get(
            project=PROJECT_NAME,
            zone=ZONE_NAME,
            instance=INSTANCE_NAME).execute()
        print(f'Current instance status: {instance["status"]}')

        # Start VM instance
        operation = compute.instances().start(
            project=PROJECT_NAME,
            zone=ZONE_NAME,
            instance=INSTANCE_NAME).execute()

        print(f'Start operation initiated: {operation["name"]}')
        print('Waiting for operation to complete...')

        # Wait for the operation to complete
        while True:
            result = compute.zoneOperations().get(
                project=PROJECT_NAME,
                zone=ZONE_NAME,
                operation=operation['name']).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    print(f'Error starting instance: {result["error"]}')
                else:
                    # Get final instance status
                    instance = compute.instances().get(
                        project=PROJECT_NAME,
                        zone=ZONE_NAME,
                        instance=INSTANCE_NAME).execute()
                    print(f'Instance successfully started. Status: {instance["status"]}')
                break

            print('Operation still in progress...')
            time.sleep(5)  # Wait 5 seconds before checking again

    except Exception as e:
        print(f'Error starting instance: {str(e)}')


def stop_instance(instance_id):
    """
    Stop a Compute Engine VM instance
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Stopping VM instance ...')
    print('Instance Id: ' + instance_id)

    # Stop VM instance
    compute.instances().stop(
          project=PROJECT_NAME,
          zone=ZONE_NAME,
          instance=INSTANCE_NAME).execute()

    return


def reset_instance(instance_id):
    """
    Reset a Compute Engine VM instance
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Resetting VM instance ...')
    print('Instance Id: ' + instance_id)

    # Reset VM instance
    compute.instances().reset(
          project=PROJECT_NAME,
          zone=ZONE_NAME,
          instance=INSTANCE_NAME).execute()

    return


def delete_instance(instance_id):
    """
    Delete a Compute Engine VM instance
    """
    # Build and initialize the API
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Deleting VM instance ...')
    print('Instance Id: ' + instance_id)

    # Delete VM instance
    compute.instances().delete(
          project=PROJECT_NAME,
          zone=ZONE_NAME,
          instance=INSTANCE_NAME).execute()

    return
