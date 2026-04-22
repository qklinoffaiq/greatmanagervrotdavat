import vk_api
import time
import logging
import threading

# --- ⚙️ НАСТРОЙКИ ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'
GROUP_ID = 237218521
PEER_ID = 2000000001 # ЗАМЕНИ НА ID СВОЕЙ БЕСЕДЫ

MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан казна снять 1364800000"
TRIGGER_INSUFFICIENT_FUNDS = "❌ Недостаточно средств!"
STOP_COMMAND = "/stop_bot"
INTERVAL = 2 # Интервал основной команды

# --- ВАРИАНТ 1: БЫСТРЫЙ (рекомендуемый) ---
# Проверяет историю только когда пришло новое событие.
# Очень быстрый, не нагружает API.

# --- ВАРИАНТ 2: УЛЬТРА-НАДЕЖНЫЙ ---
# Постоянно опрашивает историю чата (например, раз в 3-5 секунд).
# Работает всегда, даже если права бота ограничены.
# Немного больше нагрузка на API.
USE_ULTRA_RELIABLE_MODE = True # Переключатель режимов
HISTORY_POLL_INTERVAL = 5 # Интервал опроса истории в секундах (для Варианта 2)
# -----------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

should_stop = False
last_message_id = 0 # Для отслеживания новых сообщений

def send_message(vk, peer_id, message):
    """Отправляет сообщение в беседу."""
    try:
        vk.messages.send(peer_id=peer_id, message=message, random_id=0)
        logger.info(f"📤 Отправлено: {message}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")

def monitor_chat(vk):
    """
    Поток, который постоянно следит за чатом.
    Это самый надежный способ не пропустить триггер.
    """
    global last_message_id, should_stop
    logger.info("👁️‍🗨️ Старт мониторинга чата...")

    while not should_stop:
        try:
            # Получаем историю последних сообщений (например, 50 штук)
            # start_message_id=0 означает с самого последнего
            history = vk.messages.getHistory(peer_id=PEER_ID, count=50)
            messages = history.get('items', [])

            # Проверяем сообщения в обратном порядке (от новых к старым)
            for msg in reversed(messages):
                # Если это сообщение мы уже проверяли - пропускаем остальные
                if msg['id'] <= last_message_id:
                    break

                # Обновляем ID последнего проверенного сообщения
                last_message_id = max(last_message_id, msg['id'])

                # Проверяем текст на наличие триггера
                text = msg.get('text', '')
                if TRIGGER_INSUFFICIENT_FUNDS in text:
                    logger.info("🚨 ТРИГГЕР ОБНАРУЖЕН! Отправка fallback-команды...")
                    send_message(vk, PEER_ID, FALLBACK_COMMAND)
                    # Не выходим из цикла, чтобы продолжить мониторинг

        except Exception as e:
            logger.error(f"⚠️ Ошибка при мониторинге: {e}")
        
        # Если включен ультра-надежный режим, спим и повторяем опрос
        if USE_ULTRA_RELIABLE_MODE:
            time.sleep(HISTORY_POLL_INTERVAL)
        else:
            # В быстром режиме мы не спим здесь,
            # а ждем событий от LongPoll (см. main цикл)
            time.sleep(1)

    logger.info("🔒 Мониторинг чата остановлен.")

def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()

    # Запускаем поток мониторинга чата ПЕРВЫМ
    monitor_thread = threading.Thread(target=monitor_chat, args=(vk,))
    monitor_thread.start()

    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    logger.info("✅ Бот запущен. Мониторинг активен.")

    while not should_stop:
        try:
            # Отправляем основную команду по таймеру
            send_message(vk, PEER_ID, MAIN_COMMAND)
            
            # Ждем интервал или команду остановки
            for _ in range(INTERVAL):
                if should_stop:
                    break

                # Проверяем входящие команды (например, /stop_bot)
                # Используем check с таймаутом 1 секунда, чтобы не зависать
                try:
                    for event in longpoll.check(timeout=1):
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            text = event.obj.message.get('text', '').strip().lower()
                            if text == STOP_COMMAND:
                                should_stop = True
                                send_message(vk, event.obj.message['peer_id'], "🛑 Бот остановлен.")
                                logger.info("🛑 Остановка по команде /stop_bot.")
                            # Здесь можно добавить и другие команды управления
                except Exception as e:
                    # Иногда возникает ошибка "Read timed out", это нормально при timeout=1
                    pass

                time.sleep(1)

        except Exception as e:
            logger.error(f"💥 Критическая ошибка в основном цикле: {e}")
            time.sleep(INTERVAL) # Пауза перед повтором после сбоя

    # Ожидаем завершения потока мониторинга перед выходом
    should_stop = True
    monitor_thread.join()
    logger.info("🔚 Работа бота завершена.")

if __name__ == '__main__':
    main()
