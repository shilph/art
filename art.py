import tkinter as tk
from tkinter import simpledialog, messagebox
import tkinter.ttk as ttk
from importlib import import_module
from random import randint
from subprocess import Popen
from playwright.sync_api import sync_playwright
import webbrowser
import platform
from datetime import date

from art_db import ARTDatabase
from popups.add_award import AddAward
from popups.note_of_day import NoteOfDay
from popups.settings import Settings

class ART(object):
    """Main class for ART, Automated Rewards Tracker"""
    award_info_gui_components = []

    def __init__(self):
        """Initial function. Unlock MySQL and launch Chrome CDP mode; then launch ART app."""
        retry = 0
        while True:
            try:
                password = self.get_mysql_password(retry)
                self.art_db = ARTDatabase(password=password)
                self.chrome_debug_port = randint(10000, 30000)
                # set size of Chrome to a limited/fixed size
                if platform.system() == "Windows":
                    chrome_path = self.art_db.get_configs("chrome_executable")["chrome_executable"]["conf_value"]
                    self.chrome_process = Popen([
                        chrome_path,
                        f"--remote-debugging-port={self.chrome_debug_port}",
                        "--window-size=1240,800"
                    ])
                elif platform.system() == "Linux":
                    # I did not test for Linux yet.
                    self.chrome_process = Popen([
                        "google-chrome",
                        f"--remote-debugging-port={self.chrome_debug_port}",
                        "--window-size=1240,800"
                    ])
                elif platform.system() == "Darwin":
                    # Since I do not have a MAC system, I did not test this line.
                    self.chrome_process = Popen([
                        "open",
                        "-a",
                        "Google Chrome.app",
                        "--args",
                        f"--remote-debugging-port={self.chrome_debug_port}",
                        "--window-size=1240,800"
                    ])
                self.playwright = sync_playwright().start()
                self.chrome_debug_browser = self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.chrome_debug_port}"
                )
                print(f"DEBUG MODE >> Chrome Debug Port #{self.chrome_debug_port}")
                self.show_main_app()
                break
            except RuntimeError:
                retry += 1
                if retry == 3:
                    messagebox.showerror(
                        title="Exceed Retries",
                        message="Failed to match the password 3 times.\nTerminate the application."
                    )
                    break

    def get_mysql_password(self, retry: int = 0) -> str:
        """Get MySQL password from user.

        :param retry: number of retries
        :return: user entered MySQL password
        """
        title = "Enter Password" if retry == 0 else "Re-enter Password"
        if retry == 0:
            label = "Please enter MySQL Database Password:"
        else:
            label = f"Please enter MySQL Database Password (Retry {retry}):"
        return simpledialog.askstring(title=title, prompt=label, show="*")

    def show_main_app(self) -> None:
        """Creating GUI: main window."""
        self.win = tk.Tk()
        self.win.title("ART: Automated Rewards Tracker")

        self.main_frame = ttk.Frame(self.win)
        self.gui_add_menu()
        self.gui_add_main()
        self.main_frame.pack(fill="both", expand=False)

        self.init_data()

        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)
        # show note of the day but only once a day
        today = date.today().strftime("%Y-%m-%d")
        if self.art_db.get_configs("last_day_note_opened")["last_day_note_opened"]["conf_value"] != today:
            self.win.after(1000, self.show_note_of_day)

        self.win.mainloop()

    def gui_add_menu(self) -> None:
        """Creating GUI: menu."""
        menubar = tk.Menu(self.main_frame)
        self.win.config(menu=menubar)

        # menu: File
        menu_file = tk.Menu(menubar, tearoff=False)
        menu_file.add_command(label="Export to Excel (NYI)",
                              command=self.on_export_to_excel)
        menu_file.add_separator()
        menu_file.add_command(label="Settings",
                              command=self.on_open_settings_window)
        menubar.add_cascade(label="File", menu=menu_file)

        # menu: Account
        menu_account = tk.Menu(menubar, tearoff=False)
        menu_account.add_command(label="Add a User",
                                 command=self.on_add_user)
        menu_account.add_command(label="Remove a User (NYI)",
                                 command=self.on_remove_user)
        menu_account.add_separator()
        menu_account.add_command(label="Add an Award",
                                 command=self.on_add_award)
        menu_account.add_command(label="Remove an Award (NYI)",
                                 command=self.on_remove_award)
        menu_account.add_separator()
        menu_account.add_command(label="Refresh Awards (NYI)",
                                 command=self.refresh_award_list)
        menubar.add_cascade(label="Account", menu=menu_account)

        # menu: Help
        menu_help = tk.Menu(menubar, tearoff=False)
        menu_help.add_command(label="Note of the Day", command=self.on_show_note_of_day)
        menu_help.add_separator()
        menu_help.add_command(label="About ART", command=self.on_show_about)
        menubar.add_cascade(label="Help", menu=menu_help)

    def gui_add_main(self) -> None:
        """Creating GUI: Main function (award overview and detail)."""
        # user selection frame
        frame_owner = ttk.Frame(self.main_frame)
        frame_owner.grid(column=0, row=0, sticky="nsew")

        label_owner = ttk.Label(frame_owner, text="Owner:", width=10)
        label_owner.grid(column=0, row=0, padx=10, pady=2)
        current_owner = tk.StringVar()
        self.combo_owner = ttk.Combobox(frame_owner, textvariable=current_owner, width=30, state='readonly')
        self.combo_owner.bind('<<ComboboxSelected>>', self.on_owner_changed)
        self.combo_owner.grid(column=1, row=0, padx=0, pady=2)

        self.gui_add_award_list()
        self.gui_add_award_info()

    def gui_add_award_list(self) -> None:
        """Creating GUI: Award overview"""
        # main tree view frame
        paned_award_list = ttk.PanedWindow(self.main_frame)
        paned_award_list.grid(column=0, row=1, sticky="nsew")

        frame_award_list = ttk.Frame(paned_award_list)
        paned_award_list.add(frame_award_list)

        scrollbar_award_list = ttk.Scrollbar(frame_award_list)
        scrollbar_award_list.configure(orient="vertical")
        scrollbar_award_list.pack(fill="y", side="right")

        # Add a Treeview widget
        self.treeview_award_list = ttk.Treeview(
            frame_award_list,
            yscrollcommand=scrollbar_award_list.set,
            columns=('award', 'id', 'balance', 'expected_expire','last_update'),
            show='headings'
        )
        self.treeview_award_list.pack(expand=True, fill="y")
        scrollbar_award_list.config(command=self.treeview_award_list.yview)
        self.treeview_award_list.column("award", anchor="w", width=180)
        self.treeview_award_list.heading("award", text="Award Program")
        self.treeview_award_list.column("id", anchor="w", width=90)
        self.treeview_award_list.heading("id", text="Username/ID")
        self.treeview_award_list.column("balance", anchor="w", width=80)
        self.treeview_award_list.heading("balance", text="Balance")
        self.treeview_award_list.column("expected_expire", anchor="w", width=100)
        self.treeview_award_list.heading("expected_expire", text="Expected Expire")
        self.treeview_award_list.column("last_update", anchor="w", width=100)
        self.treeview_award_list.heading("last_update", text="Last Updated")
        self.treeview_award_list.bind("<<TreeviewSelect>>", self.on_show_award_details)

    def gui_add_award_info(self) -> None:
        """Creating GUI: Award detail."""
        frame_award_info = ttk.Frame(self.main_frame)
        frame_award_info.grid(column=1, row=1, sticky="nsew")

        self.frame_award_info_general = ttk.Frame(frame_award_info)
        self.frame_award_info_general.grid(row=0, sticky="nsew")

        label_award_program = ttk.Label(self.frame_award_info_general,
                                        text="Award Program")
        label_award_program.grid(column=0, row=0, padx=10, pady=2, sticky="w")
        self.entry_award_program = ttk.Entry(self.frame_award_info_general)
        self.entry_award_program.grid(column=1, row=0, padx=10, pady=2)

        # balance history
        frame_award_info_list = ttk.Frame(frame_award_info)
        frame_award_info_list.grid(row=1, sticky="nsew")

        label_balance_history = ttk.Label(frame_award_info_list,
                                          text="Balance History",
                                          width=15)
        label_balance_history.grid(padx=10, pady=2, sticky="w")

        paned_balance_history = ttk.PanedWindow(frame_award_info_list)
        paned_balance_history.grid(column=0, row=1, sticky="nsew", pady=2)

        frame_balance_history = ttk.Frame(paned_balance_history)
        paned_balance_history.add(frame_balance_history)

        scrollbar_balance_history = ttk.Scrollbar(frame_balance_history)
        scrollbar_balance_history.configure(orient="vertical")
        scrollbar_balance_history.pack(fill="y", side="right")

        # Add a Treeview widget
        self.treeview_balance_history = ttk.Treeview(
            frame_balance_history,
            yscrollcommand=scrollbar_balance_history.set,
            columns=('date', 'balance'),
            show='headings'
        )
        self.treeview_balance_history.pack(expand=True, fill="y")
        scrollbar_balance_history.config(command=self.treeview_balance_history.yview)
        self.treeview_balance_history.column("date", anchor="w", width=130)
        self.treeview_balance_history.heading("date", text="Date", anchor="w")
        self.treeview_balance_history.column("balance", anchor="w", width=130)
        self.treeview_balance_history.heading("balance", text="Balance", anchor="w")

        # button
        frame_award_info_update = ttk.Frame(frame_award_info)
        frame_award_info_update.grid(row=2, sticky="e", pady=2)

        button_update = ttk.Button(frame_award_info_update,
                                   text="Update Award Balance",
                                   command=self.on_update_award_program,
                                   width=20)
        button_update.grid(padx=3, sticky="e")

    def init_data(self) -> None:
        """Initialize data. Get user list and award information."""
        # Get users
        users = self.art_db.get_users()
        if len(users) > 0:
            self.combo_owner["values"] = self.art_db.get_users()
            self.combo_owner.current(0)
            self.refresh_award_list()

    def get_current_award_data_from_web(self, user: str, award: str, username: str) -> dict:
        """Retrieve current point balance by user and award.

        :param user: name of the current user
        :param award: award program name
        :param username: username or ID
        :return: dict output from awards.XYZ.get_balance()
        """
        # get award information
        award_info = self.art_db.get_award_info(award=award)
        account_info = self.art_db.get_account_info(award=award,
                                                    user=user,
                                                    username=username)
        script = import_module(f"awards.{award_info['script']}")
        return script.get_balance(browser=self.chrome_debug_browser,
                                  account_info=account_info,
                                  award_info=award_info)

    def refresh_award_list(self) -> None:
        """Refresh award overview"""
        award_list = self.art_db.get_all_latest_balances(user=self.combo_owner.get())

        # clear data
        for item in self.treeview_award_list.get_children():
            self.treeview_award_list.delete(item)

        # add data
        for category in award_list:
            self.treeview_award_list.insert(
                '', 'end', values=[f"[ {category} ]", "", "", "", ""])
            for award_info in award_list[category]:
                self.treeview_award_list.insert('', 'end', values=award_info)

    def on_closing(self) -> None:
        """Event: close ART application."""
        self.art_db.close()
        self.playwright.stop()
        # close Chrome browser
        self.chrome_process.terminate()
        self.chrome_process.wait()
        self.win.destroy()

    def on_export_to_excel(self) -> None:
        """Event: export data to Excel"""
        pass

    def on_add_user(self) -> None:
        """Event: add a user."""
        name = simpledialog.askstring(title="Add User", prompt="Please enter name of a user: ")
        owners = list(self.combo_owner["values"])
        owners.append(name)
        self.combo_owner["values"] = owners
        if len(owners) == 1:
            # select a newly added owner for the first time use only.
            self.combo_owner.set(name)

    def on_remove_user(self) -> None:
        """Event: remove a user."""
        pass

    def on_add_award(self):
        """Event: add an award program to the current user."""
        owner = self.combo_owner.get()
        if owner is None or owner == '':
            messagebox.showerror(title="No User Error", message="Please add a user before adding an award program.")
            return
        popup = AddAward(parent=self.win, art_db=self.art_db, owner=owner)
        account_info = popup.show()
        if account_info is not None:
            # add account only if no account exists
            award = account_info["award"]
            # in most cases, first field is "username" but there is exception.
            # To bypass the issue, "first_field" will be marked as "username"
            username = account_info[account_info["first_field"]]
            if self.art_db.add_account(user=owner,
                                       award=award,
                                       username=username,
                                       account_info=account_info):
                crawled_award_data = self.get_current_award_data_from_web(
                    user=owner, username=username, award=award
                )
                self.art_db.add_balance(user=owner,
                                        award=award,
                                        username=username,
                                        balance=crawled_award_data["balance"],
                                        expire_date=crawled_award_data["expire_date"])
                self.refresh_award_list()
            else:
                messagebox.showerror(title="Account Exists",
                                     message=f"{award} account for {owner} already exists.")

    def on_remove_award(self) -> None:
        """Event: remove an award from a user."""
        pass

    def on_open_settings_window(self) -> None:
        """Event: open setting window."""
        Settings(parent=self.win, art_db=self.art_db)

    def show_note_of_day(self) -> None:
        """Show note of the day popup"""
        NoteOfDay(parent=self.win, art_db=self.art_db)
        self.art_db.set_config("last_day_note_opened", date.today().strftime("%Y-%m-%d"))

    def on_show_note_of_day(self) -> None:
        """Event: open howto guide."""
        self.show_note_of_day()
        # record today's date

    def on_show_about(self) -> None:
        """Event: open about window."""
        webbrowser.open("https://github.com/shilph/art")

    def on_owner_changed(self, event) -> None:
        """Event: selected owner is changed."""
        pass

    def on_update_award_program(self) -> None:
        """Event: update an award program."""
        owner = self.combo_owner.get()
        award = self.entry_award_program.get()
        username = self.selected_award_details[
            self.selected_award_details["required_field_names"][0]]
        crawled_award_data = self.get_current_award_data_from_web(
            user=owner, award=award, username=username
        )
        self.art_db.add_balance(user=owner,
                                award=award,
                                username=username,
                                balance=crawled_award_data["balance"],
                                expire_date=crawled_award_data["expire_date"])
        self.refresh_award_list()
        self.update_balance_history(user=owner, award=award, username=username)

    def update_balance_history(self, user: str, award: str, username: str) -> None:
        """Update balance history to award detail page.

        :param user: name of user
        :param award: award program
        :param username: username or ID
        """
        balance_history = self.art_db.get_balance_history(user=user,
                                                          award=award,
                                                          username=username)
        for item in self.treeview_balance_history.get_children():
            self.treeview_balance_history.delete(item)
        for balance in balance_history:
            self.treeview_balance_history.insert('', 'end', values=balance)

    def update_readonly_entry(self, entry: tk.Entry, text: str) -> None:
        """Update a READONLY entry.

        :param entry: entry to update
        :param text: message to add to the entry
        """
        entry['state'] = 'normal'
        entry.delete(0, tk.END)
        entry.insert(tk.END, text)
        entry['state'] = 'readonly'

    def on_show_award_details(self, event):
        selected_award = next(
            (self.treeview_award_list.item(item)['values'] for item in self.treeview_award_list.selection()), None
        )
        if selected_award is None:
            return

        award = selected_award[0]
        self.selected_award_details = None

        if not award.startswith("["):
            # remove previous GUI components
            for comp in self.award_info_gui_components:
                comp.destroy()
            self.entry_award_program.delete(0, tk.END)

            owner = self.combo_owner.get()
            award_info = self.art_db.get_award_info(award=award)
            account_info = self.art_db.get_account_info(
                award=award, user=owner, username=selected_award[1]
            )

            self.selected_award_details = {**award_info, **account_info}

            # add GUI components
            self.update_readonly_entry(entry=self.entry_award_program,
                                       text=award)
            row = 1
            for field_name, field_display in zip(
                    award_info["required_field_names"],
                    award_info["required_field_displays"]):
                label = tk.Label(self.frame_award_info_general,
                                 text=f"{field_display}")
                label.grid(column=0, row=row, padx=10, pady=2, sticky="w")
                self.award_info_gui_components.append(label)
                entry = tk.Entry(self.frame_award_info_general,
                                 width=30,
                                 show="*" if field_name == "password" else "")
                entry.grid(column=1, row=row, padx=10, pady=2, sticky='e')
                if row == 1:
                    # username or ID: it should not be modified
                    self.update_readonly_entry(entry=entry,
                                               text=account_info[field_name])
                else:
                    entry.insert(tk.END, account_info[field_name])
                self.award_info_gui_components.append(entry)
                row += 1

            self.update_balance_history(user=owner,
                                        award=award,
                                        username=selected_award[1])


if __name__ == "__main__":
    main = ART()
