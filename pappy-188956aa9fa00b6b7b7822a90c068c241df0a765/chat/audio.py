import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import speech_recognition as sr
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import io
import json

class AudioMessageProcessor:
    """Процессор для обработки аудио-сообщений"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16000  # Стандартная частота дискретизации
    
    def process_audio(self, audio_file) -> dict:
        """Обработка аудио-файла"""
        # Загружаем аудио
        audio_content = audio_file.read()
        
        # Сохраняем временный файл
        temp_path = default_storage.save(
            'temp_audio/temp.wav',
            ContentFile(audio_content)
        )
        
        try:
            # Обработка аудио
            y, sr = librosa.load(
                default_storage.path(temp_path),
                sr=self.sample_rate
            )
            
            # Улучшение качества
            y_cleaned = self.enhance_audio(y)
            
            # Получение волновой формы
            waveform = self.generate_waveform(y_cleaned)
            
            # Транскрибация
            transcript = self.transcribe_audio(temp_path)
            
            # Сохранение обработанного аудио
            output_path = temp_path.replace('temp.wav', 'processed.wav')
            sf.write(
                default_storage.path(output_path),
                y_cleaned,
                self.sample_rate
            )
            
            return {
                'processed_file': output_path,
                'waveform': waveform,
                'transcript': transcript,
                'duration': len(y_cleaned) / self.sample_rate
            }
            
        finally:
            # Удаляем временные файлы
            default_storage.delete(temp_path)
    
    def enhance_audio(self, y: np.ndarray) -> np.ndarray:
        """Улучшение качества аудио"""
        # Нормализация
        y_normalized = librosa.util.normalize(y)
        
        # Удаление шума
        noise_reduced = self.reduce_noise(y_normalized)
        
        # Компрессия динамического диапазона
        y_compressed = self.compress_dynamic_range(noise_reduced)
        
        return y_compressed
    
    def reduce_noise(self, y: np.ndarray) -> np.ndarray:
        """Удаление шума из аудио"""
        # Оценка уровня шума по первым фреймам
        noise_sample = y[:int(self.sample_rate/2)]
        noise_profile = np.mean(np.abs(noise_sample))
        
        # Применение порога шумоподавления
        threshold = noise_profile * 2
        y_denoised = y.copy()
        y_denoised[np.abs(y) < threshold] = 0
        
        return y_denoised
    
    def compress_dynamic_range(self, y: np.ndarray, threshold: float = 0.3, ratio: float = 0.6) -> np.ndarray:
        """Компрессия динамического диапазона"""
        # Находим значения выше порога
        mask = np.abs(y) > threshold
        
        # Применяем компрессию
        y_compressed = y.copy()
        y_compressed[mask] = np.sign(y[mask]) * (
            threshold + (np.abs(y[mask]) - threshold) * ratio
        )
        
        return y_compressed
    
    def generate_waveform(self, y: np.ndarray, segments: int = 100) -> list:
        """Генерация данных для отображения волновой формы"""
        # Разбиваем сигнал на сегменты
        segment_size = len(y) // segments
        waveform = []
        
        for i in range(segments):
            start = i * segment_size
            end = start + segment_size
            segment = y[start:end]
            
            # Вычисляем амплитуду сегмента
            amplitude = float(np.abs(segment).mean())
            waveform.append(amplitude)
        
        # Нормализуем значения от 0 до 1
        waveform = np.array(waveform)
        waveform = (waveform - waveform.min()) / (waveform.max() - waveform.min())
        
        return waveform.tolist()
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Транскрибация аудио в текст"""
        try:
            with sr.AudioFile(default_storage.path(audio_path)) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='ru-RU')
                return text
        except sr.UnknownValueError:
            return "Не удалось распознать речь"
        except sr.RequestError:
            return "Ошибка сервиса распознавания речи"
        except Exception as e:
            return f"Ошибка транскрибации: {str(e)}" 