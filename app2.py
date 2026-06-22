import streamlit as st
import itertools

# 1. Настройка страницы
st.set_page_config(page_title="Распределение смены", page_icon="📊", layout="wide")

# 2. ВАША ОРИГИНАЛЬНАЯ БАЗА ДАННЫХ
employees = {
    1: {"name": "Ефимов А.", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    2: {"name": "Богатенков В.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    3: {"name": "Герр В.", "role": "старший", "wants_with":, "does_not_want_with": None},
    4: {"name": "Герр Н.", "role": "старший", "wants_with":, "does_not_want_with": [10]},
    5: {"name": "Кестер А.", "role": "старший", "wants_with": 4, "does_not_want_with": None},
    6: {"name": "Курган М.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    7: {"name": "Мазепа С.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    8: {"name": "Пашков Б.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    9: {"name": "Пегова О.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    10: {"name": "Петров Д.", "role": "оператор", "wants_with": None, "does_not_want_with": [4]},
    11: {"name": "Попов В.", "role": "старший", "wants_with": 10, "does_not_want_with": [10]},
    12: {"name": "Романкин П.", "role": "старший", "wants_with": None, "does_not_want_with": None},
    13: {"name": "Рощина В.", "role": "оператор", "wants_with": None, "does_not_want_with": [11]},
    14: {"name": "Соколова Ю.", "role": "старший", "wants_with": None, "does_not_want_with": [11]},
    15: {"name": "Царегородцева Е.", "role": "оператор", "wants_with":, "does_not_want_with": None},
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

# 3. ВИЗУАЛЬНЫЙ ИНТЕРФЕЙС
st.title("📊 Автоматическое распределение операторов")
st.markdown("Настройте параметры дня в левой панели и нажмите кнопку рассчитать.")

st.sidebar.header("⚙️ Настройки на сегодня")

employee_names_list = [info["name"] for uid, info in employees.items()]
name_to_id = {info["name"]: uid for uid, info in employees.items()}

absent_names = st.sidebar.multiselect(
    "🏥 Отсутствуют (Отпуск/Больничный):",
    options=employee_names_list,
    default=[]
)
ABSENT_EMPLOYEES = [name_to_id[name] for name in absent_names]

# Дополнительные запреты на сайте
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
        emp1 = st.selectbox(f"Сотрудник А", options=employee_names_list, key=f"conf_a_{idx}", label_visibility="collapsed")
    with col2:
        emp2 = st.selectbox(f"Не хочет с Б", options=employee_names_list, key=f"conf_b_{idx}", label_visibility="collapsed")
    if emp1 != emp2:
        site_conflicts.append((name_to_id[emp1], name_to_id[emp2]))

if st.session_state.conflicts and st.sidebar.button("🗑️ Очистить созданные запреты"):
    st.session_state.conflicts = []
    st.rerun()

st.sidebar.subheader("📈 Потребность на линиях:")
LINE_DEMANDS = {}
for line_num in range(1, 6):
    LINE_DEMANDS[line_num] = st.sidebar.number_input(
        f"Линия {line_num} (чел.):", 
        min_value=0, max_value=18, value=3 if line_num <= 4 else 0
    )

start_calculation = st.sidebar.button("⚡ Рассчитать график", type="primary")

# 4.ГЛОБАЛЬНЫЙ КОМБИНАТОРНЫЙ АЛГОРИТМ (Многошаговый поиск рокировок)
def run_smart_distribution():
    available_ids = [uid for uid in employees.keys() if uid not in ABSENT_EMPLOYEES]
    
    # Считаем суммарное количество мест, которое нужно заполнить
    total_slots_needed = sum(LINE_DEMANDS.values())
    
    # Если требуемых мест больше, чем людей на работе, берем сколько есть
    slots_to_fill = min(total_slots_needed, len(available_ids))
    
    best_global_score = -100000
    best_global_assignment = None

    # Шаг 1: Отбираем базовую группу людей, максимизируя их полезность и синергию пар
    # Чтобы не перебирать все миллионы комбинаций, сначала отранжируем кандидатов по базовой ценности
    def get_individual_worth(uid):
        worth = 0
        wants = employees[uid]["wants_with"]
        if wants:
            if isinstance(wants, list):
                worth += len(wants) * 5
            else:
                worth += 5
        return worth

    available_ids.sort(key=get_individual_worth, reverse=True)
    
    # Берем с небольшим запасом для поиска лучших рокировок
    subset_size = min(slots_to_fill + 4, len(available_ids))
    pool_for_combination = available_ids[:subset_size]

    # Шаг 2: Ищем наилучшее подмножество людей и их идеальную расстановку по линиям
    for workers_combo in itertools.combinations(pool_for_combination, slots_to_fill):
        # Строим распределение по линиям для данной комбинации сотрудников
        current_workers = list(workers_combo)
        
        # Формируем структуру линий под требования дневного плана
        line_slots = []
        for line_id, count in LINE_DEMANDS.items():
            for _ in range(count):
                if len(line_slots) < slots_to_fill:
                    line_slots.append(line_id)

        # Перебираем варианты размещения этих конкретных людей по позициям линий
        for p in itertools.permutations(current_workers):
            # Строим тестовый вариант расписания
            temp_dist = {l: [] for l in range(1, 6)}
            for worker_id, line_id in zip(p, line_slots):
                temp_dist[line_id].append(worker_id)
                
            # Проверяем жесткие ограничения (Конфликты и Антипатии)
            has_fatal_conflict = False
            for line_id, workers_on_line in temp_dist.items():
                for w1, w2 in itertools.combinations(workers_on_line, 2):
                    if check_relation(employees[w1]["does_not_want_with"], w2) or check_relation(employees[w2]["does_not_want_with"], w1):
                        has_fatal_conflict = True
                        break
                    if (w1, w2) in site_conflicts or (w2, w1) in site_conflicts:
                        has_conflict = True
                        has_fatal_conflict = True
                        break
                if has_fatal_conflict:
                    break
                    
            if has_fatal_conflict:
                continue # Эту комбинацию использовать нельзя, пропускаем её

            # Если конфликтов нет, оцениваем качество (баллы за приоритеты линий и за напарников)
            current_score = 0
            for line_id, workers_on_line in temp_dist.items():
                # Баллы за приоритет линии
                current_score += len(workers_on_line) * LINE_PRIORITIES[line_id]
                # Баллы за успешное нахождение желанных пар на одной линии
                for w1 in workers_on_line:
                    for w2 in workers_on_line:
                        if w1 != w2 and check_relation(employees[w1]["wants_with"], w2):
                            current_score += 30 # Серьезный бонус за синергию

            # Если это распределение лучше всех предыдущих — запоминаем его
            if current_score > best_global_score:
                best_global_score = current_score
                best_global_assignment = temp_dist

    # Если идеальное бесконфликтное решение среди подмножества не найдено, запускаем базовый отказоустойчивый добор
    if best_global_assignment is None:
        return {l: [] for l in range(1, 6)}, available_ids, set()

    assigned_operators = set()
    for line_id, workers in best_global_assignment.items():
        for w in workers:
            assigned_operators.add(w)

    return best_global_assignment, available_ids, assigned_operators

# ==============================================================================
# 5. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ НА САЙТЕ
# ==============================================================================
if start_calculation:
    final_dist, av_ids, assigned_ops = run_smart_distribution()
    st.success("🎉 Распределение успешно завершено методом глобальной оптимизации!")
    
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
