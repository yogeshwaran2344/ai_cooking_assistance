import time
import math
import datetime
import random
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(
    page_title="Chef AI Studio | Smart Cooking Assistant",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading with Cache ---
@st.cache_data
def load_recipes():
    try:
        df = pd.read_csv("data/recipes.csv")
        df.columns = df.columns.str.lower().str.strip()
        # Fallback values for optional columns
        cols_default = {
            "calories": "250 cal", "protein": "10g", "carbs": "30g", "fat": "8g", "fiber": "3g",
            "cuisine": "Global", "serving_size": "2", "equipment": "Pan", "tags": "delicious",
            "allergens": "none", "estimated_cost": "₹150", "storage_tips": "Refrigerate up to 2 days",
            "pairing": "Salad & Wine", "occasion": "All", "image_url": ""
        }
        for col, val in cols_default.items():
            if col not in df.columns:
                df[col] = val
        return df
    except Exception as e:
        st.error(f"Error loading recipes dataset: {e}")
        return pd.DataFrame()

recipes = load_recipes()

# --- Helper: Safe Integer Parsing ---
def parse_numeric(val, suffix=""):
    if pd.isna(val):
        return 0
    val_str = str(val).replace(suffix, "").replace("₹", "").replace("cal", "").replace("g", "").replace("min", "").strip()
    try:
        return int(float(val_str))
    except ValueError:
        return 0

# --- Initialize Session State ---
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []
if "shopping_list" not in st.session_state:
    st.session_state["shopping_list"] = []
if "meal_plan" not in st.session_state:
    st.session_state["meal_plan"] = {day: [] for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
if "cost_history" not in st.session_state:
    st.session_state["cost_history"] = [
        {"date": (datetime.date.today() - datetime.timedelta(days=6)).isoformat(), "cost": 520},
        {"date": (datetime.date.today() - datetime.timedelta(days=4)).isoformat(), "cost": 340},
        {"date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(), "cost": 410},
    ]
if "prepared_recipes" not in st.session_state:
    st.session_state["prepared_recipes"] = {}
if "unlocked_badges" not in st.session_state:
    st.session_state["unlocked_badges"] = set(["🌱 Kitchen Novice"])
if "ai_chat_history" not in st.session_state:
    st.session_state["ai_chat_history"] = [
        {"role": "assistant", "content": "👋 **Welcome Chef!** I'm your AI Culinary Copilot. Ask me about substitutions, recipes, wine pairings, or leftover ideas!"}
    ]
if "kitchen_step_index" not in st.session_state:
    st.session_state["kitchen_step_index"] = 0
if "selected_category" not in st.session_state:
    st.session_state["selected_category"] = "All"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1
if "dashboard_pincode" not in st.session_state:
    st.session_state["dashboard_pincode"] = "560001"

# --- Consolidated Sidebar ---
st.sidebar.title("🍳 Chef AI Studio")
st.sidebar.markdown("---")

# Theme Toggle
dark_mode = st.sidebar.checkbox("🌙 Enable Dark Mode", key="app_dark_mode_toggle")

# Inject High-Contrast CSS Styling for Light & Dark Modes
if dark_mode:
    st.markdown("""
        <style>
        .stApp { background-color: #0F172A; color: #F8FAFC; }
        .hero-header {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-left: 6px solid #F59E0B;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }
        .recipe-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 22px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .recipe-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 28px rgba(245, 158, 11, 0.2);
        }
        .recipe-title { font-size: 21px; font-weight: 700; color: #F59E0B; margin-top: 10px; margin-bottom: 6px; }
        .recipe-meta { font-size: 14px; font-weight: 600; color: #94A3B8; margin-bottom: 12px; }
        .badge-pill {
            background-color: #334155;
            color: #FCD34D;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
            margin-right: 6px;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        .hero-header {
            background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
            border: 2px solid #FDBA74;
            border-left: 8px solid #EA580C;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 6px 20px rgba(234, 88, 12, 0.12);
        }
        .recipe-card {
            background-color: #FFFFFF;
            border: 2px solid #E2E8F0;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 22px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .recipe-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 28px rgba(234, 88, 12, 0.22);
            border-color: #EA580C;
        }
        .recipe-title { font-size: 21px; font-weight: 800; color: #C2410C; margin-top: 10px; margin-bottom: 6px; }
        .recipe-meta { font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 12px; }
        .badge-pill {
            background-color: #FFEDD5;
            color: #C2410C;
            border: 1px solid #FDBA74;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
            margin-right: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

# 🍴 Recipe Filters in Sidebar
st.sidebar.subheader("🍴 Sidebar Filters")
cuisine_list = ["All"] + sorted(recipes["cuisine"].dropna().unique().tolist()) if not recipes.empty else ["All"]
cuisine_filter = st.sidebar.selectbox("Cuisine", cuisine_list, key="sb_cuisine_filter")
diet_filter = st.sidebar.radio("Dietary Preference", ["All", "veg", "non-veg"], key="sb_diet_filter")
prep_filter = st.sidebar.slider("Max Prep Time (mins)", 5, 120, 60, key="sb_prep_filter")
favorite_filter = st.sidebar.radio("Show Favorites Only", ["No", "Yes"], key="sb_favorite_filter")

# 🥦 Pantry Filter
st.sidebar.subheader("🥦 My Pantry ('Cook With What You Have')")
pantry_input = st.sidebar.text_area("Enter ingredients in hand", "", placeholder="e.g. potato, onion, cheese", key="sb_pantry_input")

# 🎯 Daily Nutrition Targets
st.sidebar.subheader("🎯 Daily Nutrition Goals")
goal_cal = st.sidebar.number_input("Target Calories (kcal)", 1000, 4000, 2000, key="sb_goal_cal")
goal_protein = st.sidebar.number_input("Target Protein (g)", 10, 200, 60, key="sb_goal_protein")

# Calculate Prepared Nutrition Total
current_prep_cal = 0
current_prep_protein = 0
for r_name in st.session_state["prepared_recipes"].keys():
    match = recipes[recipes["name"].str.strip().str.lower() == r_name.strip().lower()]
    if not match.empty:
        r_row = match.iloc[0]
        current_prep_cal += parse_numeric(r_row.get("calories", 0), "cal")
        current_prep_protein += parse_numeric(r_row.get("protein", 0), "g")

st.sidebar.markdown(f"**Prepared Calories:** {current_prep_cal} / {goal_cal} kcal")
st.sidebar.progress(min(current_prep_cal / goal_cal, 1.0))
st.sidebar.markdown(f"**Prepared Protein:** {current_prep_protein} / {goal_protein} g")
st.sidebar.progress(min(current_prep_protein / goal_protein, 1.0))

st.sidebar.markdown("---")
# Quick Recipe Randomizer
if st.sidebar.button("🎲 Spin 'What Should I Cook?'", key="sb_btn_randomizer"):
    if not recipes.empty:
        rand_recipe = recipes.sample(1).iloc[0]
        st.sidebar.success(f"🎉 Recommended: **{rand_recipe['name']}** ({rand_recipe['cuisine']} • {rand_recipe['prep_time']})!")

# --- Time of Day Dynamic Greeting ---
current_hour = datetime.datetime.now().hour
if current_hour < 12:
    time_greeting = "Good Morning 🌅"
elif current_hour < 17:
    time_greeting = "Good Afternoon ☀️"
else:
    time_greeting = "Good Evening 🌙"

# --- Main Dashboard Hero Header with PINCODE Input ---
st.markdown(f"""
    <div class="hero-header">
        <h1 style="margin: 0; font-size: 32px; color: {'#F59E0B' if dark_mode else '#C2410C'};">🍳 {time_greeting}, Chef!</h1>
        <p style="margin-top: 6px; font-size: 16px; font-weight: 500; opacity: 0.95;">
            Welcome to your intelligent culinary workspace with {len(recipes)}+ recipes. Plan meals, track grocery costs, and cook step-by-step.
        </p>
    </div>
""", unsafe_allow_html=True)

# 📍 MAIN DASHBOARD PINCODE INPUT
pin_c1, pin_c2, _ = st.columns([2, 2, 2])
with pin_c1:
    dash_pincode = st.text_input("📍 Your Grocery Delivery Pincode", value=st.session_state["dashboard_pincode"], key="main_dash_pincode")
    st.session_state["dashboard_pincode"] = dash_pincode
with pin_c2:
    st.write(" ")
    st.write(" ")
    st.caption(f"⚡ Live pricing active for **Pincode {st.session_state['dashboard_pincode']}**")

# Metrics Summary Bar
m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
m_col1.metric("📖 Total Recipes", len(recipes))
m_col2.metric("❤️ Favorites", len(st.session_state["favorites"]))
m_col3.metric("🛒 Cart Items", len(st.session_state["shopping_list"]))
planned_count = sum(len(dishes) for dishes in st.session_state["meal_plan"].values())
m_col4.metric("📅 Planned Meals", planned_count)
m_col5.metric("🏆 Badges", len(st.session_state["unlocked_badges"]))
m_col6.metric("🔥 Cook Streak", f"{len(st.session_state['prepared_recipes'])} Days")

# Dynamic Chef Tip Ticker
chef_tips = [
    "🔥 Always preheat your pan before adding oil or butter for non-stick results.",
    "🍋 A squeeze of fresh lemon juice at the end brightens heavy or rich sauces instantly.",
    "🥩 Let cooked meats rest for 5 minutes to seal in flavor and moisture.",
    "🌿 Add delicate fresh herbs (cilantro, basil, parsley) right before serving.",
    "🧂 Salt your pasta water generously—it should taste like sea water!",
    "🔪 Keep your knives sharp; a sharp knife is much safer and faster than a dull one."
]
st.info(f"👨‍🍳 **Chef's Golden Tip:** {random.choice(chef_tips)}")

# --- Central Search & Category Shortcuts ---
col_search, _ = st.columns([2, 1])
with col_search:
    search_query = st.text_input("🔍 Search recipes by name, tag, or ingredient", "", key="main_search_query")

st.markdown("##### 🍽️ Category Quick Filters")
cat_cols = st.columns(7)
categories_list = ["All", "Snacks", "Main Course", "Dessert", "Breakfast", "Rice", "Drinks"]

for idx, cat_name in enumerate(categories_list):
    btn_label = f"✨ {cat_name}" if cat_name == st.session_state["selected_category"] else cat_name
    if cat_cols[idx].button(btn_label, key=f"cat_btn_{cat_name}"):
        st.session_state["selected_category"] = cat_name
        st.session_state["current_page"] = 1
        st.rerun()

# --- Filtering Dataset Logic ---
filtered_df = recipes.copy()

if cuisine_filter != "All":
    filtered_df = filtered_df[filtered_df["cuisine"] == cuisine_filter]

if diet_filter != "All":
    filtered_df = filtered_df[filtered_df["diet"] == diet_filter]

filtered_df = filtered_df[filtered_df["prep_time"].apply(lambda x: parse_numeric(x, "min")) <= prep_filter]

if favorite_filter == "Yes":
    filtered_df = filtered_df[filtered_df["name"].isin(st.session_state["favorites"])]

if search_query:
    query = search_query.lower().strip()
    filtered_df = filtered_df[
        filtered_df["name"].str.lower().str.contains(query) |
        filtered_df["ingredients"].str.lower().str.contains(query) |
        filtered_df["tags"].str.lower().str.contains(query)
    ]

if st.session_state["selected_category"] != "All":
    filtered_df = filtered_df[filtered_df["category"].str.lower() == st.session_state["selected_category"].lower()]

if pantry_input:
    pantry_items = [p.strip().lower() for p in pantry_input.split(",") if p.strip()]
    if pantry_items:
        filtered_df = filtered_df[filtered_df["ingredients"].apply(
            lambda ing: all(item in str(ing).lower() for item in pantry_items)
        )]

st.markdown("---")

# --- Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🍽️ Recipe Gallery",
    "📅 Meal Planner",
    "🛒 Shopping List & Prices",
    "🤖 AI Chef Copilot",
    "📱 Hands-Free Kitchen View",
    "🍷 Flavor & Wine Pairings",
    "⭐ Favorites & Badges",
    "💰 Cost Analytics"
])

# ==========================================
# TAB 1: RECIPE GALLERY (WITH CLEAN PAGINATION)
# ==========================================
with tab1:
    pag_col1, pag_col2, pag_col3 = st.columns([2, 2, 1])
    with pag_col1:
        st.subheader(f"Showing {len(filtered_df)} Matching Recipes")
    with pag_col3:
        page_size = st.selectbox("Recipes per page", [6, 9, 12, 18], index=1, key="gal_page_size_select")
        
    total_pages = max(1, math.ceil(len(filtered_df) / page_size))
    
    # Boundary check for pagination
    if st.session_state["current_page"] > total_pages:
        st.session_state["current_page"] = 1
    
    curr_page = st.session_state["current_page"]
    start_idx = (curr_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered_df))
    
    page_df = filtered_df.iloc[start_idx:end_idx]

    # Render Pagination Controls Bar at Top
    p_nav1, p_nav2, p_nav3 = st.columns([1, 2, 1])
    with p_nav1:
        if st.button("⬅️ Previous Page", key="gal_btn_prev_top", disabled=(curr_page == 1)):
            st.session_state["current_page"] = curr_page - 1
            st.rerun()
    with p_nav2:
        st.markdown(f"<div style='text-align: center; font-weight: 700; font-size: 16px; margin-top: 6px;'>Page {curr_page} of {total_pages} (Displaying recipes {start_idx + 1}-{end_idx})</div>", unsafe_allow_html=True)
    with p_nav3:
        if st.button("Next Page ➡️", key="gal_btn_next_top", disabled=(curr_page == total_pages)):
            st.session_state["current_page"] = curr_page + 1
            st.rerun()

    st.markdown(" ")

    if page_df.empty:
        st.warning("No recipes match your filter criteria. Try clearing your search or adjusting filters in the sidebar!")
    else:
        grid_cols = st.columns(3)
        for i, (_, row) in enumerate(page_df.iterrows()):
            row_id = row.name  # Guaranteed unique index
            with grid_cols[i % 3]:
                st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
                
                # Image Display with Fallback
                img_url = str(row.get("image_url", "")).strip()
                if img_url and img_url.startswith("http"):
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=500&auto=format&fit=crop", use_container_width=True)

                # High-Contrast Diet Pill & Cuisine Badges
                diet_str = str(row.get("diet", "")).lower()
                diet_icon = "🟢 Veg" if diet_str == "veg" else "🔴 Non-Veg"
                st.markdown(f"**{diet_icon}** • <span class='badge-pill'>{row.get('cuisine','Global')}</span> <span class='badge-pill'>{row.get('category','Dish')}</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='recipe-title'>{row['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='recipe-meta'>⏱️ {row.get('prep_time','N/A')} | 🔥 {row.get('calories','N/A')} | 🏷️ {row.get('estimated_cost','N/A')}</div>", unsafe_allow_html=True)

                # Card Actions Row
                btn_c1, btn_c2 = st.columns(2)
                is_fav = row['name'] in st.session_state["favorites"]
                fav_label = "❤️ Favorited" if is_fav else "🤍 Favorite"
                
                if btn_c1.button(fav_label, key=f"btn_fav_{i}_{row_id}"):
                    if is_fav:
                        st.session_state["favorites"].remove(row['name'])
                    else:
                        st.session_state["favorites"].append(row['name'])
                        if len(st.session_state["favorites"]) >= 3:
                            st.session_state["unlocked_badges"].add("⭐ Recipe Collector")
                    st.rerun()

                if btn_c2.button("🛒 Add Items", key=f"btn_shop_{i}_{row_id}"):
                    ings = [ing.strip() for ing in str(row['ingredients']).split(";") if ing.strip()]
                    added_count = 0
                    for ing in ings:
                        if ing not in st.session_state["shopping_list"]:
                            st.session_state["shopping_list"].append(ing)
                            added_count += 1
                    st.success(f"Added {added_count} items to shopping list!")

                # Step-by-Step Cooking Expander
                with st.expander("👨‍🍳 Ingredients & Step-by-Step Instructions"):
                    st.markdown("#### 🥦 Ingredients")
                    ing_list = [ing.strip() for ing in str(row['ingredients']).split(";") if ing.strip()]
                    for ing in ing_list:
                        st.markdown(f"- {ing}")

                    st.markdown("#### 📖 Instructions & Timers")
                    local_steps = [s.strip() for s in str(row['instructions']).replace(".", "\n").replace(";", "\n").split("\n") if s.strip()]
                    
                    for step_idx, step_text in enumerate(local_steps, 1):
                        col_s1, col_s2, col_s3 = st.columns([3, 1.2, 1])
                        col_s1.write(f"**Step {step_idx}:** {step_text}")

                        # Interactive Step Timer
                        if col_s2.button(f"⏱️ Step {step_idx}", key=f"timer_{i}_{row_id}_{step_idx}"):
                            p_bar = st.progress(0)
                            for pct in range(100):
                                time.sleep(0.01)
                                p_bar.progress(pct + 1)
                            st.success("⏱️ Timer Complete!")

                        # Step Checkbox
                        st.session_state.get(f"done_{i}_{row_id}_{step_idx}", False)
                        col_s3.checkbox("Done", key=f"done_{i}_{row_id}_{step_idx}")

                    # Step Completion Counter
                    done_count = sum(1 for step_idx in range(1, len(local_steps) + 1) if st.session_state.get(f"done_{i}_{row_id}_{step_idx}", False))
                    if local_steps:
                        st.info(f"Progress: {done_count}/{len(local_steps)} steps completed")

                    st.markdown("---")
                    # Finish Dish Toggle & Review Form
                    prepared_flag = st.checkbox(f"✅ I have finished cooking {row['name']}!", key=f"prepared_flag_{i}_{row_id}")
                    
                    if prepared_flag:
                        st.session_state["prepared_recipes"][row['name']] = True
                        st.session_state["unlocked_badges"].add("👨‍🍳 Master Chef")
                        
                        st.write("🌟 **Rate & Review this dish:**")
                        rating_val = st.slider("Rating", 1, 5, 5, key=f"rating_slider_{i}_{row_id}")
                        comment_val = st.text_area("Your Review / Feedback", key=f"comment_text_{i}_{row_id}")
                        
                        if st.button("Submit Review", key=f"btn_review_{i}_{row_id}"):
                            st.success(f"Review saved for {row['name']}! Rated {rating_val}⭐")
                            st.balloons()
                            st.session_state["unlocked_badges"].add("🏅 Food Critic")

                st.markdown('</div>', unsafe_allow_html=True)

        # Bottom Pagination Bar
        st.markdown("---")
        b_nav1, b_nav2, b_nav3 = st.columns([1, 2, 1])
        with b_nav1:
            if st.button("⬅️ Previous Page ", key="gal_btn_prev_bot", disabled=(curr_page == 1)):
                st.session_state["current_page"] = curr_page - 1
                st.rerun()
        with b_nav2:
            st.markdown(f"<div style='text-align: center; font-weight: 700; font-size: 16px; margin-top: 6px;'>Page {curr_page} of {total_pages}</div>", unsafe_allow_html=True)
        with b_nav3:
            if st.button("Next Page ➡️ ", key="gal_btn_next_bot", disabled=(curr_page == total_pages)):
                st.session_state["current_page"] = curr_page + 1
                st.rerun()

# ==========================================
# TAB 2: WEEKLY MEAL PLANNER
# ==========================================
with tab2:
    st.header("📅 Interactive Weekly Meal Planner")
    st.caption(f"Schedule your weekly meals. Full {len(recipes)} recipe dataset is available for planning!")

    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        selected_day = st.selectbox("Select Day of the Week", list(st.session_state["meal_plan"].keys()), key="mp_day_select")
    with p_col2:
        all_recipe_names = sorted(recipes["name"].dropna().unique().tolist()) if not recipes.empty else []
        planner_recipe = st.selectbox("Pick Any Recipe from Dataset", all_recipe_names, key="mp_recipe_select")
    with p_col3:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Add to Plan", key="mp_btn_add"):
            if planner_recipe and planner_recipe not in st.session_state["meal_plan"][selected_day]:
                st.session_state["meal_plan"][selected_day].append(planner_recipe)
                st.success(f"Added {planner_recipe} to {selected_day}!")
                st.rerun()

    # Magic Auto-Plan Button
    if st.button("🎲 Auto-Generate Balanced Weekly Plan", key="mp_btn_autoplan"):
        if not recipes.empty:
            for day in st.session_state["meal_plan"].keys():
                st.session_state["meal_plan"][day] = list(recipes.sample(min(2, len(recipes)))["name"])
            st.success("Magic Weekly Meal Plan Generated!")
            st.rerun()

    st.markdown("---")
    st.subheader("🗓️ Your Weekly Schedule")

    day_cols = st.columns(7)
    for idx, (day, dishes) in enumerate(st.session_state["meal_plan"].items()):
        with day_cols[idx]:
            st.markdown(f"### **{day}**")
            if dishes:
                for d_idx, dish in enumerate(dishes):
                    st.info(f"🍲 {dish}")
                    if st.button("❌", key=f"del_mp_{day}_{d_idx}_{dish}"):
                        st.session_state["meal_plan"][day].remove(dish)
                        st.rerun()
            else:
                st.caption("No meals scheduled")

    st.markdown("---")
    st.subheader("📊 Daily Nutrition Totals & Target Breakdown")

    nutrition_data = []
    for day, dishes in st.session_state["meal_plan"].items():
        day_cal, day_prot, day_carbs, day_fat = 0, 0, 0, 0
        for dish in dishes:
            match = recipes[recipes["name"].str.strip().str.lower() == dish.strip().lower()]
            if not match.empty:
                r_row = match.iloc[0]
                day_cal += parse_numeric(r_row.get("calories", 0), "cal")
                day_prot += parse_numeric(r_row.get("protein", 0), "g")
                day_carbs += parse_numeric(r_row.get("carbs", 0), "g")
                day_fat += parse_numeric(r_row.get("fat", 0), "g")
        nutrition_data.append({"Day": day, "Calories (kcal)": day_cal, "Protein (g)": day_prot, "Carbs (g)": day_carbs, "Fat (g)": day_fat})

    nut_df = pd.DataFrame(nutrition_data)
    
    nut_c1, nut_c2 = st.columns([2, 1])
    with nut_c1:
        st.bar_chart(nut_df.set_index("Day")[["Calories (kcal)"]])
    with nut_c2:
        st.dataframe(nut_df, use_container_width=True)

# ==========================================
# TAB 3: SHOPPING LIST & PRICING
# ==========================================
with tab3:
    st.header("🛒 Smart Grocery Shopping List")
    st.caption(f"Price estimations active for Pincode: **{st.session_state['dashboard_pincode']}**")

    # Custom Item Input
    c_add1, c_add2 = st.columns([3, 1])
    with c_add1:
        custom_item = st.text_input("Add custom item to shopping list", "", key="shop_custom_item_input")
    with c_add2:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Add Custom Item", key="shop_btn_add_custom"):
            if custom_item and custom_item not in st.session_state["shopping_list"]:
                st.session_state["shopping_list"].append(custom_item.strip())
                st.success(f"Added '{custom_item}'!")
                st.rerun()

    if not st.session_state["shopping_list"]:
        st.info("🛒 Your shopping list is empty! Click '🛒 Add Items' on any recipe card in the Gallery.")
    else:
        st.subheader("📦 Grouped Ingredients with Checkoff")

        cat_items = {"🥦 Produce & Veggies": [], "🥛 Dairy & Refrigerated": [], "🧂 Spices & Seasoning": [], "🍞 Bakery & Grains": [], "📦 General Items": []}

        for item in set(st.session_state["shopping_list"]):
            item_l = item.lower()
            if any(v in item_l for v in ["tomato", "onion", "potato", "spinach", "carrot", "cucumber", "garlic", "lemon", "apple", "banana", "grapes", "herbs"]):
                cat_items["🥦 Produce & Veggies"].append(item)
            elif any(d in item_l for d in ["paneer", "milk", "cheese", "yogurt", "butter", "cream", "ghee"]):
                cat_items["🥛 Dairy & Refrigerated"].append(item)
            elif any(s in item_l for s in ["salt", "pepper", "masala", "chili", "turmeric", "spices", "oil", "sugar"]):
                cat_items["🧂 Spices & Seasoning"].append(item)
            elif any(g in item_l for g in ["rice", "bread", "flour", "pasta", "pita", "noodle"]):
                cat_items["🍞 Bakery & Grains"].append(item)
            else:
                cat_items["📦 General Items"].append(item)

        col_g1, col_g2 = st.columns(2)
        idx_counter = 0
        for cat_name, item_group in cat_items.items():
            if item_group:
                idx_counter += 1
                target_col = col_g1 if idx_counter % 2 != 0 else col_g2
                with target_col:
                    st.markdown(f"#### {cat_name}")
                    for item_name in item_group:
                        st.checkbox(f"{item_name}", key=f"chk_shop_{item_name}")

        st.markdown("---")
        st.subheader("💰 Live Grocery Price Estimate")

        base_item_prices = {
            "paneer": 120, "chicken": 220, "rice": 80, "bread": 45, "cheese": 140, "milk": 35,
            "tomato": 40, "onion": 35, "potato": 30, "spices": 50, "butter": 60, "mutton": 450,
            "fish": 300, "pasta": 90, "flour": 55, "oil": 160, "yogurt": 40, "chickpeas": 70, "salmon": 420
        }

        estimated_total = 0
        price_rows = []
        for item_name in set(st.session_state["shopping_list"]):
            matched_price = 45
            for key_term, price_val in base_item_prices.items():
                if key_term in item_name.lower():
                    matched_price = price_val
                    break
            estimated_total += matched_price
            price_rows.append({"Ingredient": item_name, "Estimated Price": f"₹{matched_price}"})

        p_col_left, p_col_right = st.columns([2, 1])
        with p_col_left:
            st.table(pd.DataFrame(price_rows))
        with p_col_right:
            st.metric("💰 Total Estimated Cart Cost", f"₹{estimated_total}")
            
            if st.button("💾 Save Shopping Expense to History", key="shop_btn_save_expense"):
                st.session_state["cost_history"].append({
                    "date": datetime.date.today().isoformat(),
                    "cost": estimated_total
                })
                st.session_state["unlocked_badges"].add("💰 Smart Shopper")
                st.success("Logged expense to Cost Analytics!")

            if st.button("🗑️ Clear Shopping List", key="shop_btn_clear"):
                st.session_state["shopping_list"] = []
                st.rerun()

        st.download_button(
            "📥 Export Shopping List (.txt)",
            "\n".join(st.session_state["shopping_list"]),
            file_name="shopping_list.txt",
            key="shop_btn_download_list"
        )

# ==========================================
# TAB 4: AI CHEF COPILOT
# ==========================================
with tab4:
    st.header("🤖 AI Kitchen Assistant & Culinary Copilot")
    st.caption("Ask questions about cooking, substitutions, leftover ingredients, or dietary advice.")

    st.write("💡 **Quick Question Shortcuts:**")
    qp_cols = st.columns(5)
    if qp_cols[0].button("🥚 Egg Substitute?", key="ai_qp_egg"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": "What can I use as a substitute for eggs in baking?"})
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": "💡 **Egg Substitutes in Baking:**\n- **Mashed Banana:** 1/2 banana per egg (sweet recipes)\n- **Applesauce:** 1/4 cup per egg (adds moisture)\n- **Yogurt/Curd:** 1/4 cup per egg\n- **Flax Egg:** 1 tbsp ground flax + 3 tbsp water"})
        st.rerun()

    if qp_cols[1].button("🌶️ Less Spicy?", key="ai_qp_spicy"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": "How do I fix a dish that is too spicy?"})
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": "🌶️ **Fixing Overly Spicy Dishes:**\n- **Dairy:** Add heavy cream, yogurt, or coconut milk.\n- **Acid:** Squeeze fresh lemon juice to neutralize heat.\n- **Sweetness:** Add 1/2 tsp sugar or honey."})
        st.rerun()

    if qp_cols[2].button("🍷 Wine Pairing?", key="ai_qp_wine"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": "What beverage pairs well with Biryani or Curry?"})
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": "🍷 **Pairing Ideas:**\n- **Beverage:** Chilled Mango Lassi or Mint Limeade.\n- **Wine:** Off-dry Riesling or Gewürztraminer balances spice perfectly!"})
        st.rerun()

    if qp_cols[3].button("⏱️ 15-Min Meal?", key="ai_qp_quick"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": "Suggest a quick 15-minute meal recipe."})
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": "⏱️ **Quick 15-Min Idea: Avocado Toast or Veg Cheese Sandwich!**\n- Slice veggies & paneer/cheese.\n- Butter bread, toast on tawa with chat masala till crispy."})
        st.rerun()

    if qp_cols[4].button("🥑 Keto Option?", key="ai_qp_keto"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": "Recommend a high protein keto dish."})
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": "🥑 **Keto Recommendation:** Teriyaki Salmon, Palak Paneer, or Grilled Chicken Tikka with extra green veggies!"})
        st.rerun()

    st.markdown("---")

    for msg in st.session_state["ai_chat_history"]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    user_ai_input = st.chat_input("Ask Chef AI anything (e.g. 'How do I store fresh basil?')")
    if user_ai_input:
        st.session_state["ai_chat_history"].append({"role": "user", "content": user_ai_input})
        
        inp_l = user_ai_input.lower()
        if "substitute" in inp_l or "replace" in inp_l:
            reply = "👨‍🍳 **Substitution Tip:** Use coconut cream for dairy cream, olive oil for butter, or cornstarch for flour as a thickener!"
        elif "leftover" in inp_l or "pantry" in inp_l:
            reply = "👨‍🍳 **Leftover Idea:** Make a quick Veggie Stir-Fry, Fried Rice, or Frittata using any leftover vegetables in your fridge!"
        else:
            reply = f"👨‍🍳 **Chef AI Advice:** Regarding '{user_ai_input}'—cooking on medium heat, seasoning in stages, and using fresh herbs will give you restaurant-quality results!"
        
        st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()

# ==========================================
# TAB 5: HANDS-FREE KITCHEN VIEW MODE
# ==========================================
with tab5:
    st.header("📱 Hands-Free Kitchen Cooking Mode")
    st.caption("High-contrast step-by-step display for active cooking in the kitchen!")

    all_names = sorted(recipes["name"].dropna().unique().tolist()) if not recipes.empty else []
    
    if all_names:
        selected_k_recipe = st.selectbox("Select Active Recipe to Cook", all_names, key="kv_recipe_select")
        match = recipes[recipes["name"].str.strip().str.lower() == selected_k_recipe.strip().lower()]
        
        if not match.empty:
            k_row = match.iloc[0]
            k_steps = [s.strip() for s in str(k_row['instructions']).replace(".", "\n").replace(";", "\n").split("\n") if s.strip()]
            
            st.markdown(f"## 🍳 Cooking: **{k_row['name']}**")
            st.markdown(f"**Prep Time:** {k_row.get('prep_time','N/A')} | **Cuisine:** {k_row.get('cuisine','Global')} | **Serving:** {k_row.get('serving_size','2')}")
            
            if k_steps:
                curr_idx = st.session_state.get("kitchen_step_index", 0)
                if curr_idx >= len(k_steps):
                    curr_idx = len(k_steps) - 1
                if curr_idx < 0:
                    curr_idx = 0

                st.markdown(f"""
                    <div style="background-color: {'#1E293B' if dark_mode else '#FFEDD5'}; border-left: 8px solid #EA580C; padding: 24px; border-radius: 14px; margin: 20px 0;">
                        <h3 style="color: {'#F59E0B' if dark_mode else '#C2410C'}; margin-top: 0;">Step {curr_idx + 1} of {len(k_steps)}</h3>
                        <p style="font-size: 26px; font-weight: 700; line-height: 1.5; color: {'#F8FAFC' if dark_mode else '#0F172A'};">{k_steps[curr_idx]}</p>
                    </div>
                """, unsafe_allow_html=True)

                nav_c1, nav_c2, nav_c3 = st.columns([1, 1, 2])
                with nav_c1:
                    if st.button("⬅️ Previous Step", key="kv_btn_prev", disabled=(curr_idx == 0)):
                        st.session_state["kitchen_step_index"] = curr_idx - 1
                        st.rerun()
                with nav_c2:
                    if st.button("Next Step ➡️", key="kv_btn_next", disabled=(curr_idx == len(k_steps) - 1)):
                        st.session_state["kitchen_step_index"] = curr_idx + 1
                        st.rerun()
                with nav_c3:
                    if st.button("⏱️ Start 1-Min Step Timer", key="kv_btn_timer"):
                        t_bar = st.progress(0)
                        for sec in range(60):
                            time.sleep(0.01)
                            t_bar.progress((sec + 1) / 60)
                        st.success("🔔 Step Timer Complete!")

# ==========================================
# TAB 6: FLAVOR & WINE PAIRINGS
# ==========================================
with tab6:
    st.header("🍷 Flavor, Side Dish & Wine Pairing Engine")
    st.caption("Discover perfect side dishes, beverage pairings, and storage advice for any recipe.")

    if not recipes.empty:
        pair_recipe_name = st.selectbox("Choose Recipe for Pairing Recommendations", sorted(recipes["name"].unique()), key="pair_select_recipe")
        p_match = recipes[recipes["name"] == pair_recipe_name]
        
        if not p_match.empty:
            p_row = p_match.iloc[0]
            
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                st.subheader("🍷 Beverage & Wine Pairing")
                st.info(f"**Recommended:** {p_row.get('pairing', 'Chilled White Wine or Mint Lemonade')}")
            with p_col2:
                st.subheader("🥗 Ideal Side Dish")
                st.success(f"**Pairs Great With:** {p_row.get('occasion', 'Fresh Garden Salad or Garlic Bread')}")
            with p_col3:
                st.subheader("❄️ Storage & Reheating")
                st.warning(f"**Storage Tip:** {p_row.get('storage_tips', 'Refrigerate in an airtight container for 2 days.')}")

            st.markdown("---")
            st.markdown(f"### 🍽️ Culinary Profile for **{p_row['name']}**")
            st.write(f"- **Cuisine:** {p_row.get('cuisine', 'Global')}")
            st.write(f"- **Equipment Needed:** {p_row.get('equipment', 'Standard Pan')}")
            st.write(f"- **Allergen Alert:** {p_row.get('allergens', 'None')}")
            st.write(f"- **Tags:** {p_row.get('tags', 'Delicious')}")

# ==========================================
# TAB 7: FAVORITES & BADGES
# ==========================================
with tab7:
    st.header("⭐ Saved Favorites & Culinary Badges")
    
    fav_col1, fav_col2 = st.columns([2, 1])
    with fav_col1:
        st.subheader("❤️ My Saved Favorites")
        if st.session_state["favorites"]:
            for f_idx, fav_item in enumerate(st.session_state["favorites"]):
                f_c1, f_c2 = st.columns([3, 1])
                f_c1.write(f"⭐ **{fav_item}**")
                if f_c2.button("Remove", key=f"btn_rem_fav_{f_idx}_{fav_item}"):
                    st.session_state["favorites"].remove(fav_item)
                    st.rerun()
            
            st.download_button(
                "⬇️ Export Favorites (.txt)",
                "\n".join(st.session_state["favorites"]),
                file_name="favorites.txt",
                key="btn_download_favs"
            )
        else:
            st.info("No favorites added yet. Click 🤍 Favorite on any recipe in the Gallery!")

    with fav_col2:
        st.subheader("🏆 Unlocked Achievements")
        all_possible_badges = {
            "🌱 Kitchen Novice": "Started your cooking journey",
            "⭐ Recipe Collector": "Saved 3+ favorite recipes",
            "👨‍🍳 Master Chef": "Marked a recipe as prepared",
            "🏅 Food Critic": "Submitted a detailed recipe review",
            "💰 Smart Shopper": "Saved expenses to cost tracker"
        }
        for b_title, b_desc in all_possible_badges.items():
            if b_title in st.session_state["unlocked_badges"]:
                st.success(f"**{b_title}**\n\n_{b_desc}_")
            else:
                st.caption(f"🔒 **{b_title}** ({b_desc})")

    st.markdown("---")
    st.subheader("🔥 Trending Recipes Leaderboard")
    if not recipes.empty:
        sample_trending = recipes.head(6)[["name", "cuisine", "calories", "estimated_cost"]]
        st.table(sample_trending)

# ==========================================
# TAB 8: COST ANALYTICS & EXPENSE TRACKER
# ==========================================
with tab8:
    st.header("💰 Grocery Cost Analytics & History")
    st.caption("Track your grocery expenditures over time.")

    if st.session_state["cost_history"]:
        cost_df = pd.DataFrame(st.session_state["cost_history"])
        cost_df["date"] = pd.to_datetime(cost_df["date"])
        cost_df = cost_df.sort_values("date")

        ac1, ac2, ac3 = st.columns(3)
        total_spent = cost_df["cost"].sum()
        avg_spent = cost_df["cost"].mean()
        ac1.metric("💰 Total Spent", f"₹{total_spent}")
        ac2.metric("📊 Avg Order Cost", f"₹{int(avg_spent)}")
        ac3.metric("🧾 Total Orders Logged", len(cost_df))

        st.markdown("### 📈 Grocery Expenditure Over Time")
        st.line_chart(cost_df.set_index("date")["cost"])

        st.markdown("### 📜 Expense Log Table")
        st.dataframe(cost_df, use_container_width=True)
    else:
        st.info("No expense data logged yet. Save expenses in the Shopping List tab!")
