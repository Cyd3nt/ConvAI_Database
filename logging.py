# Local imports
import uuid
# import logging

# third party imports
from google.cloud import logging
# from google.cloud.logging.handlers import CloudLoggingHandler
from google.logging.type import log_severity_pb2 as severity

logName = "convai-database-logging"


# Create a handler for Google Cloud Logging.
gcloudLoggingClient = logging.Client()
# gcloudLoggingHandler = CloudLoggingHandler(
#     gcloudLoggingClient, name=logName
# )

# Create a stream handler to log messages to the console.
# streamHandler = logging.StreamHandler()
# streamHandler.setLevel(logging.WARNING)

# Now create a logger and add the handlers:
# logger = logging.getLogger(logName)
# logger.setLevel(logging.DEBUG)
# logger.addHandler(gcloudLoggingHandler)
# logger.addHandler(streamHandler)
logger = gcloudLoggingClient.logger(logName)

def log_success_transaction(
    transactionID: str,
    origin: str,
    accessTimestamp: str,
    userInput: str,
    finalOutput: str,
    additionalInfo: str
):
    """
    Logging all successful transaction that were executed without any internal or DB error
    """
    json_payload = {
        "transactionID": transactionID,
        "origin": origin,
        "accessTimestamp": accessTimestamp,
        "userInput": userInput,
        "finalOutput": finalOutput,
        "additionalInfo": additionalInfo
    }

    logger.log_struct(json_payload, severity=severity.INFO)

def log_failed_transaction(
    transactionID: str,
    origin: str,
    accessTimestamp: str,
    userInput: str,
    error: str,
    additionalInfo: str
):
    """
    Logging all successful transaction that were executed without any internal or DB error
    """
    json_payload = {
        "transactionID": transactionID,
        "origin": origin,
        "accessTimestamp": accessTimestamp,
        "userInput": userInput,
        "error": error,
        "additionalInfo": additionalInfo
    }

    logger.log_struct(json_payload, severity=severity.ERROR)