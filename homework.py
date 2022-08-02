import logging
import os
import requests

import telegram
import time
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    filename='program.log',
    format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
    level=logging.DEBUG,
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)


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


def send_message(bot, message):
    """Отправка сообщения боту."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение направлено')
    except Exception as error:
        logger.error(f'Сообщение не направлено: {error}')


def get_api_answer(current_timestamp):
    """Отправка запроса в Яндекс.Практикум"""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        response_json = response.json()
        if response.status_code != 200:
            raise Not200Error
        logger.debug('Успешная обработка')
        logger.debug(f'Полуен ответ {response_json}')
        return response.json()
    except Exception:
        if response.status_code != 200:
            raise APIProblemsError('Ресурс API недоступен')
        else:
            raise APIProblemsError('Сбой запроса')


def check_response(response):
    """Проверка запроса"""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error('Пустое значение')
    if response.get('homeworks') is None:
        response_message_1 = ('Неверный ключ')
        logger.error(response_message_1)
        raise EmptyError(response_message_1)
    if homeworks == []:
        return {}
    if not isinstance(response.get('homeworks', None), list):
        raise KeyError('Неверный формат')
    return homeworks


def parse_status(homework):
    """Проверка статуса на изменение"""
    try:
        homework_status = homework['status']
        homework_name = homework['homework_name']
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        logging.error('Ошибка статуса')
        raise KeyError('Ошибка в статусе')
    if homework['homework_name'] is None:
        status_message_1 = 'Ключ отсутствует к homework_name'
        logger.error(status_message_1)
        raise KeyError(status_message_1)
    if homework_status is None:
        status_message_2 = 'Ключ отсутствует к status'
        logger.error(status_message_2)
        raise KeyError(status_message_2)
    if homework_status not in HOMEWORK_STATUSES:
        status_message_3 = 'Неизвестный статус'
        logger.error(status_message_3)
        raise KeyError(status_message_3)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступа по токену"""
    without_tokens = (
        'Остановка запроса из-за остсутствия переменной')
    with_tokens = True
    if TELEGRAM_TOKEN is None:
        with_tokens = False
        logger.critical(
            f'{without_tokens} TELEGRAM_TOKEN')
    if PRACTICUM_TOKEN is None:
        with_tokens = False
        logger.critical(
            f'{without_tokens} PRACTICUM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        with_tokens = False
        logger.critical(f'{without_tokens} TELEGRAM_CHAT_ID')
    return with_tokens


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_response = ''
    while True:
        try:
            logger.debug('Начало проверки')
            response = get_api_answer(ENDPOINT, current_timestamp)
            homeworks = check_response(response)
            if last_response != homeworks[0]:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.info('Нет изменений')
            last_response = homeworks[0]
        except Exception as error:
            logger.error(error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
