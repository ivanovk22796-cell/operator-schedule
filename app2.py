import streamlit as st

# Устанавливаем настройки страницы
st.set_page_config(page_title="Распределение смены", page_icon="📊", layout="wide")


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
    #19: {"name": "Вотинов", "role": "оператор", "wants_with": None, "does_not_want_with": None},
    #20: {"name": "Полищук", "role": "оператор", "wants_with": None, "does_not_want_with": None
    #21: {"name": "", "role": "оператор", "wants_with": None, "does_not_want_with": None}

    }


LINE_PRIORITIES = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10}

# ИНТЕРФЕЙС: Шапка приложения
st.title("📊 Автоматическое распределение операторов")
st.markdown("Настройте параметры дня в левой панели и нажмите кнопку рассчитать.")

# ИНТЕРФЕЙС: Боковая панель управления (Sidebar)
st.sidebar.header("⚙️ Настройки на сегодня")

# 1. Выбор отсутствующих сотрудников
all_emp_options = {uid: info["name"] for uid in employees.items()}
absent_names = st.sidebar.multiselect(
    "🏥 Отсутствуют (Отпуск/Больничный):",
    options=list(all_emp_options.values()),
    default=[]
)
# Переводим имена обратно в ID
ABSENT_EMPLOYEES = [uid for uid, name in all_emp_options.items() if name in absent_names]

# 2. Настройка потребности в людях (динамическая сложность)
st.sidebar.subheader("📈 Потребность на линиях:")
LINE_DEMANDS = {}
for line_num in range(1, 6):
    LINE_DEMANDS[line_num] = st.sidebar.number_input(
        f"Линия {line_num} (чел.):", 
        min_value=0, 
        max_value=18, 
        value=3 if line_num <= 4 else 2  # значения по умолчанию
    )

# Кнопка запуска расчета
start_calculation = st.sidebar.button("⚡ Рассчитать график", type="primary")

# ==============================================================================
# 3. ФУНКЦИЯ РАСЧЕТА (Ваш рабочий алгоритм)
# ==============================================================================
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
                    if employees[uid]["does_not_want_with"] == assigned_uid or employees[assigned_uid]["does_not_want_with"] == uid:
                        has_conflict = True
                        break
                if not has_conflict:
                    filtered_candidates.append(uid)

            if not filtered_candidates:
                break 

            def get_best_score(uid):
                score = LINE_PRIORITIES[line_num]
                partner_id = employees[uid]["wants_with"]
                if partner_id in final_distribution[line_num]:
                    score += 25
                return score

            filtered_candidates.sort(key=get_best_score, reverse=True)
            best_candidate = filtered_candidates
            
            partner_id = employees[best_candidate]["wants_with"]
            can_take_partner = False
            
            if (partner_id and 
                partner_id in available_ids and 
                partner_id not in assigned_operators and 
                len(final_distribution[line_num]) + 1 < required_count):
                
                partner_conflict = False
                for assigned_uid in final_distribution[line_num]:
                    if employees[partner_id]["does_not_want_with"] == assigned_uid or employees[assigned_uid]["does_not_want_with"] == partner_id:
                        partner_conflict = True
                        break
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
                final_distribution[line_num].append(best_candidate)
                assigned_operators.add(best_candidate)
                
    return final_distribution, available_ids, assigned_operators

# ==============================================================================
# 4. ОТРИСОВКА ИНТЕРФЕЙСА ПОСЛЕ КЛИКА
# ==============================================================================
if start_calculation:
    final_dist, av_ids, assigned_ops = run_distribution()
    
    st.success("🎉 Распределение успешно завершено!")
    
    # Выводим карточки линий в красивую сетку
    cols = st.columns(5)
    for idx, line_num in enumerate(range(1, 6)):
        with cols[idx]:
            req = LINE_DEMANDS.get(line_num, 0)
            actual_count = len(final_dist[line_num])
            
            # Заголовок карточки линии
            st.subheader(f"📍 Линия {line_num}")
            st.caption(f"План: {actual_count} из {req}")
            
            # Содержимое карточки
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
                
            # Предупреждение о нехватке кадров
            if actual_count < req:
                st.warning(f"⚠️ Нехватка: {req - actual_count} чел.")
                
    st.markdown("---")
    
    # Вывод резерва
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
