import boto3
import os
import logging

from src.aws_service import AwsService
from webdriver_screenshot import WebDriverScreenshot

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamoDb = boto3.client('dynamodb')

CARFAX_USERNAME = "moe@scautohaus.net"
CARFAX_PASSWORD = "Goodday1"
MANHEIM_USERNAME = "MYCARAUCTION"
MANHEIM_PASSWORD = "Mycarauction!!"
AUTONIQ_USERNAME = "highbid"
AUTONIQ_PASSWORD = "112111"


def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info(event)

    for record in event['Records']:
        lead_id = record["body"]
        logger.info("id:" + lead_id)
        key = {'id': lead_id}
        aws = AwsService()
        id_valid = aws.item_exist('LeadManagement_Leads_Ready', key) or \
                   aws.item_exist('LeadManagement_Leads_Followup', key) or \
                   aws.item_exist('LeadManagement_Leads_Approval', key)
        if id_valid:
            if aws.item_exist('LeadManagement_Leads_Ready', key):
                response = aws.get_item('LeadManagement_Leads_Ready', key)
            elif aws.item_exist('LeadManagement_Leads_Followup', key):
                response = aws.get_item('LeadManagement_Leads_Followup', key)
            else:
                response = aws.get_item('LeadManagement_Leads_Approval', key)
            logger.info(response)
            if 'vin' in response and len(response['vin']) == 17:
                vin = str(response['vin'])

                driver = WebDriverScreenshot()
                carfax_report_name = "carfax-" + vin
                logger.info(carfax_report_name)
                manheim_report_name = "manheim-" + vin
                logger.info(manheim_report_name)
                autoniq_report_name = "autoniq-" + vin
                logger.info(autoniq_report_name)

                logger.info(int(response['mileage']))
                logger.info(float(response['estimatedCr']))

                driver.save_carfax_report('/tmp/' + carfax_report_name, CARFAX_USERNAME, CARFAX_PASSWORD, vin)
                # Upload generated screenshot files to S3 bucket.
                s3.upload_file('/tmp/' + carfax_report_name + ".pdf",
                               os.environ['BUCKET'],
                               'session_{}/carfax.pdf'.format(lead_id))
                logger.info('Upload Completed to session_{}/carfax.pdf'.format(lead_id))

                manheim_report_created = driver.save_manheim_report('/tmp/' + manheim_report_name,
                                                                    MANHEIM_USERNAME,
                                                                    MANHEIM_PASSWORD,
                                                                    vin,
                                                                    int(response['mileage']),
                                                                    str(float(response['estimatedCr'])),
                                                                    response['color'])
                logger.info("Manheim Report is created:" + str(manheim_report_created))
                if manheim_report_created:
                    s3.upload_file('/tmp/' + manheim_report_name + ".pdf",
                                   os.environ['BUCKET'],
                                   'session_{}/manheim.pdf'.format(lead_id))
                    logger.info('Upload Completed to session_{}/manheim.pdf'.format(lead_id))
                driver.save_autoniq_report('/tmp/' + autoniq_report_name,
                                           AUTONIQ_USERNAME, AUTONIQ_PASSWORD, vin)
                s3.upload_file('/tmp/' + autoniq_report_name + ".png",
                               os.environ['BUCKET'],
                               'session_{}/autoniq.png'.format(lead_id))
                logger.info('Upload Completed to session_{}/autoniq.png'.format(lead_id))
                driver.close()

