import matplotlib
import matplotlib.pyplot as plt
import math
import MySQLdb
import os.path
import pandas as pd
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pandas.errors import ParserError
from pandastable import Table, TableModel

class Vault(object):
    host = "localhost"
    user= "root"
    passwd = "380@MySQL"
    data = pd.DataFrame()

class System (tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        Vault.data = get_db_data()

        self.fonts = {
            "title": tkfont.Font(Device="Program")
        }
        self.tabs = [
            DataFrame,
            StatsFrame
        ]
        self.create_widgets()
        self.set_tab(0)

    def create_widgets(self):
        self.rowconfigure(index=2, weight=1)
        self.columnconfigure(index=0, weight=1)

        self.title_label = tk.Label(
            self, text="Mobile.", font=self.fonts["title"], justify="left", bg="#f0f0f0")
        self.title_label.grid(row=0, column=0, ipady=8,
                              ipadx=12, sticky="")

        if len(self.tabs) > 1:
            self.subheader_frame = tk.Frame(self, bg="#f0f0f0")
            self.subheader_frame.grid(
                row=1, column=0, ipady="8", sticky="")

            for col in range(10):
                self.subheader_frame.columnconfigure(index=col, weight=1)

        self.tab_container = tk.Frame(self, bg="#fff")
        self.tab_container.grid(row=2, column=0, sticky="")
        self.tab_container.rowconfigure(index=0, weight=1)
        self.tab_container.columnconfigure(index=0, weight=1)

        self.tab_buttons = []
        for idx, tab in enumerate(self.tabs):
            if len(self.tabs) > 1:
         
                t = tk.Button(self.subheader_frame, text=tab.label, relief="ridge",
                              command=lambda index=idx: self.set_tab(index))

                self.tab_buttons.append(t)
                self.tab_buttons[idx].grid(ipadx=10, ipady=5, sticky="",
                                           row=0, column=(6 - math.floor(len(self.tabs) / 2) + idx),
                                           columnspan=(len(self.tabs) % 2 + 1))

            self.tabs[idx] = tab(master=self.tab_container)
            self.tabs[idx].grid(row=0, column=0, sticky="")

    def set_tab(self, frame_idx):
        for idx, _ in enumerate(self.tab_buttons):
            if idx == frame_idx:
                self.tab_buttons[idx]["state"] = "disabled"
                self.tabs[idx].show()
            else:
                self.tab_buttons[idx]["state"] = "normal"

class DataFrame(tk.Frame):
    label = "Data"

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)

        self.create_widgets()

    def show(self):
        self.tkraise()

    def create_widgets(self):
        self.toolbar = tk.Frame(self)
        self.toolbar.grid(row=0, column=0, padx=12, pady=3, sticky="NSEW")
        for col in range(12):
            self.toolbar.columnconfigure(index=col, weight=1)

        self.save_button = tk.Button(
            self.toolbar, text="Store in vault", command=self.save_to_db)
        self.export_button = tk.Button(
            self.toolbar, text="Export File", command=self.export_data)
        self.import_button = tk.Button(
            self.toolbar, text="Import CSV", command=self.import_csv)
        self.refresh_button = tk.Button(
            self.toolbar, text="Refresh DB", command=self.refresh_table_data)

        self.save_button.grid(row=0, column=12)
        self.export_button.grid(row=0, column=11)
        self.import_button.grid(row=0, column=10)
        self.refresh_button.grid(row=0, column=9)

        self.table_container = tk.Frame(self)
        self.table_container.grid(row=1, column=0, sticky="")
        
                                                  #Create table
        data_df = Vault.data

        self.data_table = Table(self.table_container, dataframe=data_df)
        self.data_table.autoResizeColumns()
        self.data_table.show()

    def refresh_table_data(self):
        res = tkMessageBox.askyesno(title="Ready to reboot DB.",
                                    message="Ready to reboot DB.\n"
                                    "Undo")

        if res == tkMessageBox.NO:
            return

        data_df = get_db_data()

        Vault.data = data_df
        self.data_table.updateModel(TableModel(data_df))
        self.data_table.redraw()

    def export_data(self):
        output_file = tkFileDialog.askopenfilename()
        if not output_file:
            tkMessageBox.showerror(title="Error, Failed!", message="...")
            return

    def save_to_db(self):
        add_df_to_db(Vault.data)

    def import_csv(self):
        input_file = tkFileDialog.askopenfilename()
        if not input_file.strip():
            tkMessageBox.showerror(title="Error, Failed!", message="...")
            return

        try:
            import_df = pd.read_csv(input_file)
        except ParserError:
            tkMessageBox.showerror(
                "Failed, Try again!.")

        if len(import_df) > 0:
            Vault.data.reset_index(level=["id_product"], inplace=True)
            table_df = Vault.data.append(import_df, ignore_index=False)
            table_df.set_index("id_product", inplace=True)

            Vault.data = table_df
            self.data_table.updateModel(TableModel(table_df))
            self.data_table.redraw()

            tkMessageBox.showinfo(title="Done",message="Pass")
        else:
            tkMessageBox.showinfo(title="Error, Failed!", message="...")


