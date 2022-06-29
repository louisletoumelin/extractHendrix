import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import warnings


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
            <p style = "text-align: left;"> We remind you that we are working here: </p>
            <p style = "text-align: center;">  {folder} </p>
            <p style = "text-align: center;"> </p>
            <p> <strong> We are now waiting {time_waiting} minutes</strong> before launching again commands on Hendrix. 
            <strong> You don't need to do anything.</strong></p>
            <p> It is our attempt number: {nb_of_try}. </p>
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


class DictNamespace:
    """A trick to use attributes instead of dictionary keys"""
    def __init__(self, dict_):
        self.__dict__ = dict_


def send_email(email_address, subject, content):
    """
    Send email to email_address using Météo-France network

    :param email_address: Email adress.
    :param subject: Subject of the email.
    :param content: Content of the email.
    """
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
    """
    Parse email to return first name and last name

    e.g.
    >> get_first_and_last_name_from_email("john.doe@mail.com")
        "John Doe"
    :param email_address:
    :return:
    """
    return email_address.split("@")[0].replace('.', ' ').title()


def send_success_email(config_user):
    """
    Prepare a function to send email when extraction has occurred without problem.

    :param config_user: Dictionary containing the configuration as given by the user.
    :return: Function ready to send an email.
    """
    def emailsender(current_time, time_to_download):
        c = DictNamespace(config_user)
        user = get_first_and_last_name_from_email(c.email_adress)
        html = dict_with_all_emails["finished"][1].format(
            user=user,
            config_user=config_user,
            current_time=current_time,
            time_to_download=time_to_download,
            folder=c.work_folder
        )
        subject = dict_with_all_emails["finished"][0]
        send_email(c.email_adress, subject, html)
    return emailsender


def send_problem_extraction_email(config_user):
    """
    Prepare a function to send email when a problem is encountered during extraction.

    :param config_user: Dictionary containing the configuration as given by the user.
    :return: Function ready to send an email.
    """
    def emailsender(exception, time_fail, nb_attempts, time_to_next_retry):
        c = DictNamespace(config_user)
        user = get_first_and_last_name_from_email(c.email_adress)
        html = dict_with_all_emails["problem_extraction"][1].format(
            user=user,
            error_message=exception,
            time_of_problem=time_fail,
            folder=c.work_folder,
            time_waiting=time_to_next_retry,
            nb_of_try=nb_attempts
        )
        subject = dict_with_all_emails["problem_extraction"][0]
        send_email(c.email_adress, subject, html)
    return emailsender


def send_script_stopped_email(config_user):
    """
    Prepare a function to send email when extraction has stopped.

    :param config_user: Dictionary containing the configuration as given by the user.
    :return: Function ready to send an email.
    """
    def emailsender(exception, current_time):
        c = DictNamespace(config_user)
        user = get_first_and_last_name_from_email(c.email_adress)
        html = dict_with_all_emails["script_stopped"][1].format(
            user=user,
            config_user=config_user,
            error=exception,
            current_time=current_time,
            folder=c.work_folder,
        )
        subject = dict_with_all_emails["script_stopped"][0]
        send_email(c.email_adress, subject, html)
    return emailsender
