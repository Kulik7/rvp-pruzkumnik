"""
Shiny app pro vizualizaci RVP - Verze s interaktivní tabulkou a metodickou podporou
"""

import pandas as pd
import numpy as np
from shiny import ui, render, reactive, App
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget
import textwrap

# --- 1. AKTUALIZOVANÁ CESTA K SOUBORŮM ---
DATA_DIR = Path(__file__).parent / "processed"


def load_data():
    df = pd.read_csv(DATA_DIR / "learning_outcomes.csv")
    sim_matrix = np.load(DATA_DIR / "similarity_matrix.npy")
    return df, sim_matrix


print("Načítám data pro aplikaci...")
df, sim_matrix = load_data()


# --- PŘÍPRAVA DAT ---
def extrahuj_rocnik(kod):
    try:
        casti = str(kod).split("-")
        if len(casti) >= 4:
            return casti[3]
        return "Neznámý"
    except:
        return "Neznámý"


df["rok"] = df["kod"].apply(extrahuj_rocnik)
df["orig_index"] = df.index

rocniky_choices = ["Všechny"] + sorted(df["rok"].unique().tolist())
obory_choices = ["Všechny"] + sorted(df["obor"].unique().tolist())
df["popis_kratky"] = df["popis"].apply(
    lambda x: str(x)[:120] + "..." if len(str(x)) > 120 else str(x)
)
df["popis_kratky"] = df["popis_kratky"].apply(
    lambda x: "<br>".join(textwrap.wrap(x, width=60))
)

# === UŽIVATELSKÉ ROZHRANÍ (UI) ===
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            "rocnik_select",
            "Ročník/Stupeň:",
            choices=rocniky_choices,
            selected="Všechny",
        ),
        ui.input_select(
            "obor_select", "Předmět (Obor):", choices=obory_choices, selected="Všechny"
        ),
        ui.hr(),
        ui.p("Vyberte ze seznamu, nebo klikněte na bod v mapě / řádek v tabulce:"),
        ui.input_select("kod_select", "Výchozí cíl (KOD):", choices={}, width="100%"),
        ui.hr(),
        ui.input_checkbox(
            "only_other_subjects", "💡 V tabulce hledat jen v jiných předmětech", True
        ),
        width=300,
        bg="#f8f9fa",
    ),
    ui.layout_columns(
        ui.navset_card_underline(
            ui.nav_panel(
                "Sémantická mapa (Galaxie)",
                ui.card(
                    output_widget("umap_plot", width="100%", height="750px"),
                    full_screen=True,
                ),
            ),
            ui.nav_panel(
                "Návrhy na mezipředmětové vazby",
                ui.card(
                    ui.output_data_frame("similar_kods_table"),
                    full_screen=True,
                ),
            ),
        ),
        ui.card(
            ui.card_header("🔍 Detail vybraného cíle", class_="bg-primary text-white"),
            ui.output_ui("pravy_panel_detail"),
            bg="#fdfdfd",
        ),
        col_widths=[8, 4],
        fill=True,  # <-- SLOUPEČKY VYPLNÍ CELOU VÝŠKU STRÁNKY
    ),
    title="RVP Průzkumník: Interaktivní síť znalostí",
    fillable=True,  # <-- CELÁ APLIKACE SE ROZTÁHNE NA 100 % VÝŠKY OKNA
)


