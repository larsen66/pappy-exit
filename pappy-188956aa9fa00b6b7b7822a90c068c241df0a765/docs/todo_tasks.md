# TODO Tasks

## 1. Потеряшки (Lost Pets)

### 1.1 Специальная форма создания
**Status:** Not implemented
**Implementation Plan:**
1. Create a specialized form for lost pet announcements:
```python
class LostPetAnnouncementForm(forms.ModelForm):
    class Meta:
        model = LostFoundAnnouncement
        fields = [
            'type',  # Lost/Found
            'title',
            'description',
            'date_lost_found',
            'location',
            'latitude',
            'longitude',
            'distinctive_features',
            'images'
        ]
        widgets = {
            'date_lost_found': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'location-autocomplete'}),
        }
```
2. Add map integration for location selection
3. Add multiple image upload support
4. Add breed and color selectors
5. Add distinctive features checklist

### 1.2 Уведомления в районе
**Status:** Not implemented
**Implementation Plan:**
1. Create a radius-based notification system:
```python
class AreaNotificationSystem:
    def notify_users_in_radius(self, announcement, radius_km=5):
        center_point = Point(announcement.longitude, announcement.latitude)
        users_in_radius = User.objects.filter(
            last_location__distance_lte=(center_point, D(km=radius_km))
        )
        for user in users_in_radius:
            send_notification(user, announcement)
```
2. Add PostGIS integration for geospatial queries
3. Implement push notifications
4. Add radius customization
5. Add notification preferences

### 1.3 Алгоритм сопоставления
**Status:** Not implemented
**Implementation Plan:**
1. Implement matching algorithm:
```python
class LostPetMatcher:
    def find_matches(self, announcement):
        base_queryset = LostFoundAnnouncement.objects.exclude(id=announcement.id)
        
        # Match by opposite type (lost->found, found->lost)
        opposite_type = 'found' if announcement.type == 'lost' else 'lost'
        matches = base_queryset.filter(
            type=opposite_type,
            date_lost_found__range=(
                announcement.date_lost_found - timedelta(days=30),
                announcement.date_lost_found + timedelta(days=30)
            )
        )
        
        # Score matches based on:
        # - Location proximity
        # - Date proximity
        # - Pet characteristics similarity
        scored_matches = self._score_matches(announcement, matches)
        return scored_matches
```
2. Add breed similarity scoring
3. Add color pattern matching
4. Add location proximity scoring
5. Add date-based relevance

### 1.4 Система подсказок
**Status:** Not implemented
**Implementation Plan:**
1. Create suggestion system:
```python
class LocationSuggestionSystem:
    def get_suggestions(self, announcement):
        suggestions = []
        
        # Common locations
        suggestions.extend(self._get_common_locations())
        
        # Similar case locations
        suggestions.extend(self._get_similar_case_locations(announcement))
        
        # Popular areas
        suggestions.extend(self._get_popular_areas())
        
        return suggestions
```
2. Add machine learning for pattern recognition
3. Add historical data analysis
4. Add community-driven suggestions
5. Add veterinary clinics and shelters database

### 1.5 История поиска
**Status:** Not implemented
**Implementation Plan:**
1. Create search history tracking:
```python
class SearchHistory(models.Model):
    announcement = models.ForeignKey(LostFoundAnnouncement)
    search_date = models.DateTimeField(auto_now_add=True)
    search_area = models.PolygonField()
    contacted_users = models.ManyToManyField(User)
    search_results = models.JSONField()
    
    class Meta:
        ordering = ['-search_date']
```
2. Add search area visualization
3. Add contact history tracking
4. Add search effectiveness metrics
5. Add timeline visualization

## 2. Тесты (Tests)

### 2.1 Lost Pet Tests
**Status:** Partially implemented
**Missing Tests:**
1. Lost pet form validation
2. Area notification system
3. Matching algorithm accuracy
4. Suggestion system effectiveness
5. Search history tracking

### 2.2 Integration Tests
**Status:** Partially implemented
**Missing Tests:**
1. Complete lost pet workflow
2. Notification delivery system
3. Geolocation accuracy
4. Search and match flow
5. User interaction tracking

## Required Dependencies
```
# Additional requirements for implementation
django-postgis==3.0.0
scikit-learn==1.0.2
django-push-notifications==3.0.0
geopy==2.2.0
django-location-field==2.1.0
```

## Implementation Priority
1. Специальная форма создания (High Priority)
   - Essential for user interaction
   - Foundation for other features

2. Алгоритм сопоставления (High Priority)
   - Core functionality
   - Critical for service effectiveness

3. Уведомления в районе (Medium Priority)
   - Important for community engagement
   - Depends on user base growth

4. Система подсказок (Medium Priority)
   - Enhances user experience
   - Can be gradually improved

5. История поиска (Low Priority)
   - Nice to have
   - Can be implemented later

## Next Steps
1. Set up PostGIS in development environment
2. Create specialized form templates
3. Implement base matching algorithm
4. Set up notification system
5. Add basic suggestion system
6. Implement test suite 

# Оставшиеся задачи

## Тесты для Потеряшек

### Unit Tests
- [ ] Тесты для `LostFoundAnnouncement`:
  - Создание объявления
  - Валидация полей
  - Работа индексов

- [ ] Тесты для сервисов:
  - `AreaNotificationService`
  - `LostPetMatchingService`
  - `LostPetSuggestionService`
  - `SearchHistoryService`

### Integration Tests
- [ ] End-to-end тесты процесса поиска:
  - Создание объявления о пропаже
  - Получение уведомлений
  - Поиск совпадений
  - Работа с историей поиска

### Performance Tests
- [ ] Тесты производительности:
  - Индексы геолокации
  - Алгоритм сопоставления
  - Система уведомлений

## Документация
- [ ] API документация для сервисов
- [ ] Руководство пользователя
- [ ] Примеры использования 