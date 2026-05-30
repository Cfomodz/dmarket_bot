"""Tests for custom exception classes."""

import pytest

from api.exceptions import (
    BadAPIKeyException,
    BadGatewayError,
    BadRequestError,
    Error,
    InsufficientFundsException,
    TooManyRequests,
    UnknownError,
    WrongResponseException,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_error(self):
        assert issubclass(BadAPIKeyException, Error)
        assert issubclass(WrongResponseException, Error)
        assert issubclass(UnknownError, Error)
        assert issubclass(InsufficientFundsException, Error)
        assert issubclass(TooManyRequests, Error)
        assert issubclass(BadGatewayError, Error)
        assert issubclass(BadRequestError, Error)

    def test_error_inherits_from_exception(self):
        assert issubclass(Error, Exception)


class TestBadAPIKeyException:
    def test_can_be_raised(self):
        with pytest.raises(BadAPIKeyException):
            raise BadAPIKeyException()

    def test_message(self):
        try:
            raise BadAPIKeyException()
        except BadAPIKeyException as e:
            assert "Bad API key" in str(e)


class TestWrongResponseException:
    def test_stores_response(self):
        try:
            raise WrongResponseException("bad data")
        except WrongResponseException as e:
            assert e.response == "bad data"


class TestBadGatewayError:
    def test_default_message(self):
        try:
            raise BadGatewayError()
        except BadGatewayError as e:
            assert "Bad gateway error" in str(e)

    def test_custom_message(self):
        try:
            raise BadGatewayError("custom error")
        except BadGatewayError as e:
            assert e.response == "custom error"


class TestUnknownError:
    def test_stores_response(self):
        try:
            raise UnknownError("mystery")
        except UnknownError as e:
            assert e.response == "mystery"
