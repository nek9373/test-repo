import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
import os
import argparse
import json
import time
from pathlib import Path
from tqdm import tqdm
import numpy as np

from vocal_enhancer import VocalEnhancer, VocalEnhancerLoss, count_parameters
from dataset import create_data_loaders
from audio_utils import AudioProcessor


class Trainer:
    """Класс для обучения модели улучшения вокала"""
    
    def __init__(self, 
                 model: nn.Module,
                 train_loader,
                 val_loader,
                 criterion,
                 optimizer,
                 device: torch.device,
                 config: dict):
        
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        self.config = config
        
        # Создание директорий для логов и чекпоинтов
        self.log_dir = Path(config['log_dir'])
        self.checkpoint_dir = Path(config['checkpoint_dir'])
        self.log_dir.mkdir(exist_ok=True)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Инициализация TensorBoard
        self.writer = SummaryWriter(log_dir=self.log_dir)
        
        # Переменные для отслеживания прогресса
        self.epoch = 0
        self.best_val_loss = float('inf')
        self.train_losses = []
        self.val_losses = []
        
        # Загрузка чекпоинта если указан
        if config.get('resume_from_checkpoint'):
            self.load_checkpoint(config['resume_from_checkpoint'])
    
    def train_epoch(self):
        """Обучение одной эпохи"""
        self.model.train()
        epoch_losses = []
        
        progress_bar = tqdm(self.train_loader, desc=f"Эпоха {self.epoch + 1}")
        
        for batch_idx, (noisy_batch, clean_batch) in enumerate(progress_bar):
            # Перенос данных на устройство
            noisy_batch = noisy_batch.to(self.device)
            clean_batch = clean_batch.to(self.device)
            
            # Очистка градиентов
            self.optimizer.zero_grad()
            
            # Прямой проход
            enhanced_batch = self.model(noisy_batch)
            
            # Вычисление потерь
            loss, loss_dict = self.criterion(enhanced_batch, clean_batch)
            
            # Обратное распространение
            loss.backward()
            
            # Обрезка градиентов
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 
                                         max_norm=self.config['grad_clip_norm'])
            
            # Обновление весов
            self.optimizer.step()
            
            # Сохранение потерь
            epoch_losses.append(loss.item())
            
            # Обновление прогресс-бара
            progress_bar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'L1': f"{loss_dict['l1_loss']:.4f}",
                'MSE': f"{loss_dict['mse_loss']:.4f}",
                'Spectral': f"{loss_dict['spectral_loss']:.4f}"
            })
            
            # Логирование в TensorBoard
            global_step = self.epoch * len(self.train_loader) + batch_idx
            self.writer.add_scalar('Train/Loss', loss.item(), global_step)
            self.writer.add_scalar('Train/L1_Loss', loss_dict['l1_loss'], global_step)
            self.writer.add_scalar('Train/MSE_Loss', loss_dict['mse_loss'], global_step)
            self.writer.add_scalar('Train/Spectral_Loss', loss_dict['spectral_loss'], global_step)
            
            # Периодическое логирование градиентов
            if batch_idx % 100 == 0:
                self.log_gradients(global_step)
        
        return np.mean(epoch_losses)
    
    def validate_epoch(self):
        """Валидация одной эпохи"""
        self.model.eval()
        epoch_losses = []
        
        with torch.no_grad():
            progress_bar = tqdm(self.val_loader, desc="Валидация")
            
            for batch_idx, (noisy_batch, clean_batch) in enumerate(progress_bar):
                # Перенос данных на устройство
                noisy_batch = noisy_batch.to(self.device)
                clean_batch = clean_batch.to(self.device)
                
                # Прямой проход
                enhanced_batch = self.model(noisy_batch)
                
                # Вычисление потерь
                loss, loss_dict = self.criterion(enhanced_batch, clean_batch)
                
                # Сохранение потерь
                epoch_losses.append(loss.item())
                
                # Обновление прогресс-бара
                progress_bar.set_postfix({
                    'Val Loss': f"{loss.item():.4f}",
                    'L1': f"{loss_dict['l1_loss']:.4f}",
                    'MSE': f"{loss_dict['mse_loss']:.4f}",
                    'Spectral': f"{loss_dict['spectral_loss']:.4f}"
                })
        
        return np.mean(epoch_losses)
    
    def train(self):
        """Основной цикл обучения"""
        print(f"Начинаем обучение с эпохи {self.epoch + 1}")
        print(f"Всего эпох: {self.config['num_epochs']}")
        print(f"Модель содержит {count_parameters(self.model):,} параметров")
        
        for epoch in range(self.epoch, self.config['num_epochs']):
            self.epoch = epoch
            
            # Обучение
            train_loss = self.train_epoch()
            self.train_losses.append(train_loss)
            
            # Валидация
            val_loss = self.validate_epoch()
            self.val_losses.append(val_loss)
            
            # Логирование в TensorBoard
            self.writer.add_scalar('Epoch/Train_Loss', train_loss, epoch)
            self.writer.add_scalar('Epoch/Val_Loss', val_loss, epoch)
            self.writer.add_scalar('Learning_Rate', 
                                 self.optimizer.param_groups[0]['lr'], epoch)
            
            # Вывод результатов эпохи
            print(f"Эпоха {epoch + 1}/{self.config['num_epochs']}")
            print(f"Train Loss: {train_loss:.6f}")
            print(f"Val Loss: {val_loss:.6f}")
            print(f"Learning Rate: {self.optimizer.param_groups[0]['lr']:.2e}")
            print("-" * 50)
            
            # Сохранение лучшей модели
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.save_checkpoint(is_best=True)
                print(f"Новая лучшая модель сохранена! Val Loss: {val_loss:.6f}")
            
            # Регулярное сохранение чекпоинта
            if (epoch + 1) % self.config['save_interval'] == 0:
                self.save_checkpoint()
            
            # Обновление learning rate
            if hasattr(self.optimizer, 'step') and 'scheduler' in self.config:
                self.scheduler.step(val_loss)
        
        print("Обучение завершено!")
        self.writer.close()
    
    def save_checkpoint(self, is_best=False):
        """Сохранение чекпоинта"""
        checkpoint = {
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_loss': self.best_val_loss,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'config': self.config
        }
        
        # Сохранение обычного чекпоинта
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{self.epoch + 1}.pt"
        torch.save(checkpoint, checkpoint_path)
        
        # Сохранение лучшей модели
        if is_best:
            best_path = self.checkpoint_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
    
    def load_checkpoint(self, checkpoint_path):
        """Загрузка чекпоинта"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epoch = checkpoint['epoch']
        self.best_val_loss = checkpoint['best_val_loss']
        self.train_losses = checkpoint['train_losses']
        self.val_losses = checkpoint['val_losses']
        
        print(f"Чекпоинт загружен с эпохи {self.epoch + 1}")
        print(f"Лучшая val loss: {self.best_val_loss:.6f}")
    
    def log_gradients(self, global_step):
        """Логирование градиентов в TensorBoard"""
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                self.writer.add_histogram(f'Gradients/{name}', param.grad, global_step)
                self.writer.add_scalar(f'Gradient_Norm/{name}', 
                                     param.grad.norm().item(), global_step)


def create_config():
    """Создание конфигурации по умолчанию"""
    return {
        # Модель
        'model_channels': 64,
        'model_layers': 4,
        'model_dropout': 0.1,
        
        # Обучение
        'num_epochs': 100,
        'batch_size': 8,
        'learning_rate': 1e-4,
        'weight_decay': 1e-5,
        'grad_clip_norm': 1.0,
        
        # Функция потерь
        'l1_weight': 1.0,
        'mse_weight': 1.0,
        'spectral_weight': 0.5,
        
        # Данные
        'train_clean_dir': 'data/train/clean',
        'val_clean_dir': 'data/val/clean',
        'train_noisy_dir': None,
        'val_noisy_dir': None,
        'use_synthetic_data': True,
        'num_workers': 4,
        'max_files': None,
        
        # Аудио
        'sample_rate': 16000,
        'chunk_length': 32000,
        'overlap': 4000,
        
        # Сохранение
        'log_dir': 'logs',
        'checkpoint_dir': 'checkpoints',
        'save_interval': 10,
        'resume_from_checkpoint': None
    }


def main():
    parser = argparse.ArgumentParser(description='Обучение модели улучшения вокала')
    parser.add_argument('--config', type=str, help='Путь к файлу конфигурации JSON')
    parser.add_argument('--train_clean_dir', type=str, help='Папка с чистыми аудио для обучения')
    parser.add_argument('--val_clean_dir', type=str, help='Папка с чистыми аудио для валидации')
    parser.add_argument('--resume', type=str, help='Путь к чекпоинту для продолжения обучения')
    parser.add_argument('--epochs', type=int, default=100, help='Количество эпох')
    parser.add_argument('--batch_size', type=int, default=8, help='Размер батча')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--max_files', type=int, help='Максимальное количество файлов (для тестирования)')
    
    args = parser.parse_args()
    
    # Загрузка конфигурации
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        config = create_config()
    
    # Обновление конфигурации из аргументов командной строки
    if args.train_clean_dir:
        config['train_clean_dir'] = args.train_clean_dir
    if args.val_clean_dir:
        config['val_clean_dir'] = args.val_clean_dir
    if args.resume:
        config['resume_from_checkpoint'] = args.resume
    if args.epochs:
        config['num_epochs'] = args.epochs
    if args.batch_size:
        config['batch_size'] = args.batch_size
    if args.lr:
        config['learning_rate'] = args.lr
    if args.max_files:
        config['max_files'] = args.max_files
    
    # Определение устройства
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Используется устройство: {device}")
    
    # Создание модели
    model = VocalEnhancer(
        n_channels=config['model_channels'],
        n_layers=config['model_layers'],
        dropout=config['model_dropout']
    ).to(device)
    
    # Создание data loaders
    train_loader, val_loader = create_data_loaders(
        train_clean_dir=config['train_clean_dir'],
        val_clean_dir=config['val_clean_dir'],
        train_noisy_dir=config.get('train_noisy_dir'),
        val_noisy_dir=config.get('val_noisy_dir'),
        batch_size=config['batch_size'],
        num_workers=config['num_workers'],
        use_synthetic_data=config['use_synthetic_data'],
        max_files=config.get('max_files')
    )
    
    # Создание функции потерь
    criterion = VocalEnhancerLoss(
        l1_weight=config['l1_weight'],
        mse_weight=config['mse_weight'],
        spectral_weight=config['spectral_weight']
    )
    
    # Создание оптимизатора
    optimizer = optim.AdamW(
        model.parameters(),
        lr=config['learning_rate'],
        weight_decay=config['weight_decay']
    )
    
    # Планировщик learning rate
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=10, factor=0.5, verbose=True
    )
    
    # Сохранение конфигурации
    config_path = Path(config['checkpoint_dir']) / 'config.json'
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Создание и запуск тренера
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        config=config
    )
    
    # Добавление планировщика
    trainer.scheduler = scheduler
    
    # Обучение
    trainer.train()


if __name__ == "__main__":
    main()