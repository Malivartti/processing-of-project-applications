# E2E Сценарий: Полный рабочий цикл ЦПД

## Описание

Полный сценарий обработки проектных заявок: от импорта Excel-файла до экспорта отобранных проектов
с группами и оценкой схожести.

## Предварительные условия

- Docker Compose запущен: `docker compose up -d`
- Все миграции применены: `docker compose exec backend alembic upgrade head`
- Сервисы healthy: `docker compose ps`

## Тестовые данные

Файл: `scenarios/test_projects_50.xlsx` — 50 проектов, 3 семантические группы:

| Строки | Тема | Ожидаемая группировка |
|--------|------|-----------------------|
| 2–4    | ИИ-диагностика онкологии (NOUN: диагностика, онкология, рак, система; VERB: разработать) | Должны попасть в одну группу |
| 5–7    | Управление трафиком умного города (NOUN: светофор, трафик, транспорт; VERB: управлять) | Должны попасть в одну группу |
| 8–10   | Накопление возобновляемой энергии (NOUN: накопление, энергия, аккумулятор; VERB: хранить) | Должны попасть в одну группу |
| 11–51  | Разнообразные проекты без явного семантического пересечения | Не должны группироваться |

## Шаги сценария

### Шаг 1: Импорт 50 проектов

**Действие:**
```
POST /api/projects/import (multipart, файл test_projects_50.xlsx)
```

**Ожидаемый результат:**
- Ответ: `{ valid_count: 50, error_count: 0, errors: [], duplicates: [] }`

**Подтверждение импорта:**
```
POST /api/projects/import?confirm=true (multipart, тот же файл)
```

**Проверка:**
```
GET /api/projects → total == 50
GET /api/stats/counters → { total: 50, new: 50, auto_checked: 0 }
```

**Через UI:**
1. Открыть `/projects`
2. Нажать "Импорт" → выбрать `test_projects_50.xlsx`
3. Проверить превью: "50 строк готовы к импорту"
4. Нажать "Импортировать 50 проектов"
5. Список обновился, счётчики в шапке: Всего 50 / Новых 50

---

### Шаг 2: Авто-группировка

**Действие:**
```
POST /api/grouping/run
{ "threshold": 0.75, "context": "main" }
```

**Ожидаемый ответ:** `{ run_id: "<uuid>" }`

**Отслеживание прогресса:**
```
GET /api/grouping/status/<run_id>
```
Повторять до `stage == "done"`.

**Временное ограничение:** < 30 секунд для 50 проектов.

**Ожидаемый результат:**
```
GET /api/groups?source=auto
→ Минимум 3 группы (ИИ-медицина, трафик, энергия)
```

**Через UI:**
1. Нажать "Найти похожие" → выбрать пресет "Средний (0.75)"
2. Нажать "Запустить"
3. Прогресс-бар: stages embeddings → similarity → clustering → saving → done
4. Toast: "Группировка завершена: найдено N групп"
5. Переключить в режим "Группы" — аккордеон с группами

---

### Шаг 3: Ручные корректировки

#### 3а. Подтверждение авто-группы

**Действие:**
```
POST /api/groups/<id>/confirm
```
(взять id одной из авто-групп с ИИ-медициной)

**Проверка:**
```
GET /api/groups/<id> → is_confirmed == true
```

**Через UI:**
1. В режиме "Группы" найти группу с ИИ-диагностикой
2. Нажать ✓ "Подтвердить" → подтвердить в диалоге
3. Рамка тега меняется с пунктирной на сплошную

#### 3б. Создание ручной группы

**Предусловие:** выбрать 2 проекта из разных семантических областей (не из авто-групп).

**Действие:**
```
POST /api/groups
{ "name": "Экологические технологии", "description": "Ручная группа для тестирования", "project_ids": [<id1>, <id2>] }
```

**Через UI:**
1. В режиме "Список" выделить 2 чекбокса у проектов
2. Нажать "Создать группу" → ввести название "Экологические технологии"
3. Группа появилась в тегах проектов

---

### Шаг 4: Отбор на семестр

**Действие — добавить 10 проектов в отбор:**
```
POST /api/projects/<id>/select  (× 10 проектов)
```

