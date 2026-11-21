import tkinter as tk
import tkinter.font as tkFont


class _ScenarioUI(tk.Frame):
    """Drop-down menus for the scenario settings a CA description offers

    The description lists its menus in ca_config.choice_menus as
    (setting, label, [(choice shown, value)]) and the current value of each
    setting in ca_config.choices.
    """

    def __init__(self, parent, ca_config):
        tk.Frame.__init__(self, parent, padx=10)
        title_font = tkFont.Font(self, family="Helvetica", size=16,
                                 weight=tkFont.BOLD)
        tk.Label(self, text="Scenario", font=title_font).pack(pady=(0, 10))

        self.menus = []
        for setting, label, options in ca_config.choice_menus:
            values = dict(options)
            current = ca_config.choices[setting]
            shown = next((name for name, value in options if value == current),
                         options[0][0])
            chosen = tk.StringVar(self, value=shown)
            tk.Label(self, text=label).pack(anchor=tk.W)
            menu = tk.OptionMenu(self, chosen, *values)
            menu.config(width=26)
            menu.pack(anchor=tk.W, pady=(0, 10))
            self.menus.append((setting, chosen, values))

    def get_choices(self):
        """The value chosen in each menu, keyed by setting name"""
        return {setting: values[chosen.get()]
                for setting, chosen, values in self.menus}
