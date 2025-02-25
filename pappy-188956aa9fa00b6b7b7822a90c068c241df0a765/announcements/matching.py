import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import torch
from torchvision import transforms, models
from django.core.files.storage import default_storage
from django.conf import settings
import io

class PetMatchingSystem:
    """Система сопоставления объявлений о пропаже/находке животных"""
    
    def __init__(self):
        # Инициализация модели для анализа изображений
        self.image_model = models.resnet50(pretrained=True)
        self.image_model.eval()
        
        # Подготовка трансформации изображений
        self.image_transforms = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Векторизатор для текстовых описаний
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='russian'
        )
    
    def get_image_features(self, image_path: str) -> np.ndarray:
        """Извлечение признаков из изображения"""
        # Загрузка изображения
        with default_storage.open(image_path, 'rb') as f:
            img = Image.open(io.BytesIO(f.read())).convert('RGB')
        
        # Подготовка изображения
        img_tensor = self.image_transforms(img)
        img_tensor = img_tensor.unsqueeze(0)
        
        # Получение признаков
        with torch.no_grad():
            features = self.image_model.features(img_tensor)
            features = torch.flatten(features, 1)
        
        return features.numpy()
    
    def get_text_features(self, text: str) -> np.ndarray:
        """Извлечение признаков из текста"""
        return self.text_vectorizer.fit_transform([text]).toarray()
    
    def calculate_similarity(self, announcement1, announcement2) -> float:
        """Расчет схожести двух объявлений"""
        # Веса для разных компонентов сравнения
        weights = {
            'location': 0.3,
            'description': 0.3,
            'image': 0.2,
            'attributes': 0.2
        }
        
        total_score = 0.0
        
        # Сравнение по геолокации
        distance = self.calculate_distance(
            announcement1.latitude, announcement1.longitude,
            announcement2.latitude, announcement2.longitude
        )
        location_score = 1.0 / (1.0 + distance/1000)  # km to score
        total_score += weights['location'] * location_score
        
        # Сравнение текстовых описаний
        text1 = f"{announcement1.distinctive_features} {announcement1.breed} {announcement1.color}"
        text2 = f"{announcement2.distinctive_features} {announcement2.breed} {announcement2.color}"
        
        text_vectors = self.get_text_features(text1 + " " + text2)
        text_similarity = cosine_similarity(
            text_vectors[0:1],
            text_vectors[1:2]
        )[0][0]
        total_score += weights['description'] * text_similarity
        
        # Сравнение изображений
        if announcement1.images.exists() and announcement2.images.exists():
            img_features1 = self.get_image_features(announcement1.images.first().image.path)
            img_features2 = self.get_image_features(announcement2.images.first().image.path)
            
            image_similarity = cosine_similarity(
                img_features1,
                img_features2
            )[0][0]
            total_score += weights['image'] * image_similarity
        
        # Сравнение атрибутов
        attributes_score = self.compare_attributes(announcement1, announcement2)
        total_score += weights['attributes'] * attributes_score
        
        return total_score
    
    def compare_attributes(self, announcement1, announcement2) -> float:
        """Сравнение атрибутов животных"""
        score = 0.0
        
        # Сравнение породы
        if announcement1.breed.lower() == announcement2.breed.lower():
            score += 0.4
        
        # Сравнение цвета
        if announcement1.color.lower() == announcement2.color.lower():
            score += 0.3
        
        # Сравнение возраста
        if abs(announcement1.age - announcement2.age) <= 1:
            score += 0.3
        
        return score
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Расчет расстояния между двумя точками в метрах"""
        from math import sin, cos, sqrt, atan2, radians
        
        R = 6371.0  # радиус Земли в километрах
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance * 1000  # конвертируем в метры
    
    def find_matches(self, announcement, threshold: float = 0.7) -> list:
        """Поиск похожих объявлений"""
        from .models import LostPetAnnouncement
        
        # Получаем все объявления противоположного типа
        opposite_type = 'found' if announcement.type == 'lost' else 'lost'
        potential_matches = LostPetAnnouncement.objects.filter(
            type=opposite_type,
            status='active'
        ).exclude(
            id=announcement.id
        )
        
        matches = []
        for potential_match in potential_matches:
            similarity = self.calculate_similarity(announcement, potential_match)
            if similarity >= threshold:
                matches.append({
                    'announcement': potential_match,
                    'similarity': similarity
                })
        
        # Сортируем по убыванию схожести
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches 