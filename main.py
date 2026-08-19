import flet as ft
import re
import firebase_admin as fb

def main(page: ft.Page):
    page.title = "SquashCoach"
    page.padding = 0
    page.bgcolor = ft.Colors.SURFACE
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.TEAL)

    def section_title(title, subtitle):
        return ft.Column(
            spacing=4,
            controls=[
                ft.Text(title, size=22, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        )

    graph_shell = ft.Container(
        height=280,
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Icon(ft.Icons.SHOW_CHART, size=44, color=ft.Colors.TEAL),
                ft.Text("Your performance graph will appear here", weight=ft.FontWeight.W_500),
                ft.Text("Log matches to start tracking progress.", color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        ),
    )

    match_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Score")),
            ft.DataColumn(ft.Text("Result")),
        ],
        rows=[],
        width=float("inf"),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        heading_row_color=ft.Colors.SURFACE_CONTAINER_LOW,
    )

    dashboard = ft.Container(
        expand=True,
        padding=ft.Padding(left=32, right=32, top=28, bottom=28),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=28,
            controls=[
                section_title("Dashboard", "A clear view of your squash progress."),
                ft.Column(
                    spacing=12,
                    controls=[ft.Text("Performance", size=16, weight=ft.FontWeight.BOLD), graph_shell],
                ),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text("Recent matches", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            padding=16,
                            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=8,
                            content=ft.Column(
                                spacing=12,
                                controls=[
                                    match_table,
                                    ft.Text("Match data will be shown here once it is available.", color=ft.Colors.ON_SURFACE_VARIANT),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    score_input = ft.TextField(
        label="Match score",
        hint_text="11-9, 9-11, 13-11, 12-10",
        expand=True,
    )
    score_feedback = ft.Text()

    def log_match(e):
        score_feedback.color = ft.Colors.ERROR
        score_feedback.value = ""
        score = score_input.value.strip()
        games = [game.strip() for game in score.split(",") if game.strip()]
        if not games or any(not re.fullmatch(r"\d+\s*-\s*\d+", game) for game in games):
            score_feedback.value = "Enter scores like 11-9, 9-11, 13-11."
        else:
            results = []
            for game in games:
                first, second = (int(value.strip()) for value in game.split("-"))
                if first == second:
                    score_feedback.value = "A game score cannot be tied."
                    break
                results.append("W" if first > second else "L")
            else:
                wins = results.count("W")
                losses = results.count("L")
                score_feedback.color = ft.Colors.TEAL
                score_feedback.value = f"Match preview: {'Won' if wins > losses else 'Lost'} ({wins}-{losses}) | Games: {' '.join(results)}"
        page.update()

    log_match_view = ft.Container(
        expand=True,
        padding=ft.Padding(left=32, right=32, top=28, bottom=28),
        content=ft.Column(
            spacing=24,
            controls=[
                section_title("Log a Match", "Record each game score in the order it was played."),
                ft.Container(
                    width=700,
                    padding=24,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=8,
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Text("Match score", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Separate games with commas. The higher number in each game is the winner.", color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Row(controls=[score_input, ft.Button("Preview match", icon=ft.Icons.CHECK, on_click=log_match)]),
                            score_feedback,
                        ],
                    ),
                ),
            ],
        ),
    )

    placeholder = lambda title: ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[ft.Text(title, size=22, weight=ft.FontWeight.BOLD), ft.Text("This section is coming soon.", color=ft.Colors.ON_SURFACE_VARIANT)],
        ),
    )

    tabs = ft.Tabs(
        length=4,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Dashboard", icon=ft.Icons.DASHBOARD),
                        ft.Tab(label="Log a Match", icon=ft.Icons.SPORTS_TENNIS),
                        ft.Tab(label="Log Training Session", icon=ft.Icons.EDIT_NOTE),
                        ft.Tab(label="Training", icon=ft.Icons.FITNESS_CENTER),
                    ],
                    scrollable=True,
                ),
                ft.TabBarView(controls=[dashboard, log_match_view, placeholder("Log Training Session"), placeholder("Training")], expand=True),
            ],
        ),
    )
    page.add(tabs)

ft.run(main)