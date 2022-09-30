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
    HomeworkStatusNotFound, TelegramMessageError
)

load_dotenv()

logger = logging.getLogger(__name__)


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
        logger.info('Бот отправил сообщение {}'.format(message))
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as exc:
        logger.exception('Сбой при отправке сообщения в Telegram')
        raise TelegramMessageError from exc


def get_api_answer(current_timestamp: int) -> Dict[str, Any]:
    """Запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        logger.info('Отправлен запрос к эндпоинту {}'.format(ENDPOINT))
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if api_answer.status_code != HTTPStatus.OK:
            logger.exception(
                'Ошибка сервера. Код ответа API: {}'.format(
                    api_answer.status_code
                )
            )
            raise PraktikumApiError

    except Exception as exc:
        logger.exception(
            'Cбой в работе программы: {}.'.format(exc)
        )
        raise PraktikumApiError from exc

    return api_answer.json()


def check_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка валидности ответа API."""
    if not isinstance(response, dict):
        logger.exception('Некорректнный ответ API')
        raise ResponseTypeError

    if 'homeworks' not in response or 'current_date' not in response:
        logger.exception('В ответе API отсутствуют ожидаемые ключи')
        raise ResponseKeysError

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logger.exception(
            'Не обнаружен список домашних работ под ключом "homeworks"'
        )
        raise HomeworksTypeError

    return homeworks


def parse_status(homework: Dict[str, Any]) -> str:
    """Обработка статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if 'homework_name' not in homework:
        logger.exception(
            'В ответе API не обнаружен ключ'
            'homework_name'
        )
        raise HomeworkNameNotFound

    if homework_status not in HOMEWORK_STATUSES:
        logger.exception(
            'В ответе API обнаружен недокументированный'
            'статус домашней работы'
        )
        raise HomeworkStatusNotFound

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности токенов."""
    available_tokens = all([
        TELEGRAM_TOKEN,
        PRACTICUM_TOKEN,
        TELEGRAM_CHAT_ID,
    ])
    return available_tokens


def main() -> None:
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stdout
    )

    if not check_tokens:
        logger.critical(
            'Отсутствуют обязательные переменные окружения'
        )
        raise TokensNotFound

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            if not homeworks:
                logger.debug('В ответе отсутствуют новые статусы')

            for homework in homeworks:
                message = parse_status(homework)
                if last_message != message:
                    last_message = message
                    send_message(bot, message)

            current_timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

            logger.exception(message)

            if last_message != message:
                last_message = message
                send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