# === LOGIKA APLIKACE (SERVER) ===
def server(input, output, session):

    vybrany_z_mapy = reactive.Value(None)
    # Pomocná proměnná pro mapování řádků tabulky na reálné indexy
    zobrazené_indexy_v_tabulce = reactive.Value([])

    @reactive.Calc
    def filtered_data():
        rocnik = input.rocnik_select()
        obor = input.obor_select()
        temp_df = df
        if rocnik != "Všechny":
            temp_df = temp_df[temp_df["rok"] == rocnik]
        if obor != "Všechny":
            temp_df = temp_df[temp_df["obor"] == obor]
        return temp_df

    # Synchronizace dropdownu
    @reactive.Effect
    def update_kods():
        plot_df = filtered_data()
        choices = {
            str(row["orig_index"]): f"{row['kod']} - {row['obor']}"
            for _, row in plot_df.iterrows()
        }
        current_sel = input.kod_select()
        if current_sel in choices:
            ui.update_select("kod_select", choices=choices, selected=current_sel)
        else:
            ui.update_select("kod_select", choices=choices)

    # --- KOUZLO: Synchronizace kliknutí v tabulce ---
    @reactive.Effect
    @reactive.event(input.similar_kods_table_selected_rows)
    def vyber_z_tabulky():
        rows = input.similar_kods_table_selected_rows()
        if rows:
            # Získáme index řádku v tabulce a převedeme ho na původní index v DF
            row_idx = rows[0]
            orig_idx = zobrazené_indexy_v_tabulce.get()[row_idx]
            ui.update_select("kod_select", selected=str(orig_idx))

    # Synchronizace kliknutí v mapě
    @reactive.Effect
    def sync_click_to_dropdown():
        clicked_idx = vybrany_z_mapy.get()
        if clicked_idx is not None:
            ui.update_select("kod_select", selected=clicked_idx)

    # Pravý panel s detaily a proklikem
    @output
    @render.ui
    def pravy_panel_detail():
        idx_str = input.kod_select()
        if not idx_str:
            return ui.div(
                ui.p("Zvolte cíl v mapě nebo v tabulce.", class_="text-muted")
            )

        radek = df.iloc[int(idx_str)]
        kod = str(radek["kod"])

        # URL adresy
        url_ovu = f"https://prohlednout.rvp.cz/ovu/{kod.lower()}"
        url_metodika = f"https://prohlednout.rvp.cz/metodika/{kod.lower()}"

        return ui.div(
            ui.h5(kod, class_="text-primary"),
            ui.p(ui.strong("Obor: "), radek["obor"]),
            ui.p(ui.strong("Stupeň: "), radek["rok"]),
            ui.hr(),
            ui.p(ui.strong("Znění:")),
            ui.markdown(f"*{radek['popis']}*"),
            ui.hr(),
            ui.div(
                ui.a(
                    "🔗 Otevřít kartu OVU",
                    href=url_ovu,
                    target="_blank",
                    class_="btn btn-outline-primary w-100 mb-2",
                ),
                ui.a(
                    "📚 Metodická podpora",
                    href=url_metodika,
                    target="_blank",
                    class_="btn btn-primary w-100",
                ),
            ),
        )

    # Interaktivní mapa
    @output
    @render_widget
    def umap_plot():
        plot_df = filtered_data()
        if plot_df.empty:
            return go.FigureWidget()

        fig_px = px.scatter(
            plot_df,
            x="umap_x",
            y="umap_y",
            color="obor",
            hover_name="kod",
            custom_data=["orig_index", "obor", "rok", "popis_kratky"],
            title="Sémantická mapa cílů",
        )

        fig_px.update_traces(
            hovertemplate="<b>Kód: %{hovertext}</b><br><b>Obor:</b> %{customdata[1]}<br><br><b>Znění:</b><br>%{customdata[3]}<extra></extra>",
            marker=dict(
                size=11, opacity=0.8, line=dict(width=1, color="DarkSlateGrey")
            ),
        )

        fig = go.FigureWidget(fig_px)

        def handle_click(trace, points, state):
            if points.point_inds:
                orig_index = trace.customdata[points.point_inds[0]][0]
                vybrany_z_mapy.set(str(orig_index))

        for trace in fig.data:
            trace.on_click(handle_click)

        fig.update_layout(
            template="plotly_white",
            margin=dict(l=0, r=0, t=40, b=0),
            autosize=True,
            height=750,
        )

        idx_str = input.kod_select()
        if idx_str and int(idx_str) in plot_df["orig_index"].values:
            vybrany_idx = int(idx_str)
            fig.add_trace(
                go.Scatter(
                    x=[df.iloc[vybrany_idx]["umap_x"]],
                    y=[df.iloc[vybrany_idx]["umap_y"]],
                    mode="markers",
                    marker=dict(
                        color="#ffdb0e",
                        symbol="star",
                        size=15,
                        line=dict(color="black", width=1),
                    ),
                    name="Vybraný cíl",
                    hoverinfo="skip",
                )
            )
        return fig

    # --- NOVINKA: Klikatelná tabulka podobností ---
    @output
    @render.data_frame
    def similar_kods_table():
        idx_str = input.kod_select()
        if not idx_str:
            return render.DataGrid(pd.DataFrame())

        vybrany_idx = int(idx_str)
        vybrany_obor = df.iloc[vybrany_idx]["obor"]
        similarities = sim_matrix[vybrany_idx]

        sim_pairs = [(i, similarities[i]) for i in range(len(df)) if i != vybrany_idx]

        if input.only_other_subjects():
            sim_pairs = [
                pair for pair in sim_pairs if df.iloc[pair[0]]["obor"] != vybrany_obor
            ]

        sim_pairs.sort(key=lambda x: x[1], reverse=True)
        top_indices = [x[0] for x in sim_pairs[:15]]  # Ukážeme 15 nejpodobnějších

        # Uložíme si indexy pro pozdější synchronizaci kliknutí
        zobrazené_indexy_v_tabulce.set(top_indices)

        result_df = pd.DataFrame(
            {
                "Podobnost": [f"{similarities[i]*100:.1f} %" for i in top_indices],
                "KOD": df.iloc[top_indices]["kod"].values,
                "Znění": df.iloc[top_indices]["popis"].values,
            }
        )

        # Použijeme DataGrid s výběrem jednoho řádku
        return render.DataGrid(
            result_df, selection_mode="row", width="100%", height="100%"
        )


app = App(app_ui, server)
