import vk_api
import time
import logging
import threading
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# --- ⚙️ НАСТРОЙКИ (ЗАПОЛНЕНО) ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'
GROUP_ID = 237218521
PEER_ID = 2000000001 # ЗАМЕНИ НА ID СВОЕЙ БЕСЕДЫ

MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан казна снять 1364800000"
TRIGGER_INSUFFICIENT_FUNDS = "❌ Недостаточно средств!"
STOP_COMMAND = "/stop_bot"
INTERVAL = 2
# -----------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Глобальный флаг для остановки потоков
should_stop = False

def send_message(vk, peer_id, message):
    """Отправляет сообщение в беседу."""
    try:
        vk.messages.send(peer_id=peer_id, message=message, random_id=0)
        logger.info(f"📤 Отправлено: {message}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")

def sender_thread_func(vk):
    """Поток, который отправляет сообщения по таймеру."""
    global should_stop
    logger.info("🕰️ Поток отправителя запущен.")
    while not should_stop:
        send_message(vk, PEER_ID, MAIN_COMMAND)
        # Ждём интервал перед следующей отправкой
        for _ in range(INTERVAL):
            if should_stop:
                break
            time.sleep(1)
    logger.info("🛑 Поток отправителя остановлен.")

def listener_thread_func(vk_session):
    """Поток, который слушает входящие сообщения."""
    global should_stop
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    logger.info("👂 Поток слушателя запущен. Ожидаю сообщений...")
    
    try:
        for event in longpoll.listen():
            if should_stop:
                break

            if event.type == VkBotEventType.MESSAGE_NEW:
                text = event.obj.message['text']
                current_peer_id = event.obj.message['peer_id']
                logger.info(f"📩 Получено сообщение: {text}")

                # Реакция на триггер
                if TRIGGER_INSUFFICIENT_FUNDS in text:
                    send_message(vk_session.get_api(), current_peer_id, FALLBACK_COMMAND)

                # Реакция на команду остановки
                if text.strip().lower() == STOP_COMMAND:
                    logger.info("🛑 Получена команда остановки.")
                    should_stop = True # Установим флаг для остановки всех потоков

    except Exception as e:
        if not should_stop: # Если это не запланированная остановка
            logger.error(f"⚠️ Ошибка в слушателе: {e}")
    finally:
        logger.info("🔚 Поток слушателя завершил работу.")

def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()

    # Создаём потоки
    sender_thread = threading.Thread(target=sender_thread_func, args=(vk,))
    listener_thread = threading.Thread(target=listener_thread_func, args=(vk_session,))

    # Запускаем потоки
    sender_thread.start()
    listener_thread.start()

    logger.info("✅ Бот запущен. Работают два потока.")

    # Главный поток ждёт завершения работы потоков
    try:
        sender_thread.join()
        listener_thread.join()
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по Ctrl+C...")
        should_stop = True # Установим флаг для остановки

if __name__ == '__main__':
    main()
