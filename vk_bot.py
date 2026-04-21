import vk_api
import time
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'  # Замените на ваш токен группы
PEER_ID = 2000000001  # Замените на ID беседы (peer_id)

# Интервал отправки (в секундах)
INTERVAL = 2

# Сообщение для отправки
MESSAGE = "/клан казна положить 100000"

# Флаг для остановки бота
should_stop = False


def send_message(vk, peer_id, message):
    """Отправляет сообщение в беседу."""
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=message,
            random_id=0  # Генерация нового random_id при каждом вызове
        )
        logger.info(f"Сообщение отправлено: {message}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return False


def main():
    global should_stop

    # Авторизация через токен группы
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()

    longpoll = VkBotLongPoll(vk_session, group_id=237218521)  # Укажите реальный ID группы (число)
    logger.info("Бот запущен. Ожидание команд...")

    while not should_stop:
        try:
            # Попробуем отправить сообщение
            if send_message(vk, PEER_ID, MESSAGE):
                pass  # Успешно отправлено
            
            # Ждём INTERVAL секунд перед следующей отправкой
            for _ in range(INTERVAL):
                if should_stop:
                    break
                time.sleep(1)

            # Проверим, не пришло ли сообщение для остановки
            for event in longpoll.check():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    text = event.obj.message['text'].strip()
                    if text.lower() == '/stop_bot':
                        should_stop = True
                        send_message(vk, event.obj.message['peer_id'], "Бот остановлен.")
                        logger.info("Бот остановлен по команде.")
                        break

        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(INTERVAL)  # Пауза перед повторной попыткой

    logger.info("Работа бота завершена.")


if __name__ == '__main__':
    main()
