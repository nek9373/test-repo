import torch
import torchaudio
import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Tuple, Optional, List


class AudioProcessor:
    """
    Класс для обработки аудио файлов для задач улучшения вокала
    """
    
    def __init__(self, 
                 target_sr: int = 16000,
                 chunk_length: int = 32000,  # 2 секунды при 16kHz
                 overlap: int = 4000,        # 0.25 секунды перекрытия
                 normalize: bool = True):
        """
        Args:
            target_sr: Целевая частота дискретизации
            chunk_length: Длина чанка для обработки
            overlap: Перекрытие между чанками
            normalize: Нормализовать аудио или нет
        """
        self.target_sr = target_sr
        self.chunk_length = chunk_length
        self.overlap = overlap
        self.normalize = normalize
    
    def load_audio(self, file_path: str) -> Tuple[torch.Tensor, int]:
        """
        Загрузка аудио файла
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Tuple[torch.Tensor, int]: (аудио_данные, частота_дискретизации)
        """
        try:
            # Попытка загрузки с помощью torchaudio
            audio, sr = torchaudio.load(file_path)
            
            # Конвертация в моно если стерео
            if audio.shape[0] > 1:
                audio = torch.mean(audio, dim=0, keepdim=True)
            
            # Ресемплинг до целевой частоты
            if sr != self.target_sr:
                resampler = torchaudio.transforms.Resample(sr, self.target_sr)
                audio = resampler(audio)
            
            # Нормализация
            if self.normalize:
                audio = self._normalize_audio(audio)
            
            return audio, self.target_sr
            
        except Exception as e:
            # Fallback на librosa
            try:
                audio, sr = librosa.load(file_path, sr=self.target_sr, mono=True)
                audio = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
                
                if self.normalize:
                    audio = self._normalize_audio(audio)
                
                return audio, self.target_sr
                
            except Exception as e2:
                raise ValueError(f"Не удалось загрузить аудио файл {file_path}: {e2}")
    
    def save_audio(self, audio: torch.Tensor, file_path: str, sample_rate: int = None):
        """
        Сохранение аудио файла
        
        Args:
            audio: Аудио данные
            file_path: Путь для сохранения
            sample_rate: Частота дискретизации
        """
        if sample_rate is None:
            sample_rate = self.target_sr
        
        # Убираем лишние размерности
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        # Денормализация если необходимо
        audio = torch.clamp(audio, -1.0, 1.0)
        
        # Сохранение
        torchaudio.save(file_path, audio.unsqueeze(0), sample_rate)
    
    def _normalize_audio(self, audio: torch.Tensor) -> torch.Tensor:
        """Нормализация аудио к диапазону [-1, 1]"""
        max_val = torch.max(torch.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def split_into_chunks(self, audio: torch.Tensor) -> List[torch.Tensor]:
        """
        Разделение аудио на чанки с перекрытием
        
        Args:
            audio: Входное аудио
            
        Returns:
            List[torch.Tensor]: Список чанков
        """
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)
        
        audio_length = audio.shape[1]
        chunks = []
        
        start = 0
        while start < audio_length:
            end = min(start + self.chunk_length, audio_length)
            chunk = audio[:, start:end]
            
            # Паддинг если чанк короче требуемого
            if chunk.shape[1] < self.chunk_length:
                padding = self.chunk_length - chunk.shape[1]
                chunk = torch.nn.functional.pad(chunk, (0, padding), mode='constant', value=0)
            
            chunks.append(chunk)
            
            # Если это последний чанк, выходим
            if end >= audio_length:
                break
                
            start += self.chunk_length - self.overlap
        
        return chunks
    
    def merge_chunks(self, chunks: List[torch.Tensor]) -> torch.Tensor:
        """
        Объединение чанков в одно аудио с учетом перекрытия
        
        Args:
            chunks: Список чанков
            
        Returns:
            torch.Tensor: Объединенное аудио
        """
        if not chunks:
            return torch.zeros(1, 0)
        
        if len(chunks) == 1:
            return chunks[0]
        
        # Рассчитываем общую длину
        step = self.chunk_length - self.overlap
        total_length = (len(chunks) - 1) * step + self.chunk_length
        
        # Создаем выходной тензор
        output = torch.zeros(1, total_length)
        weights = torch.zeros(1, total_length)
        
        # Создаем окно для сглаживания переходов
        window = torch.hann_window(self.overlap * 2)
        
        for i, chunk in enumerate(chunks):
            start = i * step
            end = start + self.chunk_length
            
            # Обрезаем чанк если он выходит за границы
            if end > total_length:
                chunk = chunk[:, :total_length-start]
                end = total_length
            
            # Применяем окно для сглаживания
            if i > 0:  # Не первый чанк
                fade_in = window[:self.overlap]
                chunk[:, :self.overlap] *= fade_in
            
            if i < len(chunks) - 1:  # Не последний чанк
                fade_out = window[self.overlap:]
                chunk[:, -self.overlap:] *= fade_out
            
            # Добавляем к выходному сигналу
            output[:, start:end] += chunk[:, :end-start]
            weights[:, start:end] += 1.0
        
        # Нормализация по весам
        weights = torch.clamp(weights, min=1e-8)
        output = output / weights
        
        return output
    
    def add_noise(self, audio: torch.Tensor, noise_level: float = 0.01) -> torch.Tensor:
        """
        Добавление шума к аудио для аугментации данных
        
        Args:
            audio: Входное аудио
            noise_level: Уровень шума (0.0 - 1.0)
            
        Returns:
            torch.Tensor: Аудио с шумом
        """
        noise = torch.randn_like(audio) * noise_level
        return audio + noise
    
    def time_stretch(self, audio: torch.Tensor, rate: float) -> torch.Tensor:
        """
        Изменение скорости воспроизведения без изменения тона
        
        Args:
            audio: Входное аудио
            rate: Коэффициент изменения скорости (> 1.0 ускоряет, < 1.0 замедляет)
            
        Returns:
            torch.Tensor: Измененное аудио
        """
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        # Используем librosa для time stretching
        audio_np = audio.numpy()
        stretched = librosa.effects.time_stretch(audio_np, rate=rate)
        
        return torch.tensor(stretched, dtype=torch.float32).unsqueeze(0)
    
    def pitch_shift(self, audio: torch.Tensor, n_steps: float) -> torch.Tensor:
        """
        Изменение тона аудио
        
        Args:
            audio: Входное аудио
            n_steps: Количество полутонов для сдвига
            
        Returns:
            torch.Tensor: Аудио с измененным тоном
        """
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        # Используем librosa для pitch shifting
        audio_np = audio.numpy()
        shifted = librosa.effects.pitch_shift(audio_np, sr=self.target_sr, n_steps=n_steps)
        
        return torch.tensor(shifted, dtype=torch.float32).unsqueeze(0)
    
    def compute_spectral_features(self, audio: torch.Tensor) -> dict:
        """
        Вычисление спектральных характеристик аудио
        
        Args:
            audio: Входное аудио
            
        Returns:
            dict: Словарь с характеристиками
        """
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        audio_np = audio.numpy()
        
        # Спектральный центроид
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_np, sr=self.target_sr)
        
        # Спектральная полоса пропускания
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_np, sr=self.target_sr)
        
        # Спектральный роллофф
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_np, sr=self.target_sr)
        
        # MFCC
        mfccs = librosa.feature.mfcc(y=audio_np, sr=self.target_sr, n_mfcc=13)
        
        return {
            'spectral_centroid': np.mean(spectral_centroids),
            'spectral_bandwidth': np.mean(spectral_bandwidth),
            'spectral_rolloff': np.mean(spectral_rolloff),
            'mfcc_mean': np.mean(mfccs, axis=1),
            'mfcc_std': np.std(mfccs, axis=1)
        }
    
    def plot_waveform(self, audio: torch.Tensor, title: str = "Waveform", save_path: str = None):
        """
        Визуализация формы волны
        
        Args:
            audio: Аудио данные
            title: Заголовок графика
            save_path: Путь для сохранения (опционально)
        """
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        plt.figure(figsize=(12, 4))
        time_axis = np.linspace(0, len(audio) / self.target_sr, len(audio))
        plt.plot(time_axis, audio.numpy())
        plt.title(title)
        plt.xlabel('Время (с)')
        plt.ylabel('Амплитуда')
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
    
    def plot_spectrogram(self, audio: torch.Tensor, title: str = "Spectrogram", save_path: str = None):
        """
        Визуализация спектрограммы
        
        Args:
            audio: Аудио данные
            title: Заголовок графика
            save_path: Путь для сохранения (опционально)
        """
        if audio.dim() > 1:
            audio = audio.squeeze()
        
        # Вычисляем спектрограмму
        D = librosa.stft(audio.numpy())
        DB = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        
        plt.figure(figsize=(12, 6))
        librosa.display.specshow(DB, sr=self.target_sr, x_axis='time', y_axis='hz')
        plt.colorbar(format='%+2.0f dB')
        plt.title(title)
        plt.xlabel('Время (с)')
        plt.ylabel('Частота (Гц)')
        
        if save_path:
            plt.savefig(save_path)
        plt.show()


