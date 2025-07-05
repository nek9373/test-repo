# Нейросеть для улучшения вокала (WAV to WAV)

Этот проект представляет собой нейросеть на PyTorch для улучшения качества вокала в wav файлах. Модель использует архитектуру U-Net с механизмами внимания и остаточными блоками для эффективного улучшения аудиосигналов.

## Особенности

- **Архитектура U-Net**: Эффективная архитектура для задач улучшения аудио
- **Механизмы внимания**: Фокусировка на важных частях аудиосигнала
- **Остаточные блоки**: Улучшенное обучение глубоких сетей
- **Комбинированная функция потерь**: L1, MSE и спектральные потери
- **Синтетические данные**: Возможность обучения на синтетически зашумленных данных
- **Пакетная обработка**: Обработка чанков аудио батчами для эффективности
- **Реальное время**: Возможность обработки в реальном времени

## Архитектура модели

```
VocalEnhancer:
├── Входная свертка (1 → 64 каналов)
├── Энкодер (5 уровней)
│   ├── ConvBlock + ResidualBlock + AttentionBlock
│   └── MaxPooling
├── Bottleneck (2 остаточных блока)
├── Декодер (5 уровней)
│   ├── ConvTranspose + Skip Connection
│   └── ConvBlock + ResidualBlock + AttentionBlock
└── Выходная свертка (64 → 1 канал)
```

## Установка

1. Клонировать репозиторий:
```bash
git clone <repo-url>
cd vocal-enhancer
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Обучение модели

#### Базовое обучение с синтетическими данными:
```bash
python train.py --train_clean_dir data/clean --val_clean_dir data/clean --epochs 100
```

#### Обучение с реальными парами файлов:
```bash
python train.py \
  --train_clean_dir data/train/clean \
  --val_clean_dir data/val/clean \
  --train_noisy_dir data/train/noisy \
  --val_noisy_dir data/val/noisy \
  --epochs 100 \
  --batch_size 8 \
  --lr 1e-4
```

#### Продолжение обучения с чекпоинта:
```bash
python train.py --resume checkpoints/best_model.pt --epochs 50
```

### Инференс (улучшение аудио)

#### Обработка одного файла:
```bash
python inference.py --model checkpoints/best_model.pt --input audio.wav --output enhanced_audio.wav
```

#### Обработка директории:
```bash
python inference.py \
  --model checkpoints/best_model.pt \
  --input input_folder \
  --output output_folder \
  --recursive \
  --batch_size 4
```

#### Сравнение с оригиналом:
```bash
python inference.py \
  --model checkpoints/best_model.pt \
  --input original.wav \
  --output enhanced.wav \
  --compare
```

#### Обработка в реальном времени:
```bash
python inference.py \
  --model checkpoints/best_model.pt \
  --input audio.wav \
  --output enhanced.wav \
  --realtime
```

## Структура проекта

```
vocal-enhancer/
├── vocal_enhancer.py    # Основная архитектура модели
├── audio_utils.py       # Утилиты для обработки аудио
├── dataset.py          # Dataset для загрузки данных
├── train.py           # Скрипт обучения
├── inference.py       # Скрипт инференса
├── requirements.txt   # Зависимости
└── README.md         # Документация
```

## Параметры модели

### Архитектура:
- `n_channels`: Базовое количество каналов (по умолчанию: 64)
- `n_layers`: Количество слоев энкодера/декодера (по умолчанию: 4)
- `dropout`: Коэффициент dropout (по умолчанию: 0.1)

### Аудио:
- `sample_rate`: Частота дискретизации (по умолчанию: 16000 Гц)
- `chunk_length`: Длина чанка для обработки (по умолчанию: 32000 отсчетов)
- `overlap`: Перекрытие между чанками (по умолчанию: 4000 отсчетов)

### Обучение:
- `batch_size`: Размер батча (по умолчанию: 8)
- `learning_rate`: Скорость обучения (по умолчанию: 1e-4)
- `num_epochs`: Количество эпох (по умолчанию: 100)

## Функция потерь

Модель использует комбинированную функцию потерь:
- **L1 Loss**: Средняя абсолютная ошибка
- **MSE Loss**: Среднеквадратичная ошибка
- **Spectral Loss**: Потеря в частотной области (STFT)

## Типы данных

### Синтетические данные:
- Белый шум
- Розовый шум
- Коричневый шум
- Различные уровни шума (0.05-0.2)

### Реальные данные:
- Пары файлов (зашумленное, чистое)
- Поддерживаемые форматы: WAV, MP3, FLAC, OGG, M4A

## Мониторинг обучения

Используется TensorBoard для отслеживания:
- Потери обучения и валидации
- Градиенты и веса модели
- Скорость обучения

Запуск TensorBoard:
```bash
tensorboard --logdir logs
```

## Примеры использования

### Тестирование модели:
```bash
# Тестирование архитектуры
python vocal_enhancer.py

# Тестирование обработки аудио
python audio_utils.py

# Тестирование dataset
python dataset.py
```

### Быстрый старт:
```bash
# 1. Создать папку с аудио файлами
mkdir -p data/clean
# Поместить ваши wav файлы в data/clean/

# 2. Обучить модель
python train.py --train_clean_dir data/clean --val_clean_dir data/clean --epochs 50 --max_files 10

# 3. Использовать модель
python inference.py --model checkpoints/best_model.pt --input your_audio.wav --output enhanced_audio.wav
```

## Системные требования

- Python 3.7+
- PyTorch 2.0+
- CUDA (опционально, для GPU)
- Минимум 8GB RAM
- Для обучения: 16GB+ RAM, GPU с 8GB+ VRAM

## Производительность

Типичная производительность на различном оборудовании:
- **CPU Intel i7**: ~10x медленнее реального времени
- **GPU RTX 3080**: ~5x быстрее реального времени
- **GPU RTX 4090**: ~10x быстрее реального времени

## Лицензия

MIT License - см. LICENSE файл для деталей.

## Вклад в проект

Приветствуются пулл-реквесты и issues. Перед внесением изменений, пожалуйста, ознакомьтесь с существующим кодом и следуйте принятому стилю кодирования.
