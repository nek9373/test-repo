#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех компонентов системы улучшения вокала
"""

import torch
import numpy as np
import sys
import traceback
from pathlib import Path
import tempfile
import shutil
import json

def test_imports():
    """Тестирование импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        from vocal_enhancer import VocalEnhancer, VocalEnhancerLoss, count_parameters
        print("✅ vocal_enhancer импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта vocal_enhancer: {e}")
        return False
    
    try:
        from audio_utils import AudioProcessor, create_synthetic_data
        print("✅ audio_utils импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта audio_utils: {e}")
        return False
    
    try:
        from dataset import VocalEnhancementDataset, create_data_loaders
        print("✅ dataset импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта dataset: {e}")
        return False
    
    return True


def test_model_architecture():
    """Тестирование архитектуры модели"""
    print("\n🏗️ Тестирование архитектуры модели...")
    
    try:
        from vocal_enhancer import VocalEnhancer, VocalEnhancerLoss, count_parameters
        
        # Создание модели
        model = VocalEnhancer(n_channels=32, n_layers=3, dropout=0.1)
        print(f"✅ Модель создана с {count_parameters(model):,} параметрами")
        
        # Тестовый вход
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        batch_size = 2
        seq_length = 16000
        x = torch.randn(batch_size, 1, seq_length).to(device)
        
        # Прямой проход
        with torch.no_grad():
            output = model(x)
        
        if output.shape == x.shape:
            print(f"✅ Прямой проход успешен: {x.shape} -> {output.shape}")
        else:
            print(f"❌ Неверная форма выхода: {x.shape} -> {output.shape}")
            return False
        
        # Тестирование функции потерь
        criterion = VocalEnhancerLoss()
        target = torch.randn_like(output)
        loss, loss_dict = criterion(output, target)
        
        print(f"✅ Функция потерь работает: {loss.item():.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования модели: {e}")
        traceback.print_exc()
        return False


def test_audio_processing():
    """Тестирование обработки аудио"""
    print("\n🎵 Тестирование обработки аудио...")
    
    try:
        from audio_utils import AudioProcessor, create_synthetic_data
        
        # Создание процессора
        processor = AudioProcessor(target_sr=16000, chunk_length=16000)
        
        # Создание тестового аудио
        duration = 2.0
        sample_rate = 16000
        t = torch.linspace(0, duration, int(sample_rate * duration))
        test_audio = torch.sin(2 * np.pi * 440 * t).unsqueeze(0)
        
        print(f"✅ Создано тестовое аудио: {test_audio.shape}")
        
        # Разделение на чанки
        chunks = processor.split_into_chunks(test_audio)
        print(f"✅ Разделено на {len(chunks)} чанков")
        
        # Объединение чанков
        merged = processor.merge_chunks(chunks)
        print(f"✅ Объединено обратно: {merged.shape}")
        
        # Создание синтетических данных
        synthetic_data = create_synthetic_data(test_audio, noise_levels=[0.1])
        print(f"✅ Создано {len(synthetic_data)} синтетических пар")
        
        # Вычисление характеристик
        features = processor.compute_spectral_features(test_audio)
        print(f"✅ Вычислены спектральные характеристики: {list(features.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования аудио: {e}")
        traceback.print_exc()
        return False


def test_dataset():
    """Тестирование dataset"""
    print("\n📦 Тестирование dataset...")
    
    try:
        from dataset import VocalEnhancementDataset, create_data_loaders
        import torchaudio
        
        # Создание временной директории
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создание тестовых аудио файлов
            sample_rate = 16000
            duration = 1.0
            
            for i in range(3):
                t = torch.linspace(0, duration, int(sample_rate * duration))
                freq = 440 + i * 100
                audio = torch.sin(2 * np.pi * freq * t).unsqueeze(0)
                
                audio_path = temp_path / f"test_audio_{i}.wav"
                torchaudio.save(str(audio_path), audio, sample_rate)
            
            print(f"✅ Создано 3 тестовых аудио файла")
            
            # Создание dataset
            dataset = VocalEnhancementDataset(
                clean_audio_dir=str(temp_path),
                use_synthetic_data=True,
                max_files=3
            )
            
            print(f"✅ Dataset создан с {len(dataset)} образцами")
            
            # Получение одного образца
            noisy, clean = dataset[0]
            print(f"✅ Получен образец: noisy={noisy.shape}, clean={clean.shape}")
            
            # Создание data loaders
            train_loader, val_loader = create_data_loaders(
                train_clean_dir=str(temp_path),
                val_clean_dir=str(temp_path),
                batch_size=2,
                num_workers=0,
                max_files=2
            )
            
            # Получение батча
            for batch in train_loader:
                noisy_batch, clean_batch = batch
                print(f"✅ Получен батч: noisy={noisy_batch.shape}, clean={clean_batch.shape}")
                break
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования dataset: {e}")
        traceback.print_exc()
        return False


def test_training_loop():
    """Тестирование цикла обучения"""
    print("\n🏋️ Тестирование цикла обучения...")
    
    try:
        from vocal_enhancer import VocalEnhancer, VocalEnhancerLoss
        from dataset import create_data_loaders
        import torch.optim as optim
        import torchaudio
        
        # Создание временной директории
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создание тестовых аудио файлов
            sample_rate = 16000
            duration = 1.0
            
            for i in range(5):
                t = torch.linspace(0, duration, int(sample_rate * duration))
                freq = 440 + i * 100
                audio = torch.sin(2 * np.pi * freq * t).unsqueeze(0)
                
                audio_path = temp_path / f"test_audio_{i}.wav"
                torchaudio.save(str(audio_path), audio, sample_rate)
            
            # Создание модели и компонентов
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = VocalEnhancer(n_channels=32, n_layers=2).to(device)
            criterion = VocalEnhancerLoss()
            optimizer = optim.Adam(model.parameters(), lr=1e-3)
            
            # Создание data loaders
            train_loader, val_loader = create_data_loaders(
                train_clean_dir=str(temp_path),
                val_clean_dir=str(temp_path),
                batch_size=2,
                num_workers=0,
                max_files=3
            )
            
            print(f"✅ Компоненты обучения созданы")
            
            # Одна итерация обучения
            model.train()
            for batch_idx, (noisy_batch, clean_batch) in enumerate(train_loader):
                if batch_idx >= 2:  # Только 2 батча для теста
                    break
                
                noisy_batch = noisy_batch.to(device)
                clean_batch = clean_batch.to(device)
                
                optimizer.zero_grad()
                enhanced_batch = model(noisy_batch)
                loss, loss_dict = criterion(enhanced_batch, clean_batch)
                loss.backward()
                optimizer.step()
                
                print(f"✅ Батч {batch_idx + 1}: Loss = {loss.item():.4f}")
            
            # Валидация
            model.eval()
            with torch.no_grad():
                for batch_idx, (noisy_batch, clean_batch) in enumerate(val_loader):
                    if batch_idx >= 1:  # Только 1 батч для теста
                        break
                    
                    noisy_batch = noisy_batch.to(device)
                    clean_batch = clean_batch.to(device)
                    
                    enhanced_batch = model(noisy_batch)
                    loss, loss_dict = criterion(enhanced_batch, clean_batch)
                    
                    print(f"✅ Валидация: Loss = {loss.item():.4f}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования обучения: {e}")
        traceback.print_exc()
        return False


def test_inference():
    """Тестирование инференса"""
    print("\n🔮 Тестирование инференса...")
    
    try:
        from vocal_enhancer import VocalEnhancer
        from audio_utils import AudioProcessor
        import torchaudio
        
        # Создание временной директории
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создание тестового аудио файла
            sample_rate = 16000
            duration = 2.0
            t = torch.linspace(0, duration, int(sample_rate * duration))
            audio = torch.sin(2 * np.pi * 440 * t).unsqueeze(0)
            
            input_path = temp_path / "test_input.wav"
            output_path = temp_path / "test_output.wav"
            
            torchaudio.save(str(input_path), audio, sample_rate)
            print(f"✅ Создан тестовый аудио файл")
            
            # Создание и "обучение" модели
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = VocalEnhancer(n_channels=32, n_layers=2).to(device)
            model.eval()
            
            # Создание чекпоинта
            checkpoint = {
                'epoch': 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': {},
                'best_val_loss': 0.5,
                'config': {
                    'model_channels': 32,
                    'model_layers': 2,
                    'model_dropout': 0.1,
                    'sample_rate': 16000,
                    'chunk_length': 16000,
                    'overlap': 4000
                }
            }
            
            model_path = temp_path / "test_model.pt"
            torch.save(checkpoint, model_path)
            print(f"✅ Сохранен тестовый чекпоинт")
            
            # Симуляция инференса
            audio_processor = AudioProcessor(target_sr=16000, chunk_length=16000)
            
            # Загрузка аудио
            audio, sr = audio_processor.load_audio(str(input_path))
            print(f"✅ Загружено аудио: {audio.shape}")
            
            # Разделение на чанки
            chunks = audio_processor.split_into_chunks(audio)
            print(f"✅ Разделено на {len(chunks)} чанков")
            
            # Обработка чанков
            enhanced_chunks = []
            with torch.no_grad():
                for chunk in chunks:
                    batch = chunk.unsqueeze(0).to(device)
                    enhanced = model(batch)
                    enhanced_chunks.append(enhanced.squeeze(0).cpu())
            
            # Объединение результатов
            enhanced_audio = audio_processor.merge_chunks(enhanced_chunks)
            print(f"✅ Объединено в аудио: {enhanced_audio.shape}")
            
            # Сохранение результата
            audio_processor.save_audio(enhanced_audio, str(output_path), sr)
            print(f"✅ Результат сохранен: {output_path}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования инференса: {e}")
        traceback.print_exc()
        return False


def test_dependencies():
    """Тестирование зависимостей"""
    print("\n📚 Тестирование зависимостей...")
    
    dependencies = {
        'torch': 'PyTorch',
        'torchaudio': 'TorchAudio',
        'librosa': 'LibROSA',
        'numpy': 'NumPy',
        'scipy': 'SciPy',
        'matplotlib': 'Matplotlib',
        'tqdm': 'tqdm',
        'soundfile': 'SoundFile'
    }
    
    missing_deps = []
    
    for dep, name in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {name} доступен")
        except ImportError:
            print(f"❌ {name} не найден")
            missing_deps.append(name)
    
    if missing_deps:
        print(f"\n⚠️ Отсутствуют зависимости: {', '.join(missing_deps)}")
        print("Установите их с помощью: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы улучшения вокала")
    print("=" * 60)
    
    tests = [
        ("Зависимости", test_dependencies),
        ("Импорты", test_imports),
        ("Архитектура модели", test_model_architecture),
        ("Обработка аудио", test_audio_processing),
        ("Dataset", test_dataset),
        ("Цикл обучения", test_training_loop),
        ("Инференс", test_inference)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: Критическая ошибка - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования:")
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"📈 Успешность: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 Все тесты пройдены! Система готова к использованию.")
        return True
    else:
        print(f"\n⚠️ Обнаружены проблемы. Проверьте ошибки выше.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)