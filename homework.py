"""Отслеживание статуса домашних работ с помощью телеграм-бота."""

import os
import sys
import time
import requests
import telegram
import logging

from typing import Any, Dict, List
from dotenv import load_dotenv
from http import HTTPStatus
from exceptions import (
    TokensNotFound, PraktikumApiError, ResponseTypeError,
    ResponseKeysError, HomeworksTypeError, HomeworkNameNotFound,
    HomeworkStatusNotFound
)

load_dotenv()

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)

handler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


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


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Бот отправил сообщение {}'.format(message))
    except Exception:
        logger.exception('Сбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp: int) -> Dict[str, Any]:
    """Запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if api_answer.status_code != HTTPStatus.OK:
        logger.exception(
            'Ошибка сервера. Код ответа API: {}'.format(api_answer.status_code)
        )
        raise PraktikumApiError

    return api_answer.json()


def check_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка валидности ответа API."""
    if type(response) is not dict:
        logger.exception('Некорректнный ответ API')
        raise ResponseTypeError
    if 'homeworks' in response and 'current_date' in response:
        homeworks = response.get('homeworks')
        if type(homeworks) is not list:
            logger.exception(
                'Не обнаружен список домашних работ под ключом "homeworks"'
            )
            raise HomeworksTypeError
    else:
        logger.exception('В ответе API отсутствуют ожидаемые ключи')
        raise ResponseKeysError
    return homeworks


def parse_status(homework: Dict[str, Any]) -> str:
    """Обработка статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        logger.exception(
            'В ответе API не обнаружен ключ'
            'homework_name'
        )
        raise HomeworkNameNotFound

    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        logger.exception(
            'В ответе API обнаружен недокументированный'
            'статус домашней работы'
        )
        raise HomeworkStatusNotFound

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности токенов."""
    unavailable_tokens = set()
    if not TELEGRAM_TOKEN:
        unavailable_tokens.add('TELEGRAM_TOKEN')
    if not PRACTICUM_TOKEN:
        unavailable_tokens.add('PRACTICUM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        unavailable_tokens.add('TELEGRAM_CHAT_ID')
    if not unavailable_tokens:
        return True
    else:
        logger.critical(
            'Отсутствуют обязательные переменные окружения: {}'.format(
                ', '.join(unavailable_tokens)
            )
        )
        return False


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens:
        raise TokensNotFound

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if not homeworks:
                logger.debug('В ответе отсутствуют новые статусы')

            for homework in homeworks:
                send_message(bot, parse_status(homework))

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

            if last_error_message != message:
                last_error_message = message
                send_message(bot, message)

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
