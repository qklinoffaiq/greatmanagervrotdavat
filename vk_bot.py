import vk_api
import time
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# --- ⚙️ НАСТРОЙКИ (ЗАПОЛНЕНО ПО ВАШЕМУ ЗАПРОСУ) ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'
GROUP_ID = 237218521

PEER_ID = 2000000001  # 🛑 ЗАМЕНИТЕ НА ID ВАШЕЙ БЕСЕДЫ

MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан снять 1364800000"
TRIGGER_INSUFFICIENT_FUNDS = "❌ Недостаточно средств!" # ТРИГГЕР ОБНОВЛЕН
STOP_COMMAND = "/stop_bot"
INTERVAL = 2
# -----------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

should_stop = False

def send_message(vk, peer_id, message):
    """Отправляет сообщение в беседу."""
    try:
        vk.messages.send(peer_id=peer_id, message=message, random_id=0)
        logger.info(f"📤 Отправлено: {message}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

    logger.info("✅ Бот запущен.")

    while not should_stop:
        try:
            # 1. Отправляем основную команду
            send_message(vk, PEER_ID, MAIN_COMMAND)

            # 2. Ждём INTERVAL секунд, проверяя входящие сообщения
            for _ in range(INTERVAL):
                if should_stop:
                    break

                try:
                    for event in longpoll.check():
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            text = event.obj.message['text'].strip()
                            current_peer_id = event.obj.message['peer_id']

                            # Если пришло сообщение о недостатке средств — отправляем fallback
                            if TRIGGER_INSUFFICIENT_FUNDS in text:
                                send_message(vk, current_peer_id, FALLBACK_COMMAND)

                            # Если команда на остановку — завершаем работу
                            if text.lower() == STOP_COMMAND:
                                should_stop = True
                                send_message(vk, current_peer_id, "🛑 Бот остановлен.")
                                logger.info("🛑 Бот остановлен по команде.")
                                break # Выходим из цикла по событиям
                except Exception as e:
                    logger.error(f"⚠️ Ошибка проверки событий: {e}")

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен вручную (Ctrl+C).")
            should_stop = True
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
            time.sleep(INTERVAL) # Пауза перед повтором после сбоя

    logger.info("🔚 Работа бота завершена.")

if __name__ == '__main__':
    main()
