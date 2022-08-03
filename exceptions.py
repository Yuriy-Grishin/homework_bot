class MessageNotSentError(Exception):
    """Сообщение не направлено."""


class Not200Error(Exception):
    """Ошибка 200 отсутствует."""


class APIProblemsError(Exception):
    """Проблемы с API."""


class EmptyError(Exception):
    """Пустое значение."""


class UnknownStatusError(Exception):
    """Неизвестный статус."""


class WrongKeyError(Exception):
    """Неверный ключ."""


class MissingTokenError(Exception):
    """Отсутствует доступ по токену."""
