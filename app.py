# ==============================================================================
# 1. БАЗА СОТРУДНИКОВ (Без истории ротации)
# ==============================================================================
# 'wants_with': ID напарника, с кем ХОЧЕТ работать (если нет — None)
# 'does_not_want_with': ID сотрудника, с кем КАТЕГОРИЧЕСКИ НЕ ХОЧЕТ работать (если нет — None)
employees = {
    1: {"name": "Ефимов А.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    2: {"name": "Богатенков В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    3: {"name": "Герр В.", "role": "старший", "wants_with": [4, 12, 15], "does_not_want_with": None},
    
    # ПРИМЕР: Панкратов и Поздняков хотят быть вместе, но Панкратов против Русакова (ID 6)
    4: {"name": "Герр Н.", "role": "старший", "wants_with": [3, 12, 15], "does_not_want_with": 10},
    5: {"name": "Кестер А.", "role": "старший", "wants_with": 4, "does_not_want_with": None},
    6: {"name": "Курган М.", "role": "старший", "wants_with": None, "does_not_want_with": 11},
    
    7: {"name": "Мазепа С.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    8: {"name": "Пашков Б.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    9: {"name": "Пегова О.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    10: {"name": "Петров Д.", "role": "оператор", "wants_with": None, "does_not_want_with": 4},
    11: {"name": "Попов В.", "role": "старший", "wants_with": 10, "does_not_want_with": 10},
    12: {"name": "Романкин П.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    13: {"name": "Рощина В.", "role": "оператор", "wants_with": None, "does_not_want_with": 11},
    14: {"name": "Соколова Ю.", "role": "старший", "wants_with": None, "does_not_want_with": 11},
    15: {"name": "Царегородцева Е.", "role": "оператор", "wants_with": [4, 3, 12], "does_not_want_with": None},
    16: {"name": "Чернов Г.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    17: {"name": "Чубаров С.", "role": "оператор", "wants_with": 18, "does_not_want_with": [10, 11]},
    18: {"name": "Загуменнов Д.", "role": "оператор", "wants_with": 17, "does_not_want_with": None},
    #Резерв
    19: {"name": "Вотинов", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    20: {"name": "Полищук", "role": "оператор", "wants_with": None, "does_not_want_with": None
    #21: {"name": "", "role": "оператор", "wants_with": None, "does_not_want_with": None}

    }
}

# ==============================================================================
# 2. НАСТРОЙКИ НА СЕГОДНЯ
# ==============================================================================
# Список ID тех, кто сегодня отсутствует (например, [3, 14])
ABSENT_EMPLOYEES = [18, 13, 16, 7, 8]

# Потребность в людях на 5 линиях в зависимости от сегодняшней сложности изделий
LINE_DEMANDS = {
    1: 3,  # Линия 1 -> нужно 4 человека
    2: 3,  # Линия 2 -> нужно 3 человека
    3: 4,  # Линия 3 -> нужно 2 человека
    4: 3,  # Линия 4 -> нужно 3 человека
    5: 0   # Линия 5 -> нужно 2 человека
}

# Базовые приоритеты линий. Скрипт закроет линии строго от большего к меньшему
LINE_PRIORITIES = {1: 20, 2: 40, 3: 50, 4: 30, 5: 10}

# ==============================================================================
# 3. АЛГОРИТМ БЕЗОПАСНОГО РАСПРЕДЕЛЕНИЯ
# ==============================================================================
def distribute_shift():
    # Отбираем только тех, кто реально на работе
    available_ids = [uid for uid in employees.keys() if uid not in ABSENT_EMPLOYEES]

    print("=== ЕЖЕДНЕВНОЕ АВТОМАТИЧЕСКОЕ РАСПРЕДЕЛЕНИЕ СМЕНЫ ===")
    print(f"👥 Всего операторов на работе: {len(available_ids)} чел.")
    print("=" * 55 + "\n")

    final_distribution = {line: [] for line in range(1, 6)}
    assigned_operators = set()

    # Двигаемся сверху вниз по приоритетам линий
    for line_num in sorted(LINE_PRIORITIES.keys(), key=lambda x: LINE_PRIORITIES[x], reverse=True):
        required_count = LINE_DEMANDS.get(line_num, 0)
        
        while len(final_distribution[line_num]) < required_count:
            # Находим свободных на данный момент людей
            candidates = [uid for uid in available_ids if uid not in assigned_operators]
            if not candidates:
                break 

            # Фильтруем кандидатов: убираем конфликты с теми, кто УЖЕ назначен на эту линию
            filtered_candidates = []
            for uid in candidates:
                has_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if employees[uid]["does_not_want_with"] == assigned_uid or employees[assigned_uid]["does_not_want_with"] == uid:
                        has_conflict = True
                        break
                if not has_conflict:
                    filtered_candidates.append(uid)

            if not filtered_candidates:
                break 

            # Функция оценки кандидата: базовый приоритет линии + бонус за желанного напарника
            def get_best_score(uid):
                score = LINE_PRIORITIES[line_num]
                partner_id = employees[uid]["wants_with"]
                if partner_id in final_distribution[line_num]:
                    score += 25
                return score

            filtered_candidates.sort(key=get_best_score, reverse=True)
            best_candidate = filtered_candidates[0]
            
            # Логика неразрывных пар
            partner_id = employees[best_candidate]["wants_with"]
            can_take_partner = False
            
            # ИСПРАВЛЕНО: берем пару только если на линии осталось МИНИМУМ 2 свободных места
            if (partner_id and 
                partner_id in available_ids and 
                partner_id not in assigned_operators and 
                len(final_distribution[line_num]) + 1 < required_count):
                
                # Проверяем, нет ли конфликтов у напарника с людьми на текущей линии
                partner_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if employees[partner_id]["does_not_want_with"] == assigned_uid or employees[assigned_uid]["does_not_want_with"] == partner_id:
                        partner_conflict = True
                        break
                # Напарники не должны враждовать между собой
                if employees[partner_id]["does_not_want_with"] == best_candidate or employees[best_candidate]["does_not_want_with"] == partner_id:
                    partner_conflict = True
                    
                if not partner_conflict:
                    can_take_partner = True

            if can_take_partner:
                final_distribution[line_num].append(best_candidate)
                final_distribution[line_num].append(partner_id)
                assigned_operators.add(best_candidate)
                assigned_operators.add(partner_id)
            else:
                # Берем только одного (лучшего) кандидата, так как места мало или пары нет
                final_distribution[line_num].append(best_candidate)
                assigned_operators.add(best_candidate)

    # ==============================================================================
    # 4. ВЫВОД РЕЗУЛЬТАТОВ РАБОТЫ ПРОГРАММЫ
    # ==============================================================================
    print("📍 СФОРМИРОВАННЫЙ ГРАФИК ПО ЛИНИЯМ:")
    for line_num in range(1, 6):
        req = LINE_DEMANDS.get(line_num, 0)
        formatted_names = []
        
        for uid in final_distribution[line_num]:
            name = employees[uid]["name"]
            if employees[uid]["role"] == "senior" or employees[uid]["role"] == "старший":
                formatted_names.append(f"{name} 👑")
            else:
                formatted_names.append(name)
        
        print(f"Линия {line_num} (Требуется: {req} | Распределено: {len(formatted_names)}):")
        if formatted_names:
            print(f"  └─ 🏃 Состав: {', '.join(formatted_names)}")
        else:
            print("  └─ ❌ Линия полностью простаивает")
            
        if len(formatted_names) < req:
            print(f"  ⚠️  ВНИМАНИЕ: Не хватило {req - len(formatted_names)} чел. из-за ограничений/дефицита!")
        print("-" * 55)

    # Вывод резерва
    leftovers = []
    for uid in available_ids:
        if uid not in assigned_operators:
            name = employees[uid]["name"]
            if employees[uid]["role"] == "senior" or employees[uid]["role"] == "старший":
                leftovers.append(f"{name} 👑")
            else:
                leftovers.append(name)
                
    if leftovers:
        print(f"📦 ОСТАЛИСЬ В РЕЗЕРВЕ: {', '.join(leftovers)}")

# Запуск расчета
distribute_shift()

