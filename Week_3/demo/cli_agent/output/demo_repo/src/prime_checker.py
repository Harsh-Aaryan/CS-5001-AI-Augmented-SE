"""Prime number checker module."""

def is_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: Integer to check for primality.

    Returns:
        True if n is prime, False otherwise.

    Raises:
        ValueError: If n is less than 2.
    """
    if n < 2:
        raise ValueError("Number must be 2 or greater")
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True
