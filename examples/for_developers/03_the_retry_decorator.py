from datetime import timedelta

from extracthendrix.configreader import retry_and_finally_raise

# short example, but if the code of retry_and_finally_raise can seem tricky, what it does is relatively simple:
# when an exception is raised in the decorated function, it waits and relaunches the function according to what he's been told


# it needs two callbacks functions, to execute each time the decorated function fails
# note: you have to provide a function with these exacts same arguments
def onRetry(exception_raised, time_fail, nb_attempts, time_to_next_retry):
    message = (
        f"Exception {exception_raised} at time {time_fail}\n"
        f"{nb_attempts} attempts made so far\n"
        f"retrying again in {time_to_next_retry}\n"
    )
    print(message)


# this one is called after the final attempt has been maid and failed
def onFailure(exception_raised, current_time):
    message = (
        f"Exception {exception_raised} at time {current_time}\n"
        f"This was the final attempt, I'm reraising the exception"
    )
    print(message)


def silly_function():
    print("It's a witch!")
    raise Exception("Burn!")


# now if we wrap the function in retry_and_finally_raise, and we call it we get:
retry_and_finally_raise(
    onRetry=onRetry,
    onFailure=onFailure,
    time_retries=[timedelta(seconds=s) for s in range(4)]
)(silly_function)()


# we could achieve the same result with the @ notation
@retry_and_finally_raise(
    onRetry=onRetry,
    onFailure=onFailure,
    time_retries=[timedelta(seconds=s) for s in range(4)]
)
def silly_function_decorated():
    print("It's a witch!")
    raise Exception("Burn!")


silly_function_decorated()

# note : it was technically impossible to decorate the AromeReader.get_native_file method  with the @ notation with the ability
# to choose the retry and failure callback and the time_retries
# (the reason being you can't use self in a method decorator)
# that's why the "decoration" is made  in the configreader.execute function around the computer.compute value


# see the configreader.execute method to see this decorator at work in the context of our extractions
