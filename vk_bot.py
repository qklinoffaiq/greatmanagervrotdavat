import vk_api
import time
import logging
import threading

# --- ⚙️ НАСТРОЙКИ ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'
GROUP_ID = 237218521 
PEER_ID = 2000000001 

MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан казна снять 1364800000"
TRIGGER_INSUFFICIENT_FUNDS = "❌ Недостаточно средств!"
STOP_COMMAND = "/stop_bot"
INTERVAL = 5 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

should_stop = False

def send_message(vk, peer_id, message):
    try:
        vk.messages.send(peer_id=peer_id, message=message, random_id=0)
        logger.info(f"📤 Отправлено: {message}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

# --- НОВЫЙ ПОТОК ДЛЯ ОТПРАВКИ КОМАНД ---
def sender_loop(vk):
    """Поток, который бесконечно отправляет основную команду."""
    global should_stop
    logger.info("📤 Поток отправки команд запущен.")
    while not should_stop:
        send_message(vk, PEER_ID, MAIN_COMMAND)
        # Ждем интервал перед следующей отправкой
        for _ in range(INTERVAL):
            if should_stop:
                break
            time.sleep(1)
    logger.info("📤 Поток отправки команд остановлен.")


def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    
    try:
        vk = vk_session.get_api()
        vk.groups.getById(group_id=GROUP_ID)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: Невалидный токен или ID группы. {e}")
        return

    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    vk = vk_session.get_api()

    logger.info("✅ Бот запущен. Ожидание событий...")

    # --- ЗАПУСКАЕМ ПОТОК ОТПРАВКИ В ПЕРВУЮ ОЧЕРЕДЬ ---
    sender_thread = threading.Thread(target=sender_loop, args=(vk,))
    sender_thread.start()

    # --- ОСНОВНОЙ ПОТОК ТЕПЕРЬ ТОЛЬКО СЛУШАЕТ СОБЫТИЯ ---
    while not should_stop:
        try:
            for event in longpoll.check():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    text = event.obj.message.get('text', '').strip()
                    peer_id_msg = event.obj.message['peer_id']
                    
                    # Реакция на стоп-команду из любого потока
                    if text.lower() == STOP_COMMAND:
                        should_stop = True
                        send_message(vk, peer_id_msg, "🛑 Бот остановлен.")
                        logger.info("🛑 Остановка по команде /stop_bot.")
                    
                    # Реакция на триггер из любого потока
                    if TRIGGER_INSUFFICIENT_FUNDS in text:
                        logger.info("🚨 ТРИГГЕР ОБНАРУЖЕН! Отправка fallback-команды...")
                        send_message(vk, PEER_ID, FALLBACK_COMMAND)

        except Exception as e:
            # Обычно это ошибки сети или таймауты, игнорируем их
            pass

    # Дожидаемся завершения потока отправки перед выходом
    sender_thread.join()
    
    logger.info("🔚 Работа бота завершена.")

if __name__ == '__main__':
    main()
