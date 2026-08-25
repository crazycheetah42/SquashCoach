import flet as ft
import re
from logic import (
    add_match,
    get_matches,
    get_signed_in_user,
    login_desktop_user,
    sign_out_user,
    summarize_score,
    summarize_matches_by_month,
)

async def main(page: ft.Page):
    page.title = "SquashCoach"
    page.favicon = "favicon.png"
    page.window.resizable = True
    page.padding = 0
    page.bgcolor = ft.Colors.SURFACE
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.TEAL)

    signed_in_user = get_signed_in_user()

    def show_sign_in_dialog():
        def sign_in_with_google(_):
            nonlocal signed_in_user
            signed_in_user = login_desktop_user()
            sign_in_dialog.open = False
            update_profile_action()
            refresh_dashboard()
            page.update()

        sign_in_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Sign in to SquashCoach"),
            content=ft.Text("Use your Google account to sign in."),
            actions=[
                ft.Button(
                    "Sign in with Google",
                    icon=ft.Icons.LOGIN,
                    on_click=sign_in_with_google,
                ),
                ft.TextButton("Cancel", on_click=lambda _: (setattr(sign_in_dialog, "open", False), page.update())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = sign_in_dialog
        page.show_dialog(sign_in_dialog)

    def show_profile_dialog(_):
        def sign_out(_):
            nonlocal signed_in_user
            sign_out_user()
            signed_in_user = None
            profile_dialog.open = False
            update_profile_action()
            refresh_dashboard()
            page.update()
            show_sign_in_dialog()

        profile_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Google Account"),
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.CircleAvatar(
                        foreground_image_src=signed_in_user.get("photo_url"),
                        content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
                        radius=32,
                    ),
                    ft.Text(signed_in_user.get("display_name") or "Google user", weight=ft.FontWeight.BOLD),
                    ft.Text(signed_in_user.get("email") or ""),
                ],
            ),
            actions=[ft.Button("Sign out", icon=ft.Icons.LOGOUT, on_click=sign_out)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = profile_dialog
        page.show_dialog(profile_dialog)

    def open_profile_or_sign_in(_):
        if signed_in_user:
            show_profile_dialog(None)
        else:
            show_sign_in_dialog()

    profile_action = ft.IconButton(on_click=open_profile_or_sign_in)

    def update_profile_action():
        if signed_in_user:
            profile_action.icon = ft.CircleAvatar(
                foreground_image_src=signed_in_user.get("photo_url"),
                content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE),
                radius=18,
            )
            profile_action.icon_color = None
            profile_action.tooltip = "Open Google Account"
        else:
            profile_action.icon = ft.Icons.ACCOUNT_CIRCLE
            profile_action.icon_color = None
            profile_action.tooltip = "Sign in with Google"

    update_profile_action()

    page.appbar = ft.AppBar(
        title=ft.Text("SquashCoach", weight=ft.FontWeight.BOLD),
        actions=[profile_action],
    )

    def section_title(title, subtitle):
        return ft.Column(
            spacing=4,
            controls=[
                ft.Text(title, size=22, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        )

    performance_summary = ft.Text(color=ft.Colors.ON_SURFACE_VARIANT)
    performance_graph = ft.Row(
        height=180,
        spacing=16,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
    dashboard_status = ft.Text(color=ft.Colors.ON_SURFACE_VARIANT)

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
                performance_summary,
                performance_graph,
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
                                    dashboard_status,
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    def refresh_dashboard():
        match_table.rows = []
        performance_graph.controls = []
        performance_summary.value = ""
        dashboard_status.value = ""

        if not signed_in_user:
            performance_summary.value = "Sign in to see your performance."
            dashboard_status.value = "Sign in to load your recent matches."
            return

        try:
            matches = get_matches(signed_in_user)
        except Exception as error:
            performance_summary.value = "Performance data is unavailable."
            dashboard_status.value = f"Unable to load matches: {error}"
            return

        summaries = []
        for match in matches:
            try:
                summary = summarize_score(match["score"])
            except (AttributeError, TypeError, ValueError):
                continue
            summaries.append((match, summary))

        wins = sum(summary["result"] == "Won" for _, summary in summaries)
        losses = sum(summary["result"] == "Lost" for _, summary in summaries)
        performance_summary.value = f"{wins} wins  |  {losses} losses  |  {len(summaries)} matches"

        for match, summary in summaries[:10]:
            created_at = match.get("created_at")
            date_label = created_at.strftime("%b %d") if created_at else "Recent"
            match_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(date_label)),
                        ft.DataCell(ft.Text(match["score"])),
                        ft.DataCell(
                            ft.Text(
                                summary["result"],
                                color=ft.Colors.TEAL if summary["result"] == "Won" else ft.Colors.ERROR,
                            )
                        ),
                    ]
                )
            )

        graph_matches = summarize_matches_by_month([match for match, _ in summaries])[-8:]
        maximum_games = max(
            (summary["wins"] + summary["losses"] for summary in graph_matches),
            default=1,
        )
        for summary in graph_matches:
            performance_graph.controls.append(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.END,
                            spacing=3,
                            controls=[
                                ft.Container(
                                    width=14,
                                    height=max(12, 120 * summary["wins"] / maximum_games),
                                    bgcolor=ft.Colors.TEAL,
                                ),
                                ft.Container(
                                    width=14,
                                    height=max(12, 120 * summary["losses"] / maximum_games),
                                    bgcolor=ft.Colors.ERROR,
                                ),
                            ],
                        ),
                        ft.Text(summary["label"], size=11),
                    ],
                )
            )

        if not summaries:
            dashboard_status.value = "No matches have been logged yet."

    refresh_dashboard()

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
                if not signed_in_user:
                    score_feedback.value = "Sign in before logging a match."
                else:
                    try:
                        match_id = add_match(signed_in_user, score)
                        refresh_dashboard()
                        score_feedback.color = ft.Colors.TEAL
                        score_feedback.value = f"Match saved ({match_id}). Result: {'Won' if wins > losses else 'Lost'} ({wins}-{losses}) | Games: {' '.join(results)}"
                    except Exception as error:
                        score_feedback.value = f"Unable to save match: {error}"
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
                            ft.Row(controls=[score_input, ft.Button("Save match", icon=ft.Icons.SAVE, on_click=log_match)]),
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
                    tab_alignment=ft.TabAlignment.CENTER,
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

    page.window.width = 1280
    page.window.height = 768
    page.update()
    await page.window.center()

ft.run(main)