import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from gui.theme import ThemeManager, BODY, SMALL, H3, PAD_SM, PAD_MD


class DataTable(ctk.CTkFrame):

    def __init__(self, parent, columns: list, column_widths: dict = None,
                 on_select=None, on_double_click=None, **kwargs):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_SURFACE"),
                         corner_radius=8, **kwargs)

        self._tm = tm
        self._columns = columns
        self._on_select = on_select
        self._on_double_click = on_double_click
        self._sort_column = None
        self._sort_reverse = False
        self._data_rows = []

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Custom.Treeview",
                         background=tm.c("BG_SURFACE"),
                         foreground=tm.c("TEXT_PRIMARY"),
                         fieldbackground=tm.c("BG_SURFACE"),
                         borderwidth=0,
                         font=BODY,
                         rowheight=36)

        style.configure("Custom.Treeview.Heading",
                         background=tm.c("BG_ELEVATED"),
                         foreground=tm.c("TEXT_SECONDARY"),
                         borderwidth=0,
                         font=H3,
                         relief="flat")

        style.map("Custom.Treeview",
                   background=[("selected", tm.c("BG_SELECTED"))],
                   foreground=[("selected", tm.c("TEXT_PRIMARY"))])

        style.map("Custom.Treeview.Heading",
                   background=[("active", tm.c("BG_HOVER"))])

        self.tree = ttk.Treeview(
            self, columns=columns, show="headings",
            style="Custom.Treeview", selectmode="browse",
        )

        col_widths = column_widths or {}
        for col in columns:
            width = col_widths.get(col, 120)
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=width, minwidth=60)

        self.tree.tag_configure("even", background=tm.c("BG_SURFACE"))
        self.tree.tag_configure("odd", background=tm.c("BG_ELEVATED"))
        self.tree.tag_configure("hover", background=tm.c("BG_HOVER"))

        scrollbar = ctk.CTkScrollbar(self, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", self._on_leave)
        self.tree.bind("<MouseWheel>", self._on_mousewheel)
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1, "units"))

        self._last_hover_item = None

    def set_data(self, rows: list):
        self.clear()
        self._data_rows = rows
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))

    def append_row(self, row: tuple):
        i = len(self._data_rows)
        tag = "even" if i % 2 == 0 else "odd"
        self._data_rows.append(row)
        self.tree.insert("", "end", values=row, tags=(tag,))

    def clear(self):
        self._data_rows.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_selected(self):
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0])["values"]
        return None

    def _sort_by(self, column):
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False

        col_idx = self._columns.index(column)

        for c in self._columns:
            arrow = ""
            if c == column:
                arrow = " ↓" if self._sort_reverse else " ↑"
            self.tree.heading(c, text=c + arrow)

        items = [(self.tree.item(iid)["values"], iid)
                 for iid in self.tree.get_children()]

        def sort_key(item):
            val = item[0][col_idx]
            try:
                return float(val)
            except (ValueError, TypeError):
                return str(val).lower()

        items.sort(key=sort_key, reverse=self._sort_reverse)

        for i, (values, iid) in enumerate(items):
            self.tree.move(iid, "", i)
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.item(iid, tags=(tag,))

    def _on_tree_select(self, event):
        if self._on_select:
            sel = self.get_selected()
            if sel:
                self._on_select(sel)

    def _on_tree_double_click(self, event):
        if self._on_double_click:
            sel = self.get_selected()
            if sel:
                self._on_double_click(sel)

    def _on_motion(self, event):
        item = self.tree.identify_row(event.y)
        if item and item != self._last_hover_item:
            if self._last_hover_item:
                idx = self.tree.index(self._last_hover_item)
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.item(self._last_hover_item, tags=(tag,))
            self.tree.item(item, tags=("hover",))
            self._last_hover_item = item

    def _on_leave(self, event):
        if self._last_hover_item:
            try:
                idx = self.tree.index(self._last_hover_item)
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.item(self._last_hover_item, tags=(tag,))
            except Exception:
                pass
            self._last_hover_item = None

    def _on_mousewheel(self, event):
        if event.delta:
            amt = int(-1 * (event.delta / 120))
            if amt == 0:
                amt = -1 if event.delta > 0 else 1
            self.tree.yview_scroll(amt, "units")