def create_synthetic_data(clean_audio: torch.Tensor, 
                         noise_types: List[str] = ['white', 'pink', 'brown'],
                         noise_levels: List[float] = [0.1, 0.2, 0.3]) -> List[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Создание синтетических данных для обучения
    
    Args:
        clean_audio: Чистое аудио
        noise_types: Типы шума
        noise_levels: Уровни шума
        
    Returns:
        List[Tuple[torch.Tensor, torch.Tensor]]: Список пар (зашумленное, чистое)
    """
    data_pairs = []
    
    for noise_type in noise_types:
        for noise_level in noise_levels:
            # Генерация шума
            if noise_type == 'white':
                noise = torch.randn_like(clean_audio) * noise_level
            elif noise_type == 'pink':
                # Простая аппроксимация розового шума
                noise = torch.randn_like(clean_audio) * noise_level
                # Применяем фильтр для получения розового шума
                noise = torch.nn.functional.conv1d(
                    noise.unsqueeze(1), 
                    torch.tensor([[[0.1, 0.2, 0.4, 0.2, 0.1]]]), 
                    padding=2
                ).squeeze(1)
            elif noise_type == 'brown':
                # Браунов шум (интеграл белого шума)
                noise = torch.randn_like(clean_audio) * noise_level
                noise = torch.cumsum(noise, dim=-1)
                noise = noise / torch.max(torch.abs(noise)) * noise_level
            
            # Создание зашумленного аудио
            noisy_audio = clean_audio + noise
            
            # Ограничиваем диапазон
            noisy_audio = torch.clamp(noisy_audio, -1.0, 1.0)
            
            data_pairs.append((noisy_audio, clean_audio))
    
    return data_pairs


if __name__ == "__main__":
    # Тестирование AudioProcessor
    processor = AudioProcessor(target_sr=16000, chunk_length=16000)
    
    # Создаем тестовый сигнал
    duration = 3.0  # 3 секунды
    sample_rate = 16000
    t = torch.linspace(0, duration, int(sample_rate * duration))
    
    # Синусоида 440 Гц (нота A4)
    test_audio = torch.sin(2 * np.pi * 440 * t).unsqueeze(0)
    
    print(f"Тестовый сигнал: {test_audio.shape}")
    
    # Разделение на чанки
    chunks = processor.split_into_chunks(test_audio)
    print(f"Количество чанков: {len(chunks)}")
    
    # Объединение чанков
    merged = processor.merge_chunks(chunks)
    print(f"Объединенный сигнал: {merged.shape}")
    
    # Вычисление спектральных характеристик
    features = processor.compute_spectral_features(test_audio)
    print("Спектральные характеристики:")
    for key, value in features.items():
        if isinstance(value, np.ndarray):
            print(f"  {key}: {value.shape}")
        else:
            print(f"  {key}: {value:.4f}")
    
    # Создание синтетических данных
    synthetic_data = create_synthetic_data(test_audio, noise_levels=[0.1, 0.2])
    print(f"Создано {len(synthetic_data)} пар синтетических данных")