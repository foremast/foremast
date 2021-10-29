import logging

LOG = logging.getLogger(__name__)


def exponential_backoff(attempt, exponent=2) -> float:
    """Exponential backoff function that returns a wait in seconds.  The attempt is multiplied exponentially
    using the exponent value (default 2).  For example: attempt 2 with an exponent of 4 would be 2^4=16.  This
    creates a backoff that gets exponentially longer for each attempt mitigating rate limiting and resource
    conflict errors.

    Use with retries annotation:

    Defaults:
    @retries(max_attempts=3, wait=exponential_backoff, exceptions=MyError)

    Overriding defaults:
    @retries(max_attempts=3, wait=lambda n: exponential_backoff(n, 4), exceptions=MyError)

    Args:
        attempt(int): Int representing the number of attempts so far
        exponent(float): Exponential modifier used to determine how long to wait
    """
    wait = exponent ** attempt
    LOG.debug("Backing off for {} seconds".format(wait))
    return wait