**Проверка:**
```
GET /api/projects?is_selected=true → total == 10
```

**Через UI:**
1. В карточке каждого проекта нажать "Добавить в отбор"
2. Перейти на вкладку `/selection` — 10 проектов в списке
3. Счётчик: "Отобрано: 10"

**Запуск проверки схожести среди отобранных:**
```
POST /api/grouping/run
{ "threshold": 0.75, "context": "selection" }
```

**Ожидаемый результат:**
```
GET /api/groups?context=selection
→ Группы context='selection' не смешиваются с context='main'
```

**Через UI:**
1. На `/selection` нажать "Проверить на схожесть"
2. Дождаться завершения
3. Результат показан в режиме аккордеона на той же вкладке

---

### Шаг 5: Экспорт отобранных

**Действие:**
```
GET /api/projects/export?context=selected
```

**Ожидаемый результат:**
- Статус 200, Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: `attachment; filename=projects_export.xlsx`
- Excel-файл содержит ровно 10 строк (без заголовка)
- Колонки: Название, Описание проблемы, Цель, Ожидаемый результат, Текущий, Направление, Приоритетное направление, УГТ, В отборе, Источник, **Группа**, **Score**
- У проектов, которые попали в группу, заполнены колонки Группа и Score
- Время ответа < 5 секунд

**Через UI:**
1. На `/selection` нажать "Экспорт в Excel"
2. Файл скачивается автоматически
3. Открыть в Excel: 10 строк, заполнены колонки Группа и Score

---

## Критерии успешности

| Критерий | Порог |
|----------|-------|
| Импорт 50 проектов | valid_count == 50, error_count == 0 |
| Авто-группировка | < 30 сек, ≥ 3 группы найдены |
| Семантические группы | проекты по ИИ-медицине, трафику и энергии объединены |
| Отбор | ровно 10 проектов, context изолирован |
| Экспорт | 10 строк, колонки Группа и Score заполнены |
| Общее время экспорта | < 5 сек |

---

## Воспроизведение через curl

```bash
BASE=http://localhost/api

# Шаг 1: Импорт
curl -s -X POST "$BASE/projects/import" \
  -F "file=@scenarios/test_projects_50.xlsx" | jq '.valid_count'
# → 50

curl -s -X POST "$BASE/projects/import?confirm=true" \
  -F "file=@scenarios/test_projects_50.xlsx" | jq '.'

# Шаг 2: Группировка
RUN_ID=$(curl -s -X POST "$BASE/grouping/run" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 0.75, "context": "main"}' | jq -r '.run_id')

# Ожидание завершения (≤30 сек)
for i in $(seq 1 15); do
  STATUS=$(curl -s "$BASE/grouping/status/$RUN_ID" | jq -r '.stage')
  echo "Stage: $STATUS"
  [ "$STATUS" = "done" ] && break
  sleep 2
done

# Проверка групп
curl -s "$BASE/groups?source=auto" | jq '.total'

# Шаг 3: Подтверждение первой авто-группы
GROUP_ID=$(curl -s "$BASE/groups?source=auto&limit=1" | jq -r '.items[0].id')
curl -s -X POST "$BASE/groups/$GROUP_ID/confirm" | jq '.is_confirmed'
# → true

# Шаг 4: Отбор 10 проектов
PROJ_IDS=$(curl -s "$BASE/projects?limit=10" | jq -r '.items[].id')
for ID in $PROJ_IDS; do
  curl -s -X POST "$BASE/projects/$ID/select" > /dev/null
done
curl -s "$BASE/projects?is_selected=true" | jq '.total'
# → 10

# Шаг 5: Экспорт
curl -s -o /tmp/export.xlsx "$BASE/projects/export?context=selected"
ls -la /tmp/export.xlsx
```

---

## Изоляция контекстов

Проверка что группы `main` и `selection` независимы:

```bash
# Группы основного потока
curl -s "$BASE/groups?context=main" | jq '.total'

# Группы отбора
curl -s "$BASE/groups?context=selection" | jq '.total'

# Убедиться что числа разные и не смешиваются
```
