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


def get_first_and_last_name_from_email(email_address):
    return email_address.split("@")[0].replace('.', ' ')


def _prepare_html(type_of_email, email_address, **kwargs):
    """Returns the subject of the mail (str) and the message (html)"""

    user = get_first_and_last_name_from_email(email_address)

    if type_of_email == "problem_extraction":

        kwargs_html = dict(
            user=user,
            error_message=kwargs.get("error_message"),
            time_of_problem=kwargs.get("time_of_problem"),
            resource_that_stopped=kwargs.get("resource_that_stopped"),
            folder=kwargs.get("folder"),
            nb_of_try=kwargs.get("nb_of_try"),
            time_waiting=kwargs.get("time_waiting"),
        )

    if type_of_email == "finished":

        kwargs_html = dict(
            user=user,
            config_user=kwargs.get("config_user"),
            current_time=kwargs.get("current_time"),
            time_to_download=kwargs.get("time_to_download"),
            errors=kwargs.get("errors"),
            folder=kwargs.get("folder"),
        )

    if type_of_email == "script_stopped":

        kwargs_html = dict(
            user=user,
            config_user=kwargs.get("config_user"),
            current_time=kwargs.get("current_time"),
            error=kwargs.get("error"),
            folder=kwargs.get("folder"),
        )

    html = dict_with_all_emails[type_of_email][1].format(**kwargs_html)

    return html