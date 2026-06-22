import streamlit as st

# 1. Настройка страницы (должна идти строго первой в коде)
st.set_page_config(page_title="Распределение смены", page_icon="📊", layout="wide")

# 2. ВАША ОРИГИНАЛЬНАЯ БАЗА ДАННЫХ (С постоянными исключениями)
# В поле "does_not_want_with" теперь можно писать списки ID через запятую: [10, 11, 12]
# Если запретов нет, оставляйте None
employees = {
    1: {"name": "Ефимов А.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    2: {"name": "Богатенков В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    3: {"name": "Герр В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    
    # Герр Н. не хочет работать с Петровым Д. (ID 10)
    4: {"name": "Герр Н.", "role": "старший", "wants_with": None, "does_not_want_with": [10]},
    5: {"name": "Кестер А.", "role": "старший", "wants_with": 4, "does_not_want_with": None},
    
    # Курган М. не хочет работать с Поповым В. (ID 11)
    6: {"name": "Курган М.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    
    7: {"name": "Мазепа С.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    8: {"name": "Пашков Б.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    9: {"name": "Пегова О.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    
    # Петров Д. не хочет работать с Герр Н. (ID 4)
    10: {"name": "Петров Д.", "role": "оператор", "wants_with": None, "does_not_want_with": [4]},
    
    # Попов В. не хочет работать сам с собой? (В коде стояло 10 - Петров Д.)
    11: {"name": "Попов В.", "role": "старший", "wants_with": 10, "does_not_want_with": [10]},
    
    12: {"name": "Романкин П.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    
    # Рощина В. и Соколова Ю. не хотят работать с Поповым В. (ID 11)
    13: {"name": "Рощина В.", "role": "оператор", "wants_with": None, "does_not_want_with": [11]},
    14: {"name": "Соколова Ю.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    
    15: {"name": "Царегородцева Е.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    16: {"name": "Чернов Г.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    
    # Чубаров С. на постоянной основе не хочет работать с Петровым (10) и Поповым (11)
    17: {"name": "Чубаров С.", "role": "оператор", "wants_with": 18, "does_not_want_with": [10, 11]},
    18: {"name": "Загуменнов Д.", "role": "оператор", "wants_with": 17, "does_not_want_with": None}
}


LINE_PRIORITIES = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10}

# Вспомогательная функция для проверки связей
def check_relation(relation_value, target_id):
    if relation_value is None:
        return False
    if isinstance(relation_value, list):
        return target_id in relation_value
    return relation_value == target_id

# 3. ВИЗУАЛЬНЫЙ ИНТЕРФЕЙС САЙТА
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

# ИНТЕРФЕЙС: Динамическое добавление новых запретов (антипатий)
st.sidebar.subheader("🚫 Дополнительные запреты")
st.sidebar.markdown("<small>Здесь можно оперативно добавить новые конфликты на сегодня</small>", unsafe_allow_html=True)

if "conflicts" not in st.session_state:
    st.session_state.conflicts = []

if st.sidebar.button("➕ Добавить запрет совместной работы"):
    st.session_state.conflicts.append({"emp1": employee_names_list, "emp2": employee_names_list})

# Сбор добавленных на сайте запретов
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

# Настройка потребности на линиях
st.sidebar.subheader("📈 Потребность на линиях:")
LINE_DEMANDS = {}
for line_num in range(1, 6):
    LINE_DEMANDS[line_num] = st.sidebar.number_input(
        f"Линия {line_num} (чел.):", 
        min_value=0, 
        max_value=18, 
        value=3 if line_num <= 4 else 2
    )

start_calculation = st.sidebar.button("⚡ Рассчитать график", type="primary")

# 4. ЛОГИКА РАСЧЕТА АЛГОРИТМА
def run_distribution():
    available_ids = [uid for uid in employees.keys() if uid not in ABSENT_EMPLOYEES]
    final_distribution = {line: [] for line in range(1, 6)}
    assigned_operators = set()

    for line_num in sorted(LINE_PRIORITIES.keys(), key=lambda x: LINE_PRIORITIES[x], reverse=True):
        required_count = LINE_DEMANDS.get(line_num, 0)
        
        while len(final_distribution[line_num]) < required_count:
            candidates = [uid for uid in available_ids if uid not in assigned_operators]
            if not candidates:
                break 

            filtered_candidates = []
            for uid in candidates:
                has_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    # 1. Проверяем базовые запреты из вашей базы данных
                    if check_relation(employees[uid]["does_not_want_with"], assigned_uid):
                        has_conflict = True
                        break
                    if check_relation(employees[assigned_uid]["does_not_want_with"], uid):
                        has_conflict = True
                        break
                    # 2. Проверяем новые запреты, добавленные на сайте мышкой
                    if (uid, assigned_uid) in site_conflicts or (assigned_uid, uid) in site_conflicts:
                        has_conflict = True
                        break
                        
                if not has_conflict:
                    filtered_candidates.append(uid)

            if not filtered_candidates:
                break 

            # Считаем балл полезности кандидата
            def get_best_score(uid):
                score = LINE_PRIORITIES[line_num]
                for assigned_uid in final_distribution[line_num]:
                    if check_relation(employees[uid]["wants_with"], assigned_uid):
                        score += 25
                        break
                return score

            filtered_candidates.sort(key=get_best_score, reverse=True)
            best_candidate = filtered_candidates[0]
            
            # Логика подтягивания пар (смотрим первого из списка желаемых)
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
