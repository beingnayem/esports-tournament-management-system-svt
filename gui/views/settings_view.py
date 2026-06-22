import customtkinter as ctk
import json
import os
from gui.theme import ThemeManager, ACCENT_PRESETS, H1, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, PAD_XL, RADIUS
from gui.components.toast import ToastManager
from gui.components.modal import Modal
from patterns.factory import TournamentFactory


class SettingsView(ctk.CTkFrame):

    def __init__(self, parent, service=None, app=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service
        self._app = app

        container = ctk.CTkScrollableFrame(
            self, fg_color=tm.c("BG_BASE"), corner_radius=0,
        )
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        title = ctk.CTkLabel(
            container, text="Settings", font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        title.pack(fill="x", pady=(0, PAD_LG))

        self._section_header(container, "Tournament Configuration")

        config_frame = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                     corner_radius=RADIUS)
        config_frame.pack(fill="x", pady=(0, PAD_LG))

        config_inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        self._field_label(config_inner, "Tournament Name")
        self._name_entry = ctk.CTkEntry(
            config_inner, placeholder_text="EsportsHub Tournament",
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._name_entry.pack(fill="x", pady=(0, PAD_MD))
        if service:
            self._name_entry.insert(0, service.tournament_name)

        self._field_label(config_inner, "Tournament Type")
        types = TournamentFactory.available_types()
        self._type_menu = ctk.CTkOptionMenu(
            config_inner, values=types, width=250, height=36,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            button_hover_color=tm.c("ACCENT_DIM"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
        )
        self._type_menu.set("Single Elimination")
        self._type_menu.pack(fill="x", pady=(0, PAD_MD))

        self._field_label(config_inner, "Game Title")
        self._game_entry = ctk.CTkEntry(
            config_inner, placeholder_text="CS2",
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._game_entry.insert(0, "CS2")
        self._game_entry.pack(fill="x", pady=(0, PAD_MD))

        self._field_label(config_inner, "Max Teams")

        slider_frame = ctk.CTkFrame(config_inner, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(0, PAD_MD))

        self._max_teams_var = ctk.IntVar(value=8)
        self._max_teams_label = ctk.CTkLabel(
            slider_frame, text="8", font=H3,
            text_color=tm.c("ACCENT"), width=40,
        )
        self._max_teams_label.pack(side="right")

        self._max_teams_slider = ctk.CTkSlider(
            slider_frame, from_=4, to=32,
            number_of_steps=14,
            variable=self._max_teams_var,
            fg_color=tm.c("BG_ELEVATED"),
            progress_color=tm.c("ACCENT"),
            button_color=tm.c("ACCENT"),
            button_hover_color=tm.c("ACCENT_HOVER"),
            command=self._on_slider_change,
        )
        self._max_teams_slider.pack(fill="x", side="left", expand=True, padx=(0, PAD_SM))

        self._start_btn = ctk.CTkButton(
            config_inner, text="🚀 Start Tournament", height=40,
            fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
            text_color="#FFFFFF", font=H3, corner_radius=8,
            command=self._start_tournament,
        )
        self._start_btn.pack(fill="x", pady=(PAD_SM, 0))

        self._section_header(container, "Appearance")

        appearance_frame = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                         corner_radius=RADIUS)
        appearance_frame.pack(fill="x", pady=(0, PAD_LG))

        app_inner = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        app_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        theme_row = ctk.CTkFrame(app_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(theme_row, text="Dark Mode", font=BODY,
                     text_color=tm.c("TEXT_PRIMARY")).pack(side="left")

        self._theme_switch = ctk.CTkSwitch(
            theme_row, text="", onvalue=1, offvalue=0,
            fg_color=tm.c("BG_ELEVATED"),
            progress_color=tm.c("ACCENT"),
            button_color=tm.c("TEXT_PRIMARY"),
            command=self._toggle_theme,
        )
        self._theme_switch.select()
        self._theme_switch.pack(side="right")

        self._field_label(app_inner, "Accent Color")
        accent_row = ctk.CTkFrame(app_inner, fg_color="transparent")
        accent_row.pack(fill="x", pady=(0, PAD_SM))

        for name, preset in ACCENT_PRESETS.items():
            swatch = ctk.CTkButton(
                accent_row, text="", width=36, height=36,
                fg_color=preset["ACCENT"],
                hover_color=preset["ACCENT_HOVER"],
                corner_radius=18,
                command=lambda n=name: self._set_accent(n),
            )
            swatch.pack(side="left", padx=4)

        self._section_header(container, "Data Management")

        data_frame = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                   corner_radius=RADIUS)
        data_frame.pack(fill="x", pady=(0, PAD_LG))

        data_inner = ctk.CTkFrame(data_frame, fg_color="transparent")
        data_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        btn_row = ctk.CTkFrame(data_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        export_btn = ctk.CTkButton(
            btn_row, text="📥 Export All Data (JSON)", height=36,
            fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
            border_width=1, border_color=tm.c("BORDER"), corner_radius=8,
            command=self._export_data,
        )
        export_btn.pack(side="left", padx=(0, PAD_SM), expand=True, fill="x")

        reset_btn = ctk.CTkButton(
            btn_row, text="🗑 Reset Tournament", height=36,
            fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("RED"),
            text_color=tm.c("RED"), font=BODY,
            border_width=1, border_color=tm.c("RED"), corner_radius=8,
            command=self._confirm_reset,
        )
        reset_btn.pack(side="left", padx=(PAD_SM, 0), expand=True, fill="x")

        self._section_header(container, "About")

        about_frame = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                    corner_radius=RADIUS)
        about_frame.pack(fill="x", pady=(0, PAD_LG))

        about_inner = ctk.CTkFrame(about_frame, fg_color="transparent")
        about_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        about_text = (
            "EsportsHub — Tournament Manager v1.0.0\n\n"
            "Design Patterns:\n"
            "  • Factory — Tournament type configuration\n"
            "  • Observer — Match event pub/sub system\n"
            "  • Strategy — Interchangeable ranking algorithms\n"
            "  • Composite — Bracket tree structure\n"
            "  • State — Match lifecycle state machine\n\n"
            "Built with Python, CustomTkinter, and Matplotlib"
        )
        about_label = ctk.CTkLabel(
            about_inner, text=about_text, font=SMALL,
            text_color=tm.c("TEXT_SECONDARY"), anchor="w",
            justify="left",
        )
        about_label.pack(fill="x")

    def _section_header(self, parent, text: str):
        label = ctk.CTkLabel(
            parent, text=text, font=H3,
            text_color=tm.c("TEXT_SECONDARY") if (tm := ThemeManager()) else "#888",
        )
        label.pack(fill="x", pady=(0, PAD_SM), anchor="w")

    def _field_label(self, parent, text: str):
        tm = ThemeManager()
        label = ctk.CTkLabel(
            parent, text=text, font=SMALL,
            text_color=tm.c("TEXT_SECONDARY"),
        )
        label.pack(anchor="w", pady=(0, 4))

    def _on_slider_change(self, value):
        v = int(value)
        if v % 2 != 0:
            v += 1
        self._max_teams_label.configure(text=str(v))

    def _start_tournament(self):
        if not self._service:
            return
        toast = ToastManager()

        name = self._name_entry.get().strip() or "EsportsHub Tournament"
        t_type = self._type_menu.get()
        game = self._game_entry.get().strip() or "CS2"
        max_teams = int(self._max_teams_var.get())

        try:
            self._service.configure_tournament(t_type, name=name,
                                                game=game, max_teams=max_teams)
            self._service.start_tournament()

            if self._app and hasattr(self._app, "bracket_service"):
                teams = self._service.get_all_teams()
                team_ids = [t.id for t in teams]
                team_names = {t.id: t.name for t in teams}

                def match_factory(t1_id, t2_id, round_num, position):
                    return self._service.create_match(
                        t1_id or "", t2_id or "", game, round_num, position
                    )

                self._app.bracket_service.set_match_factory(match_factory)
                self._app.bracket_service.generate_bracket(team_ids, team_names)

            toast.show(f"Tournament '{name}' started and matches generated!", "success")
        except Exception as e:
            toast.show(f"Error: {e}", "error")

    def _toggle_theme(self):
        tm = ThemeManager()
        tm.toggle_mode()
        mode = tm.mode
        ctk.set_appearance_mode(mode)
        if self._app and hasattr(self._app, 'apply_theme'):
            self._app.apply_theme()

    def _set_accent(self, name: str):
        tm = ThemeManager()
        tm.set_accent(name)
        toast = ToastManager()
        toast.show(f"Accent color: {name}", "info")
        if self._app and hasattr(self._app, 'apply_theme'):
            self._app.apply_theme()

    def _export_data(self):
        if not self._service:
            return
        toast = ToastManager()
        try:
            self._service.export_json("tournament_data.json")
            toast.show("Data exported to tournament_data.json", "success")
        except Exception as e:
            toast.show(f"Export failed: {e}", "error")

    def _confirm_reset(self):
        ResetConfirmModal(self.winfo_toplevel(), service=self._service,
                         app=self._app)

    def refresh(self):
        if not self._service:
            return

        self._name_entry.configure(state="normal")
        self._game_entry.configure(state="normal")
        self._type_menu.configure(state="normal")
        self._max_teams_slider.configure(state="normal")

        self._name_entry.delete(0, "end")
        self._name_entry.insert(0, self._service.tournament_name)

        self._game_entry.delete(0, "end")
        self._game_entry.insert(0, self._service.game)

        self._type_menu.set(self._service.type_name)

        max_t = self._service.max_teams
        self._max_teams_var.set(max_t)
        self._max_teams_label.configure(text=str(max_t))

        started = self._service.tournament_started
        if started:
            self._name_entry.configure(state="disabled")
            self._game_entry.configure(state="disabled")
            self._type_menu.configure(state="disabled")
            self._max_teams_slider.configure(state="disabled")
            self._start_btn.configure(state="disabled", text="Tournament Started")
        else:
            self._start_btn.configure(state="normal", text="🚀 Start Tournament")


class ResetConfirmModal(Modal):

    def __init__(self, parent, service=None, app=None):
        super().__init__(parent, title="Reset Tournament", width=400, height=200)
        self._service = service
        self._app = app

        tm = ThemeManager()

        self.set_action_text("Reset")
        self.set_action_command(self._do_reset)

        warning = ctk.CTkLabel(
            self.body,
            text="⚠ Are you sure you want to reset?\n\nThis will delete all teams, matches, and bracket data.\nThis action cannot be undone.",
            font=BODY, text_color=tm.c("AMBER"),
            justify="center",
        )
        warning.pack(fill="both", expand=True, pady=PAD_LG)

    def _do_reset(self):
        if self._service:
            self._service.reset()
        if self._app:
            self._app.save_state()
        toast = ToastManager()
        toast.show("Tournament reset", "warning")
        if self._app and hasattr(self._app, 'refresh_current_view'):
            self._app.refresh_current_view()
        self.close()
