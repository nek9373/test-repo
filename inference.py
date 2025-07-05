import torch
import argparse
import json
import time
from pathlib import Path
from tqdm import tqdm
import numpy as np

from vocal_enhancer import VocalEnhancer
from audio_utils import AudioProcessor


class VocalEnhancerInference:
    """Класс для инференса модели улучшения вокала"""
    
    def __init__(self, model_path: str, device: str = None):
        """
        Args:
            model_path: Путь к обученной модели
            device: Устройство для вычислений ('cpu', 'cuda', 'auto')
        """
        # Определение устройства
        if device is None or device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Используется устройство: {self.device}")
        
        # Загрузка модели
        self.model, self.config = self.load_model(model_path)
        
        # Создание аудио процессора
        self.audio_processor = AudioProcessor(
            target_sr=self.config.get('sample_rate', 16000),
            chunk_length=self.config.get('chunk_length', 32000),
            overlap=self.config.get('overlap', 4000)
        )
        
        print(f"Модель загружена и готова к использованию")
    
    def load_model(self, model_path: str):
        """Загрузка модели и конфигурации"""
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Получение конфигурации
        config = checkpoint.get('config', {})
        
        # Создание модели
        model = VocalEnhancer(
            n_channels=config.get('model_channels', 64),
            n_layers=config.get('model_layers', 4),
            dropout=config.get('model_dropout', 0.1)
        ).to(self.device)
        
        # Загрузка весов
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        
        print(f"Модель загружена с эпохи {checkpoint['epoch']}")
        print(f"Лучшая val loss: {checkpoint['best_val_loss']:.6f}")
        
        return model, config
    
    def enhance_file(self, input_path: str, output_path: str, batch_size: int = 1):
        """
        Улучшение одного аудио файла
        
        Args:
            input_path: Путь к входному файлу
            output_path: Путь к выходному файлу
            batch_size: Размер батча для обработки чанков
        """
        print(f"Обработка файла: {input_path}")
        
        # Загрузка аудио
        audio, sample_rate = self.audio_processor.load_audio(input_path)
        print(f"Загружено аудио: {audio.shape}, SR: {sample_rate}")
        
        # Разделение на чанки
        chunks = self.audio_processor.split_into_chunks(audio)
        print(f"Разделено на {len(chunks)} чанков")
        
        # Обработка чанков батчами
        enhanced_chunks = []
        
        with torch.no_grad():
            for i in tqdm(range(0, len(chunks), batch_size), desc="Обработка чанков"):
                batch_chunks = chunks[i:i+batch_size]
                
                # Создание батча
                batch = torch.stack(batch_chunks).to(self.device)
                
                # Инференс
                enhanced_batch = self.model(batch)
                
                # Добавление результатов
                for j in range(enhanced_batch.shape[0]):
                    enhanced_chunks.append(enhanced_batch[j].cpu())
        
        # Объединение чанков
        enhanced_audio = self.audio_processor.merge_chunks(enhanced_chunks)
        print(f"Объединено в аудио: {enhanced_audio.shape}")
        
        # Сохранение результата
        self.audio_processor.save_audio(enhanced_audio, output_path, sample_rate)
        print(f"Результат сохранен: {output_path}")
    
    def enhance_directory(self, input_dir: str, output_dir: str, 
                         batch_size: int = 1, recursive: bool = True):
        """
        Улучшение всех аудио файлов в директории
        
        Args:
            input_dir: Папка с входными файлами
            output_dir: Папка для выходных файлов
            batch_size: Размер батча
            recursive: Обрабатывать поддиректории
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Поиск аудио файлов
        audio_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
        
        if recursive:
            audio_files = []
            for ext in audio_extensions:
                audio_files.extend(input_path.rglob(f"*{ext}"))
        else:
            audio_files = []
            for ext in audio_extensions:
                audio_files.extend(input_path.glob(f"*{ext}"))
        
        print(f"Найдено {len(audio_files)} аудио файлов")
        
        # Обработка каждого файла
        for audio_file in tqdm(audio_files, desc="Обработка файлов"):
            try:
                # Определение пути выходного файла
                relative_path = audio_file.relative_to(input_path)
                output_file = output_path / relative_path.with_suffix('.wav')
                
                # Создание директории если необходимо
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Обработка файла
                self.enhance_file(str(audio_file), str(output_file), batch_size)
                
            except Exception as e:
                print(f"Ошибка при обработке {audio_file}: {e}")
                continue
    
    def enhance_realtime(self, input_path: str, output_path: str = None):
        """
        Улучшение в реальном времени с возможностью прослушивания
        
        Args:
            input_path: Путь к входному файлу
            output_path: Путь к выходному файлу (опционально)
        """
        try:
            import sounddevice as sd
            import threading
            import queue
        except ImportError:
            print("Для реального времени нужна библиотека sounddevice: pip install sounddevice")
            return
        
        # Загрузка аудио
        audio, sample_rate = self.audio_processor.load_audio(input_path)
        
        # Разделение на чанки
        chunks = self.audio_processor.split_into_chunks(audio)
        
        # Очередь для обработанных чанков
        audio_queue = queue.Queue()
        
        def process_chunks():
            """Обработка чанков в отдельном потоке"""
            with torch.no_grad():
                for chunk in chunks:
                    batch = chunk.unsqueeze(0).to(self.device)
                    enhanced = self.model(batch)
                    audio_queue.put(enhanced.squeeze(0).cpu().numpy())
        
        # Запуск обработки в отдельном потоке
        process_thread = threading.Thread(target=process_chunks)
        process_thread.start()
        
        # Воспроизведение обработанного аудио
        played_chunks = []
        
        while process_thread.is_alive() or not audio_queue.empty():
            try:
                chunk = audio_queue.get(timeout=0.1)
                played_chunks.append(chunk)
                
                # Воспроизведение чанка
                if chunk.ndim > 1:
                    chunk = chunk.squeeze()
                sd.play(chunk, sample_rate)
                sd.wait()
                
            except queue.Empty:
                continue
        
        # Сохранение результата если указан путь
        if output_path:
            enhanced_audio = torch.cat([torch.from_numpy(chunk) for chunk in played_chunks])
            self.audio_processor.save_audio(enhanced_audio, output_path, sample_rate)
            print(f"Результат сохранен: {output_path}")
    
    def compare_audio(self, original_path: str, enhanced_path: str):
        """
        Сравнение оригинального и улучшенного аудио
        
        Args:
            original_path: Путь к оригинальному файлу
            enhanced_path: Путь к улучшенному файлу
        """
        # Загрузка аудио
        original, sr1 = self.audio_processor.load_audio(original_path)
        enhanced, sr2 = self.audio_processor.load_audio(enhanced_path)
        
        # Вычисление характеристик
        original_features = self.audio_processor.compute_spectral_features(original)
        enhanced_features = self.audio_processor.compute_spectral_features(enhanced)
        
        print("\nСравнение характеристик:")
        print("-" * 50)
        for key in original_features.keys():
            if isinstance(original_features[key], np.ndarray):
                orig_val = np.mean(original_features[key])
                enh_val = np.mean(enhanced_features[key])
            else:
                orig_val = original_features[key]
                enh_val = enhanced_features[key]
            
            print(f"{key}:")
            print(f"  Оригинал: {orig_val:.4f}")
            print(f"  Улучшено: {enh_val:.4f}")
            print(f"  Изменение: {((enh_val - orig_val) / orig_val * 100):.2f}%")
        
        # Визуализация
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Формы волны
        axes[0, 0].plot(original.squeeze().numpy())
        axes[0, 0].set_title('Оригинальная форма волны')
        axes[0, 0].set_xlabel('Отсчеты')
        axes[0, 0].set_ylabel('Амплитуда')
        
        axes[0, 1].plot(enhanced.squeeze().numpy())
        axes[0, 1].set_title('Улучшенная форма волны')
        axes[0, 1].set_xlabel('Отсчеты')
        axes[0, 1].set_ylabel('Амплитуда')
        
        # Спектрограммы
        import librosa
        
        orig_spec = librosa.stft(original.squeeze().numpy())
        enh_spec = librosa.stft(enhanced.squeeze().numpy())
        
        orig_db = librosa.amplitude_to_db(np.abs(orig_spec), ref=np.max)
        enh_db = librosa.amplitude_to_db(np.abs(enh_spec), ref=np.max)
        
        im1 = axes[1, 0].imshow(orig_db, aspect='auto', origin='lower')
        axes[1, 0].set_title('Оригинальная спектрограмма')
        axes[1, 0].set_xlabel('Время')
        axes[1, 0].set_ylabel('Частота')
        plt.colorbar(im1, ax=axes[1, 0])
        
        im2 = axes[1, 1].imshow(enh_db, aspect='auto', origin='lower')
        axes[1, 1].set_title('Улучшенная спектрограмма')
        axes[1, 1].set_xlabel('Время')
        axes[1, 1].set_ylabel('Частота')
        plt.colorbar(im2, ax=axes[1, 1])
        
        plt.tight_layout()
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Инференс модели улучшения вокала')
    parser.add_argument('--model', type=str, required=True, 
                       help='Путь к обученной модели')
    parser.add_argument('--input', type=str, required=True,
                       help='Путь к входному файлу или директории')
    parser.add_argument('--output', type=str, required=True,
                       help='Путь к выходному файлу или директории')
    parser.add_argument('--batch_size', type=int, default=4,
                       help='Размер батча для обработки')
    parser.add_argument('--device', type=str, default='auto',
                       choices=['cpu', 'cuda', 'auto'],
                       help='Устройство для вычислений')
    parser.add_argument('--recursive', action='store_true',
                       help='Обрабатывать поддиректории')
    parser.add_argument('--realtime', action='store_true',
                       help='Воспроизведение в реальном времени')
    parser.add_argument('--compare', action='store_true',
                       help='Сравнить с оригиналом')
    
    args = parser.parse_args()
    
    # Создание инференса
    enhancer = VocalEnhancerInference(args.model, args.device)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Определение режима работы
    if input_path.is_file():
        # Обработка одного файла
        if args.realtime:
            enhancer.enhance_realtime(str(input_path), str(output_path))
        else:
            enhancer.enhance_file(str(input_path), str(output_path), args.batch_size)
        
        # Сравнение если запрошено
        if args.compare:
            enhancer.compare_audio(str(input_path), str(output_path))
    
    elif input_path.is_dir():
        # Обработка директории
        enhancer.enhance_directory(str(input_path), str(output_path), 
                                 args.batch_size, args.recursive)
    
    else:
        print(f"Путь {input_path} не найден")


if __name__ == "__main__":
    main()