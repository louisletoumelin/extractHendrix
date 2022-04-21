import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import warnings
import time

import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

warnings.simplefilter(action='ignore', category=FutureWarning)
dict_with_all_emails = \
    dict(
        problem_extraction=(
            "Extraction on Hendrix is paused",
            """
            <p> Dear {user}, </p>
            <p> </p>
            <p> <strong> Extraction on Hendrix has stopped </strong> with the following message:</p>
            <p style = "text-align: center;" > {error_message} </p>
            <p> </p>
            <p> The extraction stopped at time: </p>
            <p style = "text-align: center;"> {time_of_problem} </p>
            <p style = "text-align: center;"> </p>
            <p> We stopped while trying to reach this Vortex resource: </p>
            <p style = "text-align: center;"> {resource_that_stopped} </p>
            <p style = "text-align: left;"> </p>
            <p style = "text-align: left;"> We remind you that we are working here: </p>
            <p style = "text-align: center;">  {folder} </p>
            <p style = "text-align: center;"> </p>
            <p> <strong> We are now waiting {time_waiting} minutes</strong> before launching again commands on Hendrix. 
            <strong> You don't need to do anything.</strong></p>
            <p> It is our try number: {nb_of_try}. </p>
            <p style="margin-bottom:3cm;"> How long am I waiting? The first 5 attemps to reach Hendrix are distant from 30 min.
            If Hendrix is still unreachable, we wait 1 hour between attemps. 
            Finally, if we missed 10 attemps, we stop.</p>
            <pstyle="margin-bottom:1.5cm;"> </p>
            <p> </p>
            <p> Thank you for your understanding, </p>
            <p> HendrixConductor </p>
            <p> </p>
            <p> </p>
            """),

        finished=(
            "Your extraction on Hendrix has finished",
            """
            <p> Dear {user}, </p>
            <p> </p>
            <p> <strong> Your extraction on Hendrix correctly finished. </strong></p>
            <p> The downloaded files are: </p>
            <p style = "text-align: center;" > {config_user} </p>
            <p> The extraction finished at:</p>
            <p style = "text-align: center;" > {current_time} </p>
            <p> </p>
            <p> Total time to download files: </p>
            <p style = "text-align: center;"> {time_to_download} hours </p>
            <p style = "text-align: center;"> </p>
            <p style = "text-align: left;"> </p>
            <p style = "text-align: left;"> If anything went wrong, it could be listed below: </p>
            <p style = "text-align: center;">  {errors} </p>
            <p style = "text-align: center;"> </p>
            <p style = "text-align: left;"> We remind you that we are working here: </p>
            <p style = "text-align: center;">  {folder} </p>
            <p style = "text-align: center;"> </p>
            <pstyle="margin-bottom:1.5cm;"> </p>
            <p> </p>
            <p> HendrixConductor </p>
            <p> </p>
            <p> </p>
            """),

        script_stopped=(
            "Extraction on Hendrix didn't work",
            """
                <p> Dear {user}, </p>
                <p> </p>
                <p> <strong> Your extraction on Hendrix didn't work. </strong></p>
                <p> The configuration is: </p>
                <p style = "text-align: center;" > {config_user} </p>
                <p> The error is:</p>
                <p style = "text-align: center;" > {error} </p>
                <p> The error occurred at:</p>
                <p style = "text-align: center;" > {current_time} </p>
                <p style = "text-align: left;"> We remind you that we are working here: </p>
                <p style = "text-align: center;">  {folder} </p>
                <pstyle="margin-bottom:1.5cm;"> </p>
                <p> </p>
                <p> HendrixConductor </p>
                <p> </p>
                <p> </p>
                """)
    )


def send_email(email_address, subject, content):
    """Send email to email_address using Météo-France network"""
    server = smtplib.SMTP()
    server.connect('smtp.cnrm.meteo.fr')
    server.helo()
    from_addr = 'HendrixConductor <do_not_answer@hendrixconductor.fr>'
    to_addrs = email_address if isinstance(
        email_address, list) else [email_address]
    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = ','.join(to_addrs)
    msg["Date"] = formatdate(localtime=True)
    msg['Subject'] = subject
    part = MIMEText(content, 'html')
    msg.attach(part)
    try:
        server.sendmail(from_addr, to_addrs, msg.as_string())
        logger.info(f"Successfully sent an email to {to_addrs}\n\n")
    except smtplib.SMTPException as e:
        logger.error(
            f"Email could not be launched. The error is: {e}\n\n")
    server.quit()


def get_first_and_last_name_from_email(email_address):
    return email_address.split("@")[0].replace('.', ' ').title()


def send_succes_email(email_adress=None, config_user=None, current_time=None, time_to_download=None, errors=None, folder=None):
    user = get_first_and_last_name_from_email(email_adress)
    html = dict_with_all_emails["finished"][1].format(**locals())
    subject = dict_with_all_emails["finished"][0]
    send_email(email_adress, subject, html)
    return


def send_problem_extraction_email(email_adress=None, error_message=None, time_of_problem=None, resource_that_stopped=None, folder=None, nb_of_try=None, time_waiting=None):
    user = get_first_and_last_name_from_email(email_adress)
    html = dict_with_all_emails["problem_extraction"][1].format(
        **locals())
    subject = dict_with_all_emails["problem_extraction"][0]
    send_email(email_adress, subject, html)
    return


def send_script_stopped_email(email_adress=None, config_user=None, current_time=None, error=None, folder=None):
    user = get_first_and_last_name_from_email(email_adress)
    html = dict_with_all_emails["script_stopped"][1].format(
        **locals())
    subject = dict_with_all_emails["script_stopped"][0]
    send_email(email_adress, subject, html)
