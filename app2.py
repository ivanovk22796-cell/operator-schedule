import streamlit as st
import itertools

# 1. Настройка страницы
st.set_page_config(page_title="Распределение смены", page_icon="📊", layout="wide")

# 2. ВАША ОРИГИНАЛЬНАЯ БАЗА ДАННЫХ
employees = {
    1: {"name": "Ефимов А.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    2: {"name": "Богатенков В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    3: {"name": "Герр В.", "role": "старший", "wants_with": [4, 12, 15], "does_not_want_with": None},
    4: {"name": "Герр Н.", "role": "старший", "wants_with": [3, 12,15], "does_not_want_with": [10]},
    5: {"name": "Кестер А.", "role": "старший", "wants_with": 4, "does_not_want_with": None},
    6: {"name": "Курган М.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    7: {"name": "Мазепа С.", "role": "старший", "wants_with": 8, "does_not_want_with": None},
    8: {"name": "Пашков Б.", "role": "старший", "wants_with": 7, "does_not_want_with": None},
    9: {"name": "Пегова О.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    10: {"name": "Петров Д.", "role": "оператор", "wants_with": None, "does_not_want_with": [4]},
    11: {"name": "Попов В.", "role": "старший", "wants_with": 10, "does_not_want_with": [10]},
    12: {"name": "Романкин П.", "role": "старший", "wants_with": [3, 4, 15], "does_not_want_with": None},
    13: {"name": "Рощина В.", "role": "оператор", "wants_with": None, "does_not_want_with": [11]},
    14: {"name": "Соколова Ю.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    15: {"name": "Царегородцева Е.", "role": "оператор", "wants_with": [3, 4, 12], "does_not_want_with": None},
    16: {"name": "Чернов Г.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    17: {"name": "Чубаров С.", "role": "оператор", "wants_with": 18, "does_not_want_with": [10, 11]},
    18: {"name": "Загуменнов Д.", "role": "оператор", "wants_with": 17, "does_not_want_with": None}
}

LINE_PRIORITIES = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10}

def check_relation(relation_value, target_id):
    if relation_value is None:
        return False
    if isinstance(relation_value, list):
        return target_id in relation_value
    return relation_value == target_id

# Вычисление списка ID отсутствующих по их именам
ABSENT_EMPLOYEES = []
for uid, info in employees.items():
    if info["name"] in absent_names:
        ABSENT_EMPLOYEES.append(uid)

# ==============================================================================
# НОВОЕ: ДОБАВЛЕНИЕ ПРИВЛЕЧЕННОГО СОТРУДНИКА
# ==============================================================================
st.sidebar.subheader("➕ Привлеченный сотрудник")
external_worker_name = st.sidebar.text_input(
    "ФИО сотрудника с другого участка:",
    value="",
    placeholder="Например, Сидоров А."
).strip()

# Если поле не пустое, динамически регистрируем сотрудника в системе
external_worker_id = None
if external_worker_name:
    external_worker_id = 999  # Выделяем специальный ID для внешнего сотрудника
    employees[external_worker_id] = {
        "name": external_worker_name + " (Внеш.)",
        "role": "оператор",
        "wants_with": None,
        "does_not_want_with": None
    }
# ==============================================================================

# Дополнительные запреты на сайте
st.sidebar.subheader("🚫 Дополнительные запреты")


# 4. ЛОГИКА РАСЧЕТА АЛГОРИТМА (Скоростной алгоритм с приоритетом антипатий)
def run_distribution():
    available_ids = [uid for uid in employees.keys() if uid not in ABSENT_EMPLOYEES]
    final_distribution = {line: [] for line in range(1, 6)}
    assigned_operators = set()

    # Сортируем ВСЕХ сотрудников по количеству их ограничений.
    # Те, у кого много запретов, будут распределяться в первую очередь, чтобы им точно хватило места.
    def get_constraint_count(uid):
        count = 0
        dont_want = employees[uid]["does_not_want_with"]
        if dont_want:
            if isinstance(dont_want, list):
                count += len(dont_want)
            else:
                count += 1
        return count

    # Двигаемся строго по приоритетам линий (от 1 до 5)
    for line_num in sorted(LINE_PRIORITIES.keys(), key=lambda x: LINE_PRIORITIES[x], reverse=True):
        required_count = LINE_DEMANDS.get(line_num, 0)
        
        while len(final_distribution[line_num]) < required_count:
            candidates = [uid for uid in available_ids if uid not in assigned_operators]
            if not candidates:
                break 

            # Фильтруем кандидатов: убираем тех, кто конфликтует с уже сидящими на этой линии
            filtered_candidates = []
            for uid in candidates:
                has_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[uid]["does_not_want_with"], assigned_uid):
                        has_conflict = True
                        break
                    if check_relation(employees[assigned_uid]["does_not_want_with"], uid):
                        has_conflict = True
                        break
                    if (uid, assigned_uid) in site_conflicts or (assigned_uid, uid) in site_conflicts:
                        has_conflict = True
                        break
                        
                if not has_conflict:
                    filtered_candidates.append(uid)

            if not filtered_candidates:
                break 

            # Сортируем кандидатов: сначала берем тех, у кого больше ограничений (чтобы успеть их пристроить),
            # и добавляем бонус, если на линии есть желанный напарник.
            def get_best_score(uid):
                score = LINE_PRIORITIES[line_num]
                # Приоритет «сложным» сотрудникам для рокировки
                score += get_constraint_count(uid) * 10 
                # Бонус за напарника
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[uid]["wants_with"], assigned_uid):
                        score += 25
                        break
                return score

            filtered_candidates.sort(key=get_best_score, reverse=True)
            best_candidate = filtered_candidates[0]
            
            # Логика подтягивания пар (напарников)
            wants = employees[best_candidate]["wants_with"]
            partner_id = None
            if wants:
                if isinstance(wants, list):
                    for p_id in wants:
                        if p_id in available_ids and p_id not in assigned_operators:
                            partner_id = p_id
                            break
                else:
                    if wants in available_ids and wants not in assigned_operators:
                        partner_id = wants

            can_take_partner = False
            if partner_id and len(final_distribution[line_num]) + 1 < required_count:
                partner_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[partner_id]["does_not_want_with"], assigned_uid) or check_relation(employees[assigned_uid]["does_not_want_with"], partner_id):
                        partner_conflict = True
                        break
                    if (partner_id, assigned_uid) in site_conflicts or (assigned_uid, partner_id) in site_conflicts:
                        partner_conflict = True
                        break
                if check_relation(employees[partner_id]["does_not_want_with"], best_candidate) or check_relation(employees[best_candidate]["does_not_want_with"], partner_id):
                    partner_conflict = True
                if (partner_id, best_candidate) in site_conflicts or (best_candidate, partner_id) in site_conflicts:
                    partner_conflict = True
                    
                if not partner_conflict:
                    can_take_partner = True

            if can_take_partner:
                final_distribution[line_num].append(best_candidate)
                final_distribution[line_num].append(partner_id)
                assigned_operators.add(best_candidate)
                assigned_operators.add(partner_id)
            else:
                final_distribution[line_num].append(best_candidate)
                assigned_operators.add(best_candidate)
                
    return final_distribution, available_ids, assigned_operators

# 5. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ НА САЙТЕ
if start_calculation:
    final_dist, av_ids, assigned_ops = run_distribution()
    st.success("🎉 Распределение успешно завершено!")
    
    cols = st.columns(5)
    for idx, line_num in enumerate(range(1, 6)):
        with cols[idx]:
            req = LINE_DEMANDS.get(line_num, 0)
            actual_count = len(final_dist[line_num])
            
            st.subheader(f"📍 Линия {line_num}")
            st.caption(f"План: {actual_count} из {req}")
            
            if final_dist[line_num]:
                for uid in final_dist[line_num]:
                    name = employees[uid]["name"]
                    role = employees[uid]["role"]
                    if role == "старший":
                        st.info(f"👑 **{name}**")
                    else:
                        st.write(f"🏃 {name}")
            else:
                st.error("❌ Простой линии")
                
            if actual_count < req:
                st.warning(f"⚠️ Нехватка: {req - actual_count} чел.")
                
    st.markdown("---")
    
    leftovers = []
    for uid in av_ids:
        if uid not in assigned_ops:
            name = employees[uid]["name"]
            if employees[uid]["role"] == "старший":
                leftovers.append(f"{name} 👑")
            else:
                leftovers.append(name)
                
    st.subheader("📦 Свободный остаток смены (Резерв)")
    if leftovers:
        st.write(", ".join(leftovers))
    else:
        st.write("*Все сотрудники распределены по рабочим местам.*")
else:
    st.info("💡 Нажмите кнопку **«Рассчитать график»** в левой панели, чтобы увидеть результат.")

