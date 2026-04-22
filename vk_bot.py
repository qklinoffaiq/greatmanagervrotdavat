import vk_api
import time
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

# --- ⚙️ НАСТРОЙКИ БОТА (ИЗМЕНИТЕ ПОД СЕБЯ) ⚙️ ---
GROUP_TOKEN = 'vk1.a.63gRKaofhLXxItbjXWRcbNVwOsjxuMM8lq2wfge5nLscGQ4CPK6VbaU3loh1UPbNE2rjxt3vcDoaOjc2KFaShDfYKFldqUz2J3qVVilyj_stqbnNGE2NqRwYxY8DkU3StollkCK3cOvi-dixk92XSiI8OtNOmH_zmbF2mB3EShA4bBhmmrYhQwmUm7uyvujlkIQIJX2V8q_Dd2V45yzKJw'  # Токен группы VK
GROUP_ID = 237218521             # ID вашей группы (число)
PEER_ID = 2000000001             # ID беседы (peer_id), куда писать

# Основные команды
MAIN_COMMAND = "/клан казна положить 10000000"
FALLBACK_COMMAND = "/клан снять 1364800000"

# Триггер для fallback-команды
TRIGGER_INSUFFICIENT_FUNDS = "❌Недостаточно Средств"

# Интервал между отправками (в секундах)
INTERVAL = 2

# Команда для остановки бота
STOP_COMMAND = "/stop_bot"
# -------------------------------------------

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

should_stop = False

def send_message(vk, peer_id, message):
    """Отправляет сообщение в беседу."""
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=message,
            random_id=0
        )
        logger.info(f"📤 Отправлено: {message}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке: {e}")
        return False

def main():
    global should_stop

    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()

    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)
    logger.info("✅ Бот запущен. Ожидание событий...")

    while not should_stop:
        try:
            # Отправляем основную команду
            send_message(vk, PEER_ID, MAIN_COMMAND)

            # Ждём INTERVAL секунд, проверяя входящие сообщения
            for _ in range(INTERVAL):
                if should_stop:
                    break

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
