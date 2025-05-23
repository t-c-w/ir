"""
amazon_sender.py
~~~~~~~~

Python helper class that can send emails using Amazon SES and boto.
The biggest feature of this class is that encodings are handled properly.
It can send both text and html emails.
This implementation is using Python's standard library (which opens up for a lot more options).

Example::

    amazon_sender = AmazonSender(AWS_ID, AWS_SECRET)

    amazon_sender.send_email(sender=u'Me <john@doe.com>',
                             to='blah@blah.com',
                             subject='Hello friend',
                             text='Just a message',
                             html='<b>Just a message</b>',
                             sender_ascii='Ascii Sender <no_reply@wedoist.com>')


:copyright: 2011 by Amir Salihefendic ( http://amix.dk/ ).
:license: BSD
"""

import types

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from ut.util.importing import get_environment_variable
from boto.ses import SESConnection


class AmazonSender(object):

    client = None

    def __init__(self, to_addresses=None, sender=None, aws_key=None, aws_secret=None):
        self.sender = sender or 'Thor Stats <thor_stats@mscoms.com>'
        self.to_addresses = to_addresses or 'thor@mscoms.com'
        self.aws_key = aws_key or get_environment_variable('VEN_S3_ACCESS_KEY')
        self.aws_secret = aws_secret or get_environment_variable('VEN_S3_SECRET')

    def send_email(
        self, subject='', text='', html=None, reply_addresses=None, sender_ascii=None
    ):
        if not sender_ascii:
            sender_ascii = self.sender

        client = self.get_client()

        message = MIMEMultipart('alternative')
        message.set_charset('UTF-8')

        message['Subject'] = _encode_str(subject)
        message['From'] = _encode_str(self.sender)

        message['To'] = _convert_to_strings(self.to_addresses)

        if reply_addresses:
            message['Reply-To'] = _convert_to_strings(reply_addresses)

        message.attach(MIMEText(_encode_str(text), 'plain'))

        if html:
            message.attach(MIMEText(_encode_str(html), 'html'))

        return client.send_raw_email(
            message.as_string(), sender_ascii, destinations=self.to_addresses
        )

    def verify_email(self, email):
        client = self.get_client()
        return client.verify_email_address(email)

    def get_client(self):
        if not self.client:
            self.client = SESConnection(self.aws_key, self.aws_secret)
        return self.client


# --- Helpers ----------------------------------------------
def _convert_to_strings(list_of_strs):
    if isinstance(list_of_strs, (list, tuple)):
        result = COMMASPACE.join(list_of_strs)
    else:
        result = list_of_strs
    return _encode_str(result)


def _encode_str(s):
    if type(s) == str:
        return s.encode('utf8')
    return s




def list_verified_emails(sender):
    """
    Retrieves a list of all email addresses that have been verified with Amazon SES in the sender's account.
    
    Parameters:
        sender (AmazonSender): An instance of the AmazonSender class.
    
    Returns:
        list: A list of verified email addresses.
    
    Example:
        >>> amazon_sender = AmazonSender(aws_key='your_aws_access_key', aws_secret='your_aws_secret_key')
        >>> verified_emails = list_verified_emails(amazon_sender)
        >>> print(verified_emails)
    """
    client = sender.get_client()
    response = client.list_verified_email_addresses()
    return response.get('VerifiedEmailAddresses', [])

def batch_send_emails(sender, emails):
    """
    Sends multiple emails in a batch. Each email in the list should be a dictionary specifying the parameters
    for the send_email method of the AmazonSender class.
    
    Parameters:
        sender (AmazonSender): An instance of the AmazonSender class.
        emails (list of dict): A list where each dictionary contains parameters for the send_email method.
    
    Returns:
        list: A list of responses from the send_email method for each email sent.
    
    Example:
        >>> amazon_sender = AmazonSender(aws_key='your_aws_access_key', aws_secret='your_aws_secret_key')
        >>> emails = [
        ...     {'subject': 'Hello', 'text': 'Hello there!', 'to_addresses': ['example1@example.com']},
        ...     {'subject': 'Greetings', 'text': 'Greetings!', 'to_addresses': ['example2@example.com']}
        ... ]
        >>> responses = batch_send_emails(amazon_sender, emails)
        >>> print(responses)
    """
    responses = []
    for email in emails:
        response = sender.send_email(**email)
        responses.append(response)
    return responses
