import json
import logging

from webdriver_screenshot import WebDriverScreenshot

CARFAX_USERNAME = "moe@scautohaus.net"
CARFAX_PASSWORD = "Goodday1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_mmr_adjustment(highlights):
    for highlight in highlights:
        if "buyback" in highlight.lower():
            return 0.6
        if "lemon" in highlight.lower():
            return 0.6
        if highlight.lower().startswith("branded title"):
            return 0.5
    return 1


def get_cr_adjustment(highlights):
    cr = 4.5
    for highlight in highlights:
        if highlight.lower().startswith("accident reported"):
            cr = min(cr, 2.5)
            if "airbag deployed" in highlight.lower():
                cr = min(cr, 1.5)
            if "vehicle not damaged" in highlight.lower():
                cr = min(cr, 3.0)
        if highlight.lower().startswith("damage reported"):
            cr = min(cr, 2.5)
            if "airbag deployed" in highlight.lower():
                cr = min(cr, 1.5)
            if "structural" in highlight.lower():
                cr = min(cr, 1.5)
        if "vehicle reported stolen" in highlight.lower():
            cr = min(cr, 2.0)
        if "taxi" in highlight.lower():
            cr = min(cr, 2.0)
    return cr


def get_appraisal_needed(highlights):
    for highlight in highlights:
        if "total loss" in highlight.lower():
            return True
        if "odometer rollback" in highlight.lower():
            return True
    return False


def get_carfax_highlight(event):
    message = json.loads(event["body"])
    vin = message['vin']
    logger.info("Get CarFax scores for VIN:" + vin)
    driver = WebDriverScreenshot()
    highlights = driver.get_carfax_highlight(CARFAX_USERNAME, CARFAX_PASSWORD, vin)
    response = {
        'highlights': highlights,
        'cr_adj': get_cr_adjustment(highlights),
        'mmr_adj_percent': get_mmr_adjustment(highlights),
        'appraisal_needed': get_appraisal_needed(highlights)
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
