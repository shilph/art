import tkinter as tk
import tkinter.ttk as ttk
import re

from art_db import ARTDatabase


class Settings(tk.Toplevel):
    """Popup window to display Note of the Day."""
    return_info = False

    def __init__(self, parent, art_db: ARTDatabase):
        """Init function. Open a popup window

        :param parent: main ART GUI window
        :param art_db: ART database
        """
        self.art_db = art_db
        super(Settings, self).__init__(parent)
        self.title("Settings")

        paned_setting_list = ttk.PanedWindow(self)
        paned_setting_list.grid(column=0, row=0, sticky="nsew")

        frame_setting_list = ttk.Frame(paned_setting_list)
        paned_setting_list.add(frame_setting_list)

        scrollbar_setting_list = ttk.Scrollbar(frame_setting_list)
        scrollbar_setting_list.configure(orient="vertical")
        scrollbar_setting_list.pack(fill="y", side="right")

        # Add a Treeview widget
        self.treeview_setting_list = ttk.Treeview(
            frame_setting_list,
            yscrollcommand=scrollbar_setting_list.set,
            columns=('conf_key', 'conf_label', 'conf_value'),
            show='headings'
        )
        self.treeview_setting_list.pack(expand=True, fill="y")
        scrollbar_setting_list.config(command=self.treeview_setting_list.yview)
        self.treeview_setting_list.column("conf_key", anchor="w", width=0, stretch=False)
        self.treeview_setting_list.heading("conf_key", text="")
        self.treeview_setting_list.column("conf_label", anchor="w", width=200)
        self.treeview_setting_list.heading("conf_label", text="Variable")
        self.treeview_setting_list.column("conf_value", anchor="w", width=400)
        self.treeview_setting_list.heading("conf_value", text="Value")

        configs = self.art_db.get_configs()
        for conf_key in configs:
            config = configs[conf_key]
            if config["conf_label"] != "":
                self.treeview_setting_list.insert(
                    parent="",
                    index="end",
                    values=[conf_key, config["conf_label"], config["conf_value"]]
                )

        # Create an entry widget for editing
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.entry_var)
        self.entry.bind("<Return>", self.update_cell)  # Bind the Return key to update the cell

        # edit by double click
        self.treeview_setting_list.bind("<Double-1>", self.edit_value)

        button_frame = ttk.Frame(self)
        button_frame.grid(column=0, row=1, padx=10, pady=2)
        # Create the Update button
        update_button = tk.Button(button_frame,
                              text="Update Settings",
                              command=self.on_update_settings)
        update_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')

        # Create the Cancel button
        cancel_button = tk.Button(button_frame,
                                  text="Cancel",
                                  command=self.destroy)
        cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')


    def edit_value(self, event):
        item = self.treeview_setting_list.identify('item', event.x, event.y)
        column = self.treeview_setting_list.identify_column(event.x)

        # If the selected column is conf_value (column index "#3")
        if column == '#3':
            # Get the bounding box of the cell
            bbox = self.treeview_setting_list.bbox(item, column)

            # Set the value of the entry widget to the current value of the cell
            self.entry_var.set(self.treeview_setting_list.item(item, 'values')[2])

            # Place the entry widget over the cell for editing
            self.entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
            self.entry.focus_set()

    def update_cell(self, event):
        # Get the selected item
        item = self.treeview_setting_list.selection()[0]

        # Get the new value from the entry widget
        new_value = self.entry_var.get()

        # Update the value in the second column
        self.treeview_setting_list.item(
            item,
            values=(
                self.treeview_setting_list.item(item, 'values')[0],
                self.treeview_setting_list.item(item, 'values')[1],
                new_value
            )
        )

        # Hide the entry widget after editing
        self.entry.place_forget()

    def on_update_settings(self) -> None:
        """Event when update settings button clicked."""
        for index in self.treeview_setting_list.get_children():
            line = self.treeview_setting_list.set(index)
            self.art_db.set_config(conf_key=line['conf_key'], conf_value=line['conf_value'].replace("\\", "\\\\"))

        self.destroy()