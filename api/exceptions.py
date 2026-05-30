from config import logger

__all__ = ['Error', 'BadGatewayError', 'WrongResponseException', 'BadAPIKeyException',
           'InsufficientFundsException', 'UnknownError', 'TooManyRequests', 'BadRequestError']


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class BadAPIKeyException(Error):
    def __init__(self):
        logger.error('Bad API key used or Unauthorized')
        super().__init__('Bad API key used or Unauthorized')


class WrongResponseException(Error):
    def __init__(self, response_text: str):
        logger.error(f'Wrong response was received: {response_text}')
        self.response = response_text
        super().__init__(response_text)


class UnknownError(Error):
    def __init__(self, text: str):
        logger.error(f'Unknown error: {text}')
        self.response = text
        super().__init__(text)


class InsufficientFundsException(Error):
    pass


class TooManyRequests(Error):
    pass


class BadGatewayError(Error):
    def __init__(self, text: str = ''):
        logger.error(text or 'Bad gateway error')
        self.response = text
        super().__init__(text or 'Bad gateway error')


class BadRequestError(Error):
    pass
