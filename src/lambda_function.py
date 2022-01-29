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


def delete_tmp_files():
    files_in_directory = os.listdir('/tmp')
    filtered_files = [file for file in files_in_directory if file.endswith(".pdf")]
    for file in filtered_files:
        path_to_file = os.path.join('/tmp', file)
        os.remove(path_to_file)


def lambda_handler(event, context):
    logger.info(event)
    delete_tmp_files()

    for record in event['Records']:
        vin = record["body"]
        logger.info("vin:" + vin)
        if len(vin) == 17:
            driver = WebDriverScreenshot()
            carfax_report_name = vin + "_carfax"
            logger.info(carfax_report_name)
            manheim_report_name = vin + "_manheim"
            logger.info(manheim_report_name)
            autoniq_report_name = vin + "_autoniq"
            logger.info(autoniq_report_name)

            carfax_report_created = driver.save_carfax_report('/tmp/' + carfax_report_name, CARFAX_USERNAME, CARFAX_PASSWORD, vin)
            if carfax_report_created:
                s3.upload_file('/tmp/' + carfax_report_name + ".pdf",
                               os.environ['BUCKET'],
                               'car_report/{}_carfax.pdf'.format(vin))
                logger.info('Upload Completed to car_report/{}_carfax.pdf'.format(vin))

            '''
            if ('mileage' in response) and ('estimatedCr' in response) and ('color' in response):
                logger.info(int(response['mileage']))
                logger.info(float(response['estimatedCr']))

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
            '''

            driver.save_autoniq_report('/tmp/' + autoniq_report_name,
                                       AUTONIQ_USERNAME, AUTONIQ_PASSWORD, vin)
            s3.upload_file('/tmp/' + autoniq_report_name + ".png",
                           os.environ['BUCKET'],
                           'car_report/{}_autoniq.png'.format(vin))
            logger.info('Upload Completed to car_report/{}_autoniq.png'.format(vin))
            driver.close()

    delete_tmp_files()

