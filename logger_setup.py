import logging
import colorlog

# Налаштування форматування та кольорів для логування
log_colors = {
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
    'SUCCESS': 'bold_green'  # Додаємо новий рівень SUCCESS
}

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors=log_colors
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('balance_checker_logger')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Додаємо кастомний рівень SUCCESS
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

# Функція для отримання логера
def get_logger():
    return logger