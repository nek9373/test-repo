import torch
from torch.utils.data import Dataset, DataLoader
import os
import random
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from audio_utils import AudioProcessor, create_synthetic_data


class VocalEnhancementDataset(Dataset):
    """
    Dataset для обучения модели улучшения вокала
    Может работать с парами (зашумленное, чистое) аудио или генерировать синтетические данные
    """
    
    def __init__(self, 
                 clean_audio_dir: str,
                 noisy_audio_dir: Optional[str] = None,
                 sample_rate: int = 16000,
                 chunk_length: int = 32000,
                 overlap: int = 4000,
                 use_synthetic_data: bool = False,
                 noise_types: List[str] = ['white', 'pink', 'brown'],
                 noise_levels: List[float] = [0.05, 0.1, 0.15, 0.2],
                 augmentation: bool = True,
                 max_files: Optional[int] = None):
        """
        Args:
            clean_audio_dir: Папка с чистыми аудио файлами
            noisy_audio_dir: Папка с зашумленными аудио файлами (опционально)
            sample_rate: Частота дискретизации
            chunk_length: Длина чанка для тренировки
            overlap: Перекрытие между чанками
            use_synthetic_data: Использовать синтетические данные
            noise_types: Типы шума для синтетических данных
            noise_levels: Уровни шума для синтетических данных
            augmentation: Использовать аугментацию данных
            max_files: Максимальное количество файлов для загрузки (для тестирования)
        """
        self.clean_audio_dir = Path(clean_audio_dir)
        self.noisy_audio_dir = Path(noisy_audio_dir) if noisy_audio_dir else None
        self.use_synthetic_data = use_synthetic_data
        self.noise_types = noise_types
        self.noise_levels = noise_levels
        self.augmentation = augmentation
        
        # Инициализация аудио процессора
        self.audio_processor = AudioProcessor(
            target_sr=sample_rate,
            chunk_length=chunk_length,
            overlap=overlap
        )
        
        # Поддерживаемые форматы аудио
        self.audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
        
        # Загрузка списка файлов
        self.clean_files = self._get_audio_files(self.clean_audio_dir)
        if max_files:
            self.clean_files = self.clean_files[:max_files]
        
        if self.noisy_audio_dir and not self.use_synthetic_data:
            self.noisy_files = self._get_audio_files(self.noisy_audio_dir)
            if max_files:
                self.noisy_files = self.noisy_files[:max_files]
            
            # Проверяем соответствие файлов
            self._validate_file_pairs()
        else:
            self.noisy_files = None
        
        # Предзагрузка и разделение на чанки
        self.data_chunks = []
        self._prepare_data()
        
        print(f"Загружено {len(self.clean_files)} файлов")
        print(f"Создано {len(self.data_chunks)} чанков для обучения")
    
    def _get_audio_files(self, directory: Path) -> List[Path]:
        """Получение списка аудио файлов из директории"""
        audio_files = []
        for ext in self.audio_extensions:
            audio_files.extend(directory.glob(f"**/*{ext}"))
        return sorted(audio_files)
    
    def _validate_file_pairs(self):
        """Проверка соответствия пар файлов"""
        clean_stems = {f.stem for f in self.clean_files}
        noisy_stems = {f.stem for f in self.noisy_files}
        
        # Находим пересечение
        common_stems = clean_stems & noisy_stems
        
        if not common_stems:
            raise ValueError("Нет соответствующих пар файлов между clean и noisy директориями")
        
        # Фильтруем файлы, оставляя только совпадающие
        self.clean_files = [f for f in self.clean_files if f.stem in common_stems]
        self.noisy_files = [f for f in self.noisy_files if f.stem in common_stems]
        
        print(f"Найдено {len(common_stems)} совпадающих пар файлов")
    
    def _prepare_data(self):
        """Предзагрузка и подготовка данных"""
        for i, clean_file in enumerate(self.clean_files):
            try:
                # Загрузка чистого аудио
                clean_audio, _ = self.audio_processor.load_audio(str(clean_file))
                
                if self.use_synthetic_data:
                    # Создание синтетических данных
                    synthetic_pairs = create_synthetic_data(
                        clean_audio, 
                        noise_types=self.noise_types,
                        noise_levels=self.noise_levels
                    )
                    
                    for noisy_audio, clean_audio_target in synthetic_pairs:
                        # Разделение на чанки
                        clean_chunks = self.audio_processor.split_into_chunks(clean_audio_target)
                        noisy_chunks = self.audio_processor.split_into_chunks(noisy_audio)
                        
                        for clean_chunk, noisy_chunk in zip(clean_chunks, noisy_chunks):
                            self.data_chunks.append((noisy_chunk, clean_chunk))
                
                else:
                    # Использование реальных пар файлов
                    if self.noisy_files:
                        noisy_file = self.noisy_files[i]
                        noisy_audio, _ = self.audio_processor.load_audio(str(noisy_file))
                    else:
                        # Если нет зашумленных файлов, используем чистые как есть
                        noisy_audio = clean_audio
                    
                    # Разделение на чанки
                    clean_chunks = self.audio_processor.split_into_chunks(clean_audio)
                    noisy_chunks = self.audio_processor.split_into_chunks(noisy_audio)
                    
                    for clean_chunk, noisy_chunk in zip(clean_chunks, noisy_chunks):
                        self.data_chunks.append((noisy_chunk, clean_chunk))
                
            except Exception as e:
                print(f"Ошибка при обработке файла {clean_file}: {e}")
                continue
    
    def __len__(self) -> int:
        return len(self.data_chunks)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        noisy_chunk, clean_chunk = self.data_chunks[idx]
        
        # Аугментация данных
        if self.augmentation and random.random() < 0.3:
            noisy_chunk, clean_chunk = self._apply_augmentation(noisy_chunk, clean_chunk)
        
        return noisy_chunk, clean_chunk
    
    def _apply_augmentation(self, noisy: torch.Tensor, clean: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Применение аугментации к аудио данным"""
        # Случайное изменение громкости
        if random.random() < 0.5:
            volume_factor = random.uniform(0.7, 1.3)
            noisy = noisy * volume_factor
            clean = clean * volume_factor
        
        # Добавление дополнительного шума
        if random.random() < 0.3:
            noise_level = random.uniform(0.01, 0.05)
            noise = torch.randn_like(noisy) * noise_level
            noisy = noisy + noise
        
        # Ограничение диапазона
        noisy = torch.clamp(noisy, -1.0, 1.0)
        clean = torch.clamp(clean, -1.0, 1.0)
        
        return noisy, clean


def create_data_loaders(train_clean_dir: str,
                       val_clean_dir: str,
                       train_noisy_dir: Optional[str] = None,
                       val_noisy_dir: Optional[str] = None,
                       batch_size: int = 8,
                       num_workers: int = 4,
                       use_synthetic_data: bool = True,
                       max_files: Optional[int] = None) -> Tuple[DataLoader, DataLoader]:
    """
    Создание data loaders для обучения и валидации
    
    Args:
        train_clean_dir: Папка с чистыми аудио для обучения
        val_clean_dir: Папка с чистыми аудио для валидации
        train_noisy_dir: Папка с зашумленными аудио для обучения (опционально)
        val_noisy_dir: Папка с зашумленными аудио для валидации (опционально)
        batch_size: Размер батча
        num_workers: Количество воркеров для загрузки данных
        use_synthetic_data: Использовать синтетические данные
        max_files: Максимальное количество файлов (для тестирования)
        
    Returns:
        Tuple[DataLoader, DataLoader]: (train_loader, val_loader)
    """
    
    # Создание datasets
    train_dataset = VocalEnhancementDataset(
        clean_audio_dir=train_clean_dir,
        noisy_audio_dir=train_noisy_dir,
        use_synthetic_data=use_synthetic_data,
        augmentation=True,
        max_files=max_files
    )
    
    val_dataset = VocalEnhancementDataset(
        clean_audio_dir=val_clean_dir,
        noisy_audio_dir=val_noisy_dir,
        use_synthetic_data=use_synthetic_data,
        augmentation=False,
        max_files=max_files
    )
    
    # Создание data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False
    )
    
    return train_loader, val_loader


class AudioCollator:
    """Кастомный collator для батчей аудио данных"""
    
    def __init__(self, pad_to_length: Optional[int] = None):
        self.pad_to_length = pad_to_length
    
    def __call__(self, batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Объединение батча аудио данных
        
        Args:
            batch: Список кортежей (noisy_audio, clean_audio)
            
        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (батч_noisy, батч_clean)
        """
        noisy_audios, clean_audios = zip(*batch)
        
        # Если указана целевая длина, подгоняем все аудио к этой длине
        if self.pad_to_length:
            noisy_audios = [self._pad_or_trim(audio, self.pad_to_length) for audio in noisy_audios]
            clean_audios = [self._pad_or_trim(audio, self.pad_to_length) for audio in clean_audios]
        
        # Стэкинг в батч
        noisy_batch = torch.stack(noisy_audios, dim=0)
        clean_batch = torch.stack(clean_audios, dim=0)
        
        return noisy_batch, clean_batch
    
    def _pad_or_trim(self, audio: torch.Tensor, target_length: int) -> torch.Tensor:
        """Подгонка аудио к целевой длине"""
        current_length = audio.shape[-1]
        
        if current_length == target_length:
            return audio
        elif current_length < target_length:
            # Паддинг
            padding = target_length - current_length
            return torch.nn.functional.pad(audio, (0, padding), mode='constant', value=0)
        else:
            # Обрезка
            return audio[..., :target_length]


if __name__ == "__main__":
    # Создание тестовых данных
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Создание тестовых аудио файлов
    sample_rate = 16000
    duration = 2.0
    
    for i in range(5):
        # Создание тестового синусоидального сигнала
        t = torch.linspace(0, duration, int(sample_rate * duration))
        freq = 440 + i * 100  # Разные частоты
        audio = torch.sin(2 * np.pi * freq * t).unsqueeze(0)
        
        # Сохранение
        import torchaudio
        torchaudio.save(test_dir / f"test_audio_{i}.wav", audio, sample_rate)
    
    # Тестирование dataset
    dataset = VocalEnhancementDataset(
        clean_audio_dir=str(test_dir),
        use_synthetic_data=True,
        max_files=3
    )
    
    print(f"Размер dataset: {len(dataset)}")
    
    # Тестирование data loader
    train_loader, val_loader = create_data_loaders(
        train_clean_dir=str(test_dir),
        val_clean_dir=str(test_dir),
        batch_size=2,
        num_workers=0,
        max_files=2
    )
    
    # Получение одного батча
    for noisy_batch, clean_batch in train_loader:
        print(f"Размер noisy батча: {noisy_batch.shape}")
        print(f"Размер clean батча: {clean_batch.shape}")
        break
    
    # Удаление тестовых файлов
    import shutil
    shutil.rmtree(test_dir)