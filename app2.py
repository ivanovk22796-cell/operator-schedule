import streamlit as st

# 1. Настройка страницы (должна идти строго первой в коде)
st.set_page_config(page_title="Распределение смены", page_icon="📊", layout="wide")

# 2. ВАША ОРИГИНАЛЬНАЯ БАЗА ДАННЫХ
employees = {
    1: {"name": "Ефимов А.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    2: {"name": "Богатенков В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    3: {"name": "Герр В.", "role": "старший", "wants_with": [4, 12, 15], "does_not_want_with": [6, 11, 13, 14, 16]},
    4: {"name": "Герр Н.", "role": "старший", "wants_with": [3, 12,15], "does_not_want_with": [1, 2, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17]},
    5: {"name": "Кестер А.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    6: {"name": "Курган М.", "role": "старший", "wants_with": None, "does_not_want_with": [3, 4, 12, 15, 11]},
    7: {"name": "Мазепа С.", "role": "старший", "wants_with": 8, "does_not_want_with": None},
    8: {"name": "Пашков Б.", "role": "старший", "wants_with": 7, "does_not_want_with": None},
    9: {"name": "Пегова О.", "role": "старший", "wants_with": [1, 2, 3, 6, 7, 8, 12, 14], "does_not_want_with": [4, 10, 11, 15]},
    10: {"name": "Петров Д.", "role": "оператор", "wants_with": None, "does_not_want_with": [4, 15]},
    11: {"name": "Попов В.", "role": "старший", "wants_with": [1, 2, 7, 8, 16], "does_not_want_with": [3, 4, 6, 10, 12, 14, 15]},
    12: {"name": "Романкин П.", "role": "старший", "wants_with": [3, 4, 15], "does_not_want_with": None},
    13: {"name": "Рощина В.", "role": "оператор", "wants_with": [1, 2, 6, 7, 8, 9, 11, 14, 16], "does_not_want_with": [4, 15, 17]},
    14: {"name": "Соколова Ю.", "role": "старший", "wants_with": [1, 2, 6, 7, 8, 9, 17], "does_not_want_with": [11, 15]},
    15: {"name": "Царегородцева Е.", "role": "оператор", "wants_with": [3, 4, 12], "does_not_want_with": None},
    16: {"name": "Чернов Г.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    17: {"name": "Чубаров С.", "role": "оператор", "wants_with": [1, 2, 7, 8, 9, 16], "does_not_want_with": [5, 10, 11, 14]},
    #18: {"name": "Загуменнов Д.", "role": "оператор", "wants_with": 17, "does_not_want_with": None}
}

LINE_PRIORITIES = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10}

# 3. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ СВЯЗЕЙ
def check_relation(relation_value, target_id):
    if relation_value is None:
        return False
    try:
        if isinstance(relation_value, list):
            return target_id in relation_value
        return relation_value == target_id
    except:
        return False

# 4. ВИЗУАЛЬНЫЙ ИНТЕРФЕЙС САЙТА
st.title("📊 Автоматическое распределение операторов")
st.markdown("Настройте параметры дня в левой панели и нажмите кнопку рассчитать.")

st.sidebar.header("⚙️ Настройки на сегодня")

# Списки для выпадающих меню
employee_names_list = [info["name"] for uid, info in employees.items()]
name_to_id = {info["name"]: uid for uid, info in employees.items()}

# Выбор отсутствующих сотрудников
absent_names = st.sidebar.multiselect(
    "🏥 Отсутствуют (Отпуск/Больничный):",
    options=employee_names_list,
    default=[]
)
ABSENT_EMPLOYEES = [name_to_id[name] for name in absent_names]

# ДОБАВЛЕНИЕ ПРИВЛЕЧЕННЫХ СОТРУДНИКОВ (Можно вводить через запятую)
st.sidebar.subheader("➕ Привлеченные сотрудники")
external_workers_input = st.sidebar.text_input(
    "ФИО сотрудников с другого участка (через запятую):",
    value="",
    placeholder="Например: Сидоров А., Кузнецов И."
).strip()

# Если поле не пустое, разбиваем по запятым и регистрируем в системе
if external_workers_input:
    names = [name.strip() for name in external_workers_input.split(",") if name.strip()]
    for idx, name in enumerate(names):
        ext_id = 900 + idx
        employees[ext_id] = {
            "name": f"{name} (Внеш.)",
            "role": "оператор",
            "wants_with": None,
            "does_not_want_with": None
        }
        if f"{name} (Внеш.)" not in employee_names_list:
            employee_names_list.append(f"{name} (Внеш.)")
            name_to_id[f"{name} (Внеш.)"] = ext_id

# Динамическое добавление новых запретов (антипатий) на сайте
st.sidebar.subheader("🚫 Дополнительные запреты")
if "conflicts" not in st.session_state:
    st.session_state.conflicts = []

if st.sidebar.button("➕ Добавить запрет совместной работы"):
    st.session_state.conflicts.append({"emp1": employee_names_list, "emp2": employee_names_list})

site_conflicts = []
for idx in range(len(st.session_state.conflicts)):
    st.sidebar.markdown(f"**Запрет №{idx+1}**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        emp1 = st.selectbox(f"Сотрудник А (пара {idx})", options=employee_names_list, key=f"conf_a_{idx}", label_visibility="collapsed")
    with col2:
        emp2 = st.selectbox(f"Не хочет с Б (пара {idx})", options=employee_names_list, key=f"conf_b_{idx}", label_visibility="collapsed")
    if emp1 != emp2:
        site_conflicts.append((name_to_id[emp1], name_to_id[emp2]))

if st.session_state.conflicts and st.sidebar.button("🗑️ Очистить созданные запреты"):
    st.session_state.conflicts = []
    st.rerun()

# ==============================================================================
# НАСТРОЙКА НАЗВАНИЙ И ПОТРЕБНОСТИ НА ЛИНИЯХ
# ==============================================================================
# 📝 ВПИШИТЕ СЮДА ВАШИ НОВЫЕ НАЗВАНИЯ ЛИНИЙ В КАВЫЧКАХ:
LINE_NAMES = {
    1: "Линия 2-1",
    2: "Линия 2-2",
    3: "Линия 2-3",
    4: "Линия 4-3",
    5: "Линия 4-4"
}

st.sidebar.subheader("📈 Потребность на линиях:")
LINE_DEMANDS = {}
for line_num in range(1, 6):
    # Берем красивое название из словаря выше
    display_name = LINE_NAMES[line_num]
    LINE_DEMANDS[line_num] = st.sidebar.number_input(
        f"{display_name} (чел.):", 
        min_value=0, 
        max_value=18, 
        value=3 if line_num <= 4 else 2
    )

start_calculation = st.sidebar.button("⚡ Рассчитать график", type="primary")


# 5. ЛОГИКА РАСЧЕТА АЛГОРИТМА (С максимальной защитой от ошибок)
def run_distribution():
    available_ids = [uid for uid in employees.keys() if uid not in ABSENT_EMPLOYEES]
    final_distribution = {line: [] for line in range(1, 6)}
    assigned_operators = set()

    def get_constraint_count(uid):
        if uid not in employees:
            return 0
        count = 0
        dont_want = employees[uid].get("does_not_want_with", None)
        if dont_want:
            if isinstance(dont_want, list):
                count += len(dont_want)
            else:
                count += 1
        return count

    for line_num in sorted(LINE_PRIORITIES.keys(), key=lambda x: LINE_PRIORITIES[x], reverse=True):
        required_count = LINE_DEMANDS.get(line_num, 0)
        
        while len(final_distribution[line_num]) < required_count:
            candidates = [uid for uid in available_ids if uid not in assigned_operators]
            if not candidates:
                break 

            filtered_candidates = []
            for uid in candidates:
                if uid not in employees:
                    continue
                has_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[uid].get("does_not_want_with", None), assigned_uid):
                        has_conflict = True
                        break
                    if check_relation(employees.get(assigned_uid, {}).get("does_not_want_with", None), uid):
                        has_conflict = True
                        break
                    if (uid, assigned_uid) in site_conflicts or (assigned_uid, uid) in site_conflicts:
                        has_conflict = True
                        break
                if not has_conflict:
                    filtered_candidates.append(uid)

            if not filtered_candidates:
                break 

            def get_best_score(uid):
                score = LINE_PRIORITIES[line_num]
                score += get_constraint_count(uid) * 10 
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[uid].get("wants_with", None), assigned_uid):
                        score += 25
                        break
                return score

            filtered_candidates.sort(key=get_best_score, reverse=True)
            
            # ЗАЩИТА: Проверяем, что в списке реально кто-то есть
            if len(filtered_candidates) == 0:
                break
                
            # ИСПРАВЛЕНО: Берем именно ПЕРВЫЙ элемент из отсортированного списка кандидатов
            best_candidate = filtered_candidates[0]
            
            if best_candidate is None or best_candidate not in employees:
                break

            wants = employees[best_candidate].get("wants_with", None)
            partner_id = None
            if wants:
                if isinstance(wants, list):
                    for p_id in wants:
                        if p_id in employees and p_id in available_ids and p_id not in assigned_operators:
                            partner_id = p_id
                            break
                else:
                    if wants in employees and wants in available_ids and wants not in assigned_operators:
                        partner_id = wants

            can_take_partner = False
            if partner_id and partner_id in employees and len(final_distribution[line_num]) + 1 < required_count:
                partner_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[partner_id].get("does_not_want_with", None), assigned_uid) or check_relation(employees.get(assigned_uid, {}).get("does_not_want_with", None), partner_id):
                        partner_conflict = True
                        break
                    if (partner_id, assigned_uid) in site_conflicts or (assigned_uid, partner_id) in site_conflicts:
                        partner_conflict = True
                        break
                if check_relation(employees[partner_id].get("does_not_want_with", None), best_candidate) or check_relation(employees[best_candidate].get("does_not_want_with", None), partner_id):
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


  # ==============================================================================
# 6. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ НА САЙТЕ
# ==============================================================================
if start_calculation:
    final_dist, av_ids, assigned_ops = run_distribution()
    st.success("🎉 Распределение успешно завершено!")
    
    cols = st.columns(5)
    for idx, line_num in enumerate(range(1, 6)):
        with cols[idx]:
            req = LINE_DEMANDS.get(line_num, 0)
            actual_count = len(final_dist[line_num])
            
            # Используем новое название линии для заголовка карточки
            display_name = LINE_NAMES.get(line_num, f"Линия {line_num}")
            st.subheader(f"📍 {display_name}")
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

