"""Кастомные ошибки для homework."""


class TokensNotFound(NameError):
    """Необходимые токены недоступны."""

    pass


class PraktikumApiError(Exception):
    """Ошибка на сервере практикума."""

    pass


class TelegramMessageError(Exception):
    """Ошибка отправки сообщения в телеграм."""

    pass


class HomeworksTypeError(TypeError):
    """Домашние работы переданы не в виде списка."""

    pass


class ResponseTypeError(TypeError):
    """Ответ передан не в виде словаря."""

    pass


class ResponseKeysError(KeyError):
    """Ответ не содержит ожидаемых ключей."""

    pass


class HomeworkNameNotFound(KeyError):
    """Данные о домашней работе не содержат ключ homework_name."""

    pass


class HomeworkStatusNotFound(KeyError):
    """Передан некорректный статус."""

    pass
