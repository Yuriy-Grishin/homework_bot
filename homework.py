import logging
import os
import requests

import telegram
import time
import sys
from dotenv import load_dotenv
import exceptions

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


def send_message(bot, message):
    """Отправка сообщения боту."""
    logger.info('Начало отправки сообщения в Telegram')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение направлено')
    except Exception:
        raise exceptions.MessageNotSentError('Сообщение не направлено')
    else:
        logger.info('Сообщение успешно направлено')


def get_api_answer(current_timestamp):
    """Отправка запроса в Яндекс.Практикум."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.info('Начало запросв к API')
    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        response_json = response.json()
        if response.status_code != 200:
            raise exceptions.Not200Error
        logger.debug('Успешная обработка')
        logger.debug(f'Полуен ответ {response_json}')
        return response.json()
    except Exception:
        raise exceptions.Not200Error


def check_response(response):
    """Проверка запроса."""
    logging.info('Начало проверки запроса')
    if not response:
        raise KeyError('Отсутствует ответ')
    # Если без костыля ниже, то не проходит тест:
    # if not isinstance(response, dict):
    #     raise KeyError('Ответ не в форме словаря')
    if isinstance(response, list) and len(response) == 1:
        response = response[0]
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('В ответе нет homeworks" или "current_date"')
    homeworks = response.get('homeworks', [])
    if not isinstance(homeworks, list):
        raise KeyError('В ответе под ключом "homeworks" не список.'
                       f'response = {response}.')
    return homeworks


def parse_status(homework):
    """Проверка статуса на изменение."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        raise KeyError('Не найдено имя homework')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Не найден статус')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступа по токену."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    message = exit
    if not check_tokens():
        sys.exit(message)
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
        except KeyError as error:
            logger.error(error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