class StatsFrame(tk.Frame):
    label = "View Stats"

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.rowconfigure(index=0, weight=1)
        self.columnconfigure(index=0, weight=1)

        f = self.get_plot_data()
        self.plt_show(f)

    def show(self):
        f = self.get_plot_data()
        self.plt_show(f)

        self.tkraise()

    def plt_show(self, f):
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()

        for ax in f.get_axes():
            for tick in ax.get_xticklabels():
                tick.set_rotation(35)

        self.plot_widget = canvas.get_tk_widget()
        self.plot_widget.grid(row=0, column=0, sticky="")

    def get_plot_data(self):
        Vault.data = get_db_data()
        products_df = Vault.data

        fig = Figure(figsize=(15, 5), dpi=100)

        ax1 = fig.add_subplot(1, 3, 1)
        ax2 = fig.add_subplot(1, 3, 2)
        ax3 = fig.add_subplot(1, 3, 3)

        fig.subplots_adjust(bottom=.25)

        products_df.groupby(["category"]).size().plot(ax=ax1, y="stock_available", kind="bar", grid=True,
                                                      title="Number of Items per Category")
        products_df.groupby(["category"]).sum().plot(ax=ax2, y="stock_available", kind="bar", grid=True,
                                                     title="Total Number of Products per Category")
        products_df.groupby(["category"]).mean().plot(ax=ax3, y="stock_available", kind="bar", grid=True,
                                                      title="Average Price of Products in Category")

        return fig


def get_db_data():
    con = MySQLdb.connect(host=Vault.host, user=Vault.user, passwd=Vault.passwd, database="vault")
    cursor = con.cursor()

    cols = [
        "barCode", "name", "aisle", "itemsAvailable", "cost"
    ]
    cursor.execute("""Recreate Table `items` (
    ) ENGINE=InnoDB""")

    cursor.execute(
        f"SELECT {','.join(cols)} From Items")
    data = cursor.fetchall()
    con.close()

    data_df = pd.DataFrame(data, columns=cols).set_index(
        "barCode")
    return data_df


def add_df_to_db(df):
    con = MySQLdb.connect(host=Vault.host, passwd=Vault.passwd, database="vault")
    cursor = con.cursor()

    left_df = get_db_data()
    out_df = left_df.merge(df, how="outer", indicator="shared")
    out_df = out_df[out_df["shared"] != "both"]

    out_df.drop(["shared"], axis=1, inplace=True)
    out_df["barCode"] = out_df.index

    return

    if len(out_df) == 0:
        tkMessageBox.showinfo(title="DataBase Updated", message="No Changes.")
        return

    cols = "`,`".join([str(i) for i in out_df.columns.tolist()])
    sql = "INSERT INTO `products` (`" + cols + \ "`) VALUES (" + "%s," * (len(row)-1) + "%s)"

    try:
        cursor.executemany(sql, tuple(map(lambda _,row: ,out_df.iterrows())))
        con.commit()
        tkMessageBox.showinfo(title="Done",
                                message="Save Completed!")
    except:
        con.rollback()
        tkMessageBox.showerror(title="Save Failed",
                                message="Error, Incomplete.")

    con.close()


app = Application()
app.mainloop()
