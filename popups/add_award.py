import tkinter as tk
import tkinter.ttk as ttk
from tkinter import StringVar
from art_db import ARTDatabase


class AddAward(tk.Toplevel):
    """Popup window to add an award."""
    return_info = False

    def __init__(self, parent, art_db: ARTDatabase, owner: str):
        """Init function. Open a popup window

        :param parent: main ART GUI window
        :param art_db: ART database
        :param owner: name of user to add this award program.
        """
        self.return_info = False
        self.apt_db = art_db
        self.required_fields = {}
        self.required_fields_guis = []

        super(AddAward, self).__init__(parent)
        self.title("Add an Award Program")

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(column=0, row=0, sticky="nsew")

        # Create the 'Owner' label and combobox
        label_owner = tk.Label(self.main_frame, text="Owner: ")
        label_owner.grid(row=0, column=0, padx=3, pady=2, sticky='w')
        entry_owner = ttk.Entry(self.main_frame, width=30)
        entry_owner.insert(0, owner)
        entry_owner.grid(row=0, column=1, padx=3, pady=2, sticky='e')
        entry_owner['state'] = 'disabled'

        # Create the 'Award Program' label and combobox
        label_award = tk.Label(self.main_frame, text="Award Program: ")
        label_award.grid(row=1, column=0, padx=3, pady=2, sticky='w')
        award_names = art_db.get_award_program_names()
        self.award = StringVar(self)
        combo_award = ttk.Combobox(self.main_frame,
                                   values=award_names,
                                   width=30,
                                   textvariable=self.award,
                                   state='readonly')
        combo_award.grid(row=1, column=1, padx=3, pady=2, sticky='e')
        combo_award.bind("<<ComboboxSelected>>", self.on_award_selected)

        # add required fields
        max_fields_count = 0
        for award_name in award_names:
            award_name = award_name.split(":")[1].strip()
            award_info = self.apt_db.get_award_info(award=award_name)
            self.required_fields[award_name] = {
                "required_field_names": award_info["required_field_names"],
                "required_field_displays": award_info["required_field_displays"]
            }
            max_fields_count = max(max_fields_count,
                                   len(award_info["required_field_names"]))
        row = 2
        for index in range(0, max_fields_count):
            label = tk.Label(self.main_frame)
            label.grid(row=row, column=0, padx=3, pady=2, sticky='w')
            str_var = StringVar(self)
            entry = tk.Entry(self.main_frame, width=30, textvariable=str_var)
            entry.grid(row=row, column=1, padx=3, pady=2, sticky='e')
            self.required_fields_guis.append([label, entry, str_var])
            label.grid_remove()
            entry.grid_remove()
            row += 1

        button_frame = ttk.Frame(self)
        button_frame.grid(column=0, row=1, padx=10, pady=2)
        # Create the OK button
        ok_button = tk.Button(button_frame,
                              text="OK",
                              command=self.on_add_award)
        ok_button.grid(row=4, column=0, padx=10, pady=10, sticky='e')

        # Create the Cancel button
        cancel_button = tk.Button(button_frame,
                                  text="Cancel",
                                  command=self.on_not_add_award)
        cancel_button.grid(row=4, column=1, padx=10, pady=10, sticky='w')

        # event when popup windows is closed except OK button clicked
        self.protocol("WM_DELETE_WINDOW", self.on_not_add_award)

    def on_award_selected(self, event) -> None:
        """Event when award program selection is changed

        :param event: event (not in use)
        """
        award_info = self.required_fields[self.award.get().split(":")[1].strip()]

        for index in range(0, len(self.required_fields_guis)):
            self.required_fields_guis[index][0].grid_remove()
            self.required_fields_guis[index][1].grid_remove()

        # show GUI components
        for index in range(0, len(award_info["required_field_names"])):
            label = self.required_fields_guis[index][0]
            label.config(text=award_info["required_field_displays"][index])
            label.grid()
            entry = self.required_fields_guis[index][1]
            entry.config(
                show="*" if award_info["required_field_names"][index] ==
                "password" else "")
            entry.grid()

    def on_not_add_award(self):
        """Event when the popup windows is closed."""
        self.destroy()

    def on_add_award(self):
        """Event when OK button is clicked."""
        self.return_info = True
        self.destroy()

    def show(self) -> dict | None:
        """Show this "add award program" window then return award program name, user ID & password

        :return: {award, first_field, required_field_names(key)+required_values(value)}
        """
        self.wm_deiconify()
        self.wait_window()
        if self.return_info:
            award = self.award.get().split(":")[1].strip()
            ret_val = {
                "award":
                    award,
                "first_field":
                    self.required_fields[award]["required_field_names"][0]
            }
            for required_field, gui in zip(
                    self.required_fields[award]["required_field_names"],
                    self.required_fields_guis):
                ret_val[required_field] = gui[2].get()
            return ret_val
        else:
            return None
