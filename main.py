from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivy.lang import Builder
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

import pandas as pd

KOREAN_FONT = "./font/NanumGothic.ttf"
BUDGET_FILE = "./DB/budget.csv"
TRANSACTION_FILE = "./DB/transaction.csv"
STATUS_FILE = "./DB/status.csv"

class FileBox(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"

        self.file_chooser = FileChooserListView(path='./DB', size_hint=(1, 0.5))
        self.file_chooser.bind(on_touch_down=self.load_csv)
        self.add_widget(self.file_chooser)

        # Create a TextInput widget for editing the CSV file
        self.file_editor = TextInput(size_hint=(1, 0.5), multiline=True, font_name=KOREAN_FONT)
        self.add_widget(self.file_editor)

        # Create a button to run the CSV file operation
        run_button = MDRaisedButton(text='Save CSV', size_hint=(1, 0.1))
        run_button.bind(on_press=self.save_csv)
        self.add_widget(run_button)

    def load_csv(self, instance, touch):
        # Get the file path from the TextInput widget
        if touch.is_double_tap and self.file_chooser.collide_point(*touch.pos):
            selected_file = self.file_chooser.selection[0]

            df = pd.read_csv(selected_file)
            self.file_editor.text = df.to_csv(index=False)

    def save_csv(self, instance):
        # Get the file path from the TextInput widget
        file_path = self.file_chooser.selection[0]

        # Save the contents of the file editor widget to the CSV file
        with open(file_path, 'w', encoding='utf-8') as csv_file:
            csv_file.write(f"{self.file_editor.text}")

        self.calculate()

    def calculate(self):
        budget = pd.read_csv(BUDGET_FILE)
        budget.set_index(keys='종목', inplace=True)

        transaction = pd.read_csv(TRANSACTION_FILE)
        transaction.fillna({'금액': (transaction['단가'] * transaction['수량']).round(2)}, inplace=True)
        transaction.drop('일자', axis=1, inplace=True)
        transaction_group = transaction.groupby(['종목', '거래유형']).agg(sum)
        transaction_group['평단'] = transaction_group['금액'] / transaction_group['수량']
        transaction_group = transaction_group.reset_index(level=[1])

        transaction_group_sell = transaction_group[transaction_group['거래유형'] == '매도'] 
        transaction_group_buy =  transaction_group[transaction_group['거래유형'] == '매수']

        transaction_group_buy_sell = pd.merge(transaction_group_buy, transaction_group_sell, on='종목', how='left')
        transaction_group_buy_sell["거래유형_y"].fillna("매도", inplace=True)
        transaction_group_buy_sell.fillna(0, inplace=True)

        transaction_group_buy_sell = pd.merge(budget, transaction_group_buy_sell, on="종목", how='right')
        transaction_group_buy_sell["예산"].fillna(0, inplace=True)

        transaction_group_buy_sell['현재보유량'] = transaction_group_buy_sell["수량_x"].astype(int) - transaction_group_buy_sell["수량_y"].astype(int)
        transaction_group_buy_sell['현재매수금액'] = transaction_group_buy_sell["금액_x"] - transaction_group_buy_sell["금액_y"]
        transaction_group_buy_sell['현재평단'] = transaction_group_buy_sell['현재매수금액'] / transaction_group_buy_sell['현재보유량'] 
        transaction_group_buy_sell['매수가능금액'] = transaction_group_buy_sell["예산"] - transaction_group_buy_sell["금액_x"] + transaction_group_buy_sell["금액_y"]

        transaction_group_buy_sell.rename(columns={"금액_x": "매수금액",
                                                    "수량_x": "매수량",
                                                    "평단_x": "매수평단",
                                                    "금액_y": "매도금액",
                                                    "수량_y": "매도량",
                                                    "평단_y": "매도평단"}, inplace=True)
        transaction_group_buy_sell.drop(columns=['거래유형_x', '거래유형_y'], inplace=True)

        # total_buy_available = budget["예산"].sum() - transaction_group_buy_sell['현재매수금액'].sum()
        # total_over_budget =  transaction_group_buy_sell.loc[transaction_group_buy_sell["매수가능금액"] < 0, "매수가능금액"].sum()
        # print(f"total_buy_available: {total_buy_available:.2f}")
        # print(f"total_over_budget: {total_over_budget:.2f}")
        transaction_group_buy_sell = transaction_group_buy_sell.applymap(format_float)
        transaction_group_buy_sell.to_csv(STATUS_FILE)

class StatusBox(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.filepath = STATUS_FILE

        self.data_table = MDDataTable(size_hint=(1, 1),
                                       column_data=self.gen_column_data(),
                                       row_data=self.gen_row_data(),
                                       rows_num = 10,
                                       use_pagination=True)
        self.add_widget(self.data_table)
        self.display_status()

        refresh_button = MDRaisedButton(text='Refresh', size_hint=(1, 0.1))
        refresh_button.bind(on_press=self.on_click_refresh)
        self.add_widget(refresh_button)



    def gen_column_data(self):
        header = pd.read_csv(self.filepath , nrows=0).columns.tolist()
        column_data = []
        for col in header:
            column_data.append((f'[font={KOREAN_FONT}]{col}[/font]', dp(20)))
        return column_data
    
    def gen_row_data(self):
        df = pd.read_csv(self.filepath)
        def change_font(x):
            return f'[font={KOREAN_FONT}]{x}[/font]'
        df['종목'] = df['종목'].apply(change_font)
        return list(df.itertuples(index=False, name=None))
    
    def display_status(self):
        row_data = self.gen_row_data()
        self.data_table.update_row_data(instance_data_table=self.data_table,
                                        data=row_data)

    def on_click_refresh(self, instance):
        self.display_status()
        

class BudgetBox(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.filepath = BUDGET_FILE

        self.data_table = MDDataTable(size_hint=(1, 1),
                                       column_data=self.gen_column_data(),
                                       row_data=self.gen_row_data(),
                                       rows_num = 10,
                                       use_pagination=True)
        self.add_widget(self.data_table)
        self.display_status()

        refresh_button = MDRaisedButton(text='Refresh', size_hint=(1, 0.1))
        refresh_button.bind(on_press=self.on_click_refresh)
        self.add_widget(refresh_button)


    def gen_column_data(self):
        header = pd.read_csv(self.filepath , nrows=0).columns.tolist()
        column_data = []
        for col in header:
            column_data.append((f'[font={KOREAN_FONT}]{col}[/font]', dp(20)))
        return column_data
    
    def gen_row_data(self):
        df = pd.read_csv(self.filepath )
        def change_font(x):
            return f'[font={KOREAN_FONT}]{x}[/font]'
        df['종목'] = df['종목'].apply(change_font)
        return list(df.itertuples(index=False, name=None))

    def display_status(self):
        row_data = self.gen_row_data()
        self.data_table.update_row_data(instance_data_table=self.data_table,
                                        data=row_data)
        
    def on_click_refresh(self, instance):
        self.display_status()

        
class TransactionBox(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.filepath = TRANSACTION_FILE

        self.data_table = MDDataTable(size_hint=(1, 1),
                                       column_data=self.gen_column_data(),
                                       row_data=self.gen_row_data(),
                                       rows_num = 10,
                                       use_pagination=True)
        self.add_widget(self.data_table)
        self.display_status()

        refresh_button = MDRaisedButton(text='Refresh', size_hint=(1, 0.1))
        refresh_button.bind(on_press=self.on_click_refresh)
        self.add_widget(refresh_button)


    def gen_column_data(self):
        header = pd.read_csv(self.filepath , nrows=0).columns.tolist()
        column_data = []
        for col in header:
            column_data.append((f'[font={KOREAN_FONT}]{col}[/font]', dp(20)))
        return column_data
    
    def gen_row_data(self):
        df = pd.read_csv(self.filepath)
        df.fillna({'금액': (df['단가'] * df['수량']).round(2)}, inplace=True)
        def change_font(x):
            return f'[font={KOREAN_FONT}]{x}[/font]'
        df['종목'] = df['종목'].apply(change_font)
        df['거래유형'] = df['거래유형'].apply(change_font)
        return list(df.itertuples(index=False, name=None))

    def display_status(self):
        row_data = self.gen_row_data()
        self.data_table.update_row_data(instance_data_table=self.data_table,
                                        data=row_data)
    
    def on_click_refresh(self, instance):
        self.display_status()

class FilesItem(MDBottomNavigationItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.orientation = "vertical"
        self.filebox = FileBox()
        self.add_widget(self.filebox)
  

class StatusItem(MDBottomNavigationItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.orientation = "vertical"
        self.status_box = StatusBox()
        self.add_widget(self.status_box)


class BudgetItem(MDBottomNavigationItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.orientation = "vertical"
        self.budget_box = BudgetBox()
        self.add_widget(self.budget_box)


class TransactionItem(MDBottomNavigationItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.orientation = "vertical"
        self.transaction_box = TransactionBox()
        self.add_widget(self.transaction_box)
  

def format_float(x):
    if isinstance(x, float):
        return f'{x:.2f}'
    else:
        return x


class StockApp(MDApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"

        root = MDBottomNavigation()
        self.navigation_item4 = FilesItem(name='files', text='files')
        self.navigation_item4.filebox.calculate()  
        self.navigation_item1 = StatusItem(name='status', text='status')
        self.navigation_item2 = BudgetItem(name='budget', text='budget')
        self.navigation_item3 = TransactionItem(name='transaction', text='transaction')

        root.add_widget(self.navigation_item1)
        root.add_widget(self.navigation_item2)
        root.add_widget(self.navigation_item3)
        root.add_widget(self.navigation_item4)

        return root


if __name__ == '__main__':
    StockApp().run()