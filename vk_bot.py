import vk_api
import time
import logging
import threading
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# --- ⚙️ НАСТРОЙКИ ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbFmB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'
GROUP_ID = 237218521
PEER_ID = 2000000001 # ЗАМЕНИ НА ID СВОЕЙ БЕСЕДЫ

MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан казна снять 1364800000"
TRIGGER_INSUFFICIENT_FUNDS = "❌ Недостаточно средств!"
STOP_COMMAND = "/stop_bot"
INTERVAL = 5 # Увеличим интервал, чтобы избежать блокировки
MONITOR_SLEEP = 2 # Задержка для потока мониторинга

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

should_stop = False
last_message_id = 0

def send_message(vk, peer_id, message):
    try:
        vk.messages.send(peer_id=peer_id, message=message, random_id=0)
        logger.info(f"📤 Отправлено: {message}")
        return True # Вернуть успех
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False # Вернуть неудачу

def monitor_chat(vk):
    """
    Поток для мониторинга чата с задержкой.
    """
    global last_message_id, should_stop
    logger.info("👁️‍🗨️ Старт мониторинга чата...")

    while not should_stop:
        try:
            history = vk.messages.getHistory(peer_id=PEER_ID, count=50)
            messages = history.get('items', [])

            for msg in reversed(messages):
                if msg['id'] <= last_message_id:
                    break

                last_message_id = max(last_message_id, msg['id'])
                text = msg.get('text', '')

                if TRIGGER_INSUFFICIENT_FUNDS in text:
                    logger.info("🚨 ТРИГГЕР ОБНАРУЖЕН! Попытка отправки fallback-команды...")
                    success = send_message(vk, PEER_ID, FALLBACK_COMMAND)
                    if not success:
                        logger.warning("⚠️ Не удалось отправить fallback-команду. Повторим позже.")

        except Exception as e:
            error_msg = str(e).lower()
            if "access denied" in error_msg or "[15]" in error_msg:
                logger.warning("⚠️ Нет прав на чтение истории. Повтор через 10 сек.")
                time.sleep(10) # Ждем дольше при ошибке доступа
            else:
                logger.error(f"⚠️ Ошибка при мониторинге: {e}")
                time.sleep(5)
        
        time.sleep(MONITOR_SLEEP) # Обязательная пауза для снижения нагрузки

    logger.info("🔒 Мониторинг чата остановлен.")

def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()

    monitor_thread = threading.Thread(target=monitor_chat, args=(vk,))
    monitor_thread.start()

    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    logger.info("✅ Бот запущен. Мониторинг активен.")

    while not should_stop:
        try:
            send_message(vk, PEER_ID, MAIN_COMMAND)
            
            # Пауза между отправками основной команды
            for _ in range(INTERVAL):
                if should_stop:
                    break

                try:
                    for event in longpoll.check(timeout=1):
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            text = event.obj.message.get('text', '').strip().lower()
                            if text == STOP_COMMAND:
                                should_stop = True
                                send_message(vk, event.obj.message['peer_id'], "🛑 Бот остановлен.")
                                logger.info("🛑 Остановка по команде /stop_bot.")
                except Exception as e:
                    pass # Игнорируем ошибки LongPoll

                time.sleep(1)

        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            time.sleep(INTERVAL * 2) # Пауза дольше при критической ошибке

    should_stop = True
    monitor_thread.join()
    logger.info("🔚 Работа бота завершена.")

if __name__ == '__main__':
    main()
