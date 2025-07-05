import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class ConvBlock(nn.Module):
    """Базовый блок свертки с нормализацией и активацией"""
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1, dropout=0.1):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size, stride, padding)
        self.bn = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.dropout(x)
        return x


class ResidualBlock(nn.Module):
    """Остаточный блок для лучшего обучения глубоких сетей"""
    def __init__(self, channels, kernel_size=3, dropout=0.1):
        super(ResidualBlock, self).__init__()
        self.conv1 = ConvBlock(channels, channels, kernel_size, dropout=dropout)
        self.conv2 = nn.Conv1d(channels, channels, kernel_size, padding=kernel_size//2)
        self.bn = nn.BatchNorm1d(channels)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        residual = x
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.bn(x)
        x = self.dropout(x)
        x = x + residual
        return F.relu(x)


class AttentionBlock(nn.Module):
    """Механизм внимания для фокусировки на важных частях аудио"""
    def __init__(self, channels):
        super(AttentionBlock, self).__init__()
        self.conv = nn.Conv1d(channels, 1, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        attention = self.conv(x)
        attention = self.sigmoid(attention)
        return x * attention


class VocalEnhancer(nn.Module):
    """
    U-Net архитектура для улучшения вокала в wav файлах
    
    Архитектура:
    - Энкодер: постепенное уменьшение разрешения с увеличением каналов
    - Декодер: постепенное увеличение разрешения с уменьшением каналов
    - Skip connections для сохранения деталей
    - Attention механизм для фокусировки на важных частях
    """
    
    def __init__(self, n_channels=64, n_layers=5, dropout=0.1):
        super(VocalEnhancer, self).__init__()
        
        self.n_layers = n_layers
        
        # Входная свертка
        self.input_conv = ConvBlock(1, n_channels, kernel_size=7, padding=3, dropout=dropout)
        
        # Энкодер
        self.encoder_blocks = nn.ModuleList()
        self.encoder_pools = nn.ModuleList()
        
        in_ch = n_channels
        for i in range(n_layers):
            out_ch = min(n_channels * (2 ** i), 512)
            self.encoder_blocks.append(nn.Sequential(
                ConvBlock(in_ch, out_ch, dropout=dropout),
                ResidualBlock(out_ch, dropout=dropout),
                AttentionBlock(out_ch)
            ))
            self.encoder_pools.append(nn.MaxPool1d(2))
            in_ch = out_ch
        
        # Bottleneck
        self.bottleneck = nn.Sequential(
            ConvBlock(in_ch, in_ch * 2, dropout=dropout),
            ResidualBlock(in_ch * 2, dropout=dropout),
            ResidualBlock(in_ch * 2, dropout=dropout),
            AttentionBlock(in_ch * 2)
        )
        
        # Декодер
        self.decoder_blocks = nn.ModuleList()
        self.decoder_upsamples = nn.ModuleList()
        
        in_ch = in_ch * 2
        for i in range(n_layers):
            out_ch = min(n_channels * (2 ** (n_layers - i - 1)), 512)
            skip_ch = out_ch if i < n_layers - 1 else n_channels
            
            self.decoder_upsamples.append(nn.ConvTranspose1d(in_ch, out_ch, 2, stride=2))
            self.decoder_blocks.append(nn.Sequential(
                ConvBlock(out_ch + skip_ch, out_ch, dropout=dropout),
                ResidualBlock(out_ch, dropout=dropout),
                AttentionBlock(out_ch)
            ))
            in_ch = out_ch
        
        # Выходная свертка
        self.output_conv = nn.Sequential(
            ConvBlock(n_channels, n_channels // 2, dropout=dropout),
            nn.Conv1d(n_channels // 2, 1, kernel_size=7, padding=3),
            nn.Tanh()  # Ограничиваем выход в диапазон [-1, 1]
        )
        
        # Инициализация весов
        self.apply(self._init_weights)
    
    def _init_weights(self, m):
        if isinstance(m, nn.Conv1d):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # Входная свертка
        x = self.input_conv(x)
        
        # Энкодер с сохранением skip connections
        skip_connections = []
        for i, (encoder, pool) in enumerate(zip(self.encoder_blocks, self.encoder_pools)):
            x = encoder(x)
            skip_connections.append(x)
            x = pool(x)
        
        # Bottleneck
        x = self.bottleneck(x)
        
        # Декодер с использованием skip connections
        for i, (upsample, decoder) in enumerate(zip(self.decoder_upsamples, self.decoder_blocks)):
            x = upsample(x)
            # Подгоняем размер если необходимо
            if x.size(-1) != skip_connections[-(i+1)].size(-1):
                x = F.interpolate(x, size=skip_connections[-(i+1)].size(-1), mode='linear', align_corners=False)
            x = torch.cat([x, skip_connections[-(i+1)]], dim=1)
            x = decoder(x)
        
        # Выходная свертка
        x = self.output_conv(x)
        
        return x


class VocalEnhancerLoss(nn.Module):
    """
    Специализированная функция потерь для улучшения вокала
    Комбинирует L1 loss, MSE loss и спектральные потери
    """
    
    def __init__(self, l1_weight=1.0, mse_weight=1.0, spectral_weight=0.5):
        super(VocalEnhancerLoss, self).__init__()
        self.l1_weight = l1_weight
        self.mse_weight = mse_weight
        self.spectral_weight = spectral_weight
        
        self.l1_loss = nn.L1Loss()
        self.mse_loss = nn.MSELoss()
    
    def spectral_loss(self, pred, target):
        """Спектральная потеря для лучшего сохранения частотных характеристик"""
        # STFT для получения спектрограммы
        pred_stft = torch.stft(pred.squeeze(1), n_fft=512, hop_length=128, 
                              win_length=512, return_complex=True)
        target_stft = torch.stft(target.squeeze(1), n_fft=512, hop_length=128, 
                               win_length=512, return_complex=True)
        
        # Амплитудная спектрограмма
        pred_mag = torch.abs(pred_stft)
        target_mag = torch.abs(target_stft)
        
        return self.l1_loss(pred_mag, target_mag)
    
    def forward(self, pred, target):
        # Временная потеря
        l1_loss = self.l1_loss(pred, target)
        mse_loss = self.mse_loss(pred, target)
        
        # Спектральная потеря
        spectral_loss = self.spectral_loss(pred, target)
        
        total_loss = (self.l1_weight * l1_loss + 
                     self.mse_weight * mse_loss + 
                     self.spectral_weight * spectral_loss)
        
        return total_loss, {
            'l1_loss': l1_loss.item(),
            'mse_loss': mse_loss.item(),
            'spectral_loss': spectral_loss.item(),
            'total_loss': total_loss.item()
        }


def count_parameters(model):
    """Подсчет количества обучаемых параметров"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Тестирование модели
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = VocalEnhancer(n_channels=64, n_layers=4).to(device)
    
    print(f"Модель создана с {count_parameters(model):,} обучаемыми параметрами")
    
    # Тестовый вход
    batch_size = 2
    seq_length = 16000  # 1 секунда при 16kHz
    x = torch.randn(batch_size, 1, seq_length).to(device)
    
    with torch.no_grad():
        output = model(x)
    
    print(f"Вход: {x.shape}")
    print(f"Выход: {output.shape}")
    
    # Тестирование функции потерь
    loss_fn = VocalEnhancerLoss()
    target = torch.randn_like(output)
    loss, loss_dict = loss_fn(output, target)
    
    print(f"Потеря: {loss.item():.4f}")
    print("Компоненты потерь:", loss_dict)