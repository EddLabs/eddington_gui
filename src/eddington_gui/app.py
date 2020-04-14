"""
A gui library wrapping Eddington
"""
from collections import OrderedDict
from pathlib import Path
from typing import List

from eddington_matplotlib import (
    plot_fitting,
    plot_residuals,
    plot_data,
    OutputConfiguration,
    plot_all,
)
from eddington_core import fit_to_data, FitData, FitResult, EddingtonException

import numpy as np
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, FANTASY

from eddington_gui.boxes.data_columns_box import DataColumnsBox
from eddington_gui.boxes.fitting_function_box import FittingFunctionBox
from eddington_gui.boxes.header_box import HeaderBox
from eddington_gui.boxes.initial_guess_box import InitialGuessBox
from eddington_gui.boxes.input_file_box import InputFileBox
from eddington_gui.boxes.line_box import LineBox
from eddington_gui.boxes.plot_configuration_box import PlotConfigurationBox
from eddington_gui.consts import WINDOW_SIZE, BIG_PADDING, MAIN_BOTTOM_PADDING, SMALL_PADDING
from eddington_gui.window.records_choice_window import RecordsChoiceWindow


class EddingtonGUI(toga.App):

    input_file_box: InputFileBox
    fitting_function_box: FittingFunctionBox
    initial_guess_box: InitialGuessBox
    plot_configuration_box: PlotConfigurationBox
    data_columns_box: DataColumnsBox
    output_directory_input: toga.TextInput

    __chosen_records: List[bool] = None
    __fit_data: FitData = None
    __a0: np.ndarray = None
    __fit_result: FitResult = None

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box(style=Pack(direction=COLUMN))
        main_box.add(HeaderBox())

        self.input_file_box = InputFileBox(flex=1)
        self.input_file_box.add_handler(lambda data_dict: self.reset_all())
        self.input_file_box.add_handler(self.init_chosen_records)
        main_box.add(self.input_file_box)

        self.fitting_function_box = FittingFunctionBox(flex=1)
        self.fitting_function_box.add_handler(lambda fit_func: self.reset_fit_result())
        main_box.add(self.fitting_function_box)

        self.initial_guess_box = InitialGuessBox()
        self.initial_guess_box.add_handler(lambda a0: self.reset_fit_result())
        self.fitting_function_box.add_handler(self.set_parameters_number)
        main_box.add(self.initial_guess_box)

        self.data_columns_box = DataColumnsBox(flex=5)
        self.data_columns_box.add_handler(lambda columns: self.reset_all())
        self.input_file_box.add_handler(self.data_columns_box.update_data_dict)

        self.plot_configuration_box = PlotConfigurationBox(flex=5)
        self.fitting_function_box.add_handler(
            self.plot_configuration_box.load_fit_function
        )
        self.data_columns_box.add_handler(self.plot_configuration_box.load_columns)

        main_box.add(
            toga.Box(
                style=Pack(direction=ROW, padding_top=BIG_PADDING, flex=1),
                children=[
                    self.data_columns_box,
                    toga.Box(style=Pack(flex=2)),
                    self.plot_configuration_box,
                ],
            )
        )
        main_box.add(
            LineBox(
                children=[
                    toga.Button(label="Choose Records", on_press=self.choose_records)
                ]
            )
        )
        main_box.add(toga.Box(style=Pack(flex=1)))
        main_box.add(
            LineBox(
                children=[
                    toga.Button(label="Fit", on_press=self.fit, style=Pack(flex=1))
                ],
            )
        )
        main_box.add(
            LineBox(
                children=[
                    toga.Button(
                        label="Plot data", on_press=self.plot_data, style=Pack(flex=1)
                    ),
                    toga.Button(
                        label="Plot Fitting", on_press=self.plot, style=Pack(flex=1)
                    ),
                    toga.Button(
                        label="Residuals", on_press=self.residuals, style=Pack(flex=1)
                    ),
                ],
            )
        )
        self.output_directory_input = toga.TextInput(style=Pack(flex=1))
        main_box.add(
            LineBox(
                padding_bottom=MAIN_BOTTOM_PADDING,
                children=[
                    toga.Label(text="Output directory:"),
                    self.output_directory_input,
                    toga.Button(
                        label="Choose directory",
                        on_press=self.choose_output_dir,
                        style=Pack(padding_left=SMALL_PADDING),
                    ),
                    toga.Button(
                        label="Save",
                        on_press=self.save_to_output_dir,
                        style=Pack(
                            padding_left=SMALL_PADDING, padding_right=SMALL_PADDING
                        ),
                    ),
                ],
            )
        )

        self.main_window = toga.MainWindow(title=self.formal_name, size=WINDOW_SIZE)
        self.main_window.content = main_box
        self.main_window.show()

    @property
    def fit_data(self):
        if self.__fit_data is None:
            self.__calculate_fit_data()
        return self.__fit_data

    @fit_data.setter
    def fit_data(self, fit_data):
        self.__fit_data = fit_data

    @property
    def fit_result(self):
        if self.__fit_result is None:
            self.__calculate_fit_result()
        return self.__fit_result

    @fit_result.setter
    def fit_result(self, fit_result):
        self.__fit_result = fit_result

    def choose_records(self, widget):
        if self.input_file_box.data_dict is None:
            self.main_window.info_dialog(
                title="Choose Records", message="No data been given yet"
            )
            return
        window = RecordsChoiceWindow(
            data_dict=self.input_file_box.data_dict,
            initial_chosen_records=self.__chosen_records,
            save_action=self.save_chosen_records,
        )
        window.show()
        self.reset_all()

    def fit(self, widget):
        if self.fit_result is None:
            self.main_window.info_dialog(
                title="Fit Result", message="Nothing to fit yet"
            )
        else:
            self.main_window.info_dialog(
                title="Fit Result", message=str(self.fit_result)
            )

    def plot_data(self, widget):
        if self.fit_data is None:
            self.show_nothing_to_plot()
        else:
            plot_data(
                data=self.fit_data,
                plot_configuration=self.plot_configuration_box.plot_configuration,
            )

    def plot(self, widget):
        if self.fit_result is None:
            self.show_nothing_to_plot()
        else:
            plot_fitting(
                func=self.fitting_function_box.fit_function,
                data=self.fit_data,
                plot_configuration=self.plot_configuration_box.plot_configuration,
                a=self.fit_result.a,
            )

    def residuals(self, widget):
        if self.fit_result is None:
            self.show_nothing_to_plot()
        else:
            plot_residuals(
                func=self.fitting_function_box.fit_function,
                data=self.fit_data,
                plot_configuration=self.plot_configuration_box.plot_configuration,
                a=self.fit_result.a,
            )

    def choose_output_dir(self, widget):
        try:
            folder_path = self.main_window.select_folder_dialog(
                title="Output directory"
            )
        except ValueError:
            return
        self.output_directory_input.value = folder_path[0]

    def save_to_output_dir(self, widget):
        if self.fit_result is None:
            self.show_nothing_to_plot()
            return
        output_dir = Path(self.output_directory_input.value)
        if not output_dir.exists():
            output_dir.mkdir()
        func_name = self.fitting_function_box.fit_function.name
        output_configuration = OutputConfiguration.build(
            base_name=func_name, output_dir=output_dir,
        )
        plot_all(
            func=self.fitting_function_box.fit_function,
            data=self.fit_data,
            plot_configuration=self.plot_configuration_box.plot_configuration,
            output_configuration=output_configuration,
            result=self.fit_result,
        )
        self.main_window.info_dialog(
            title="Save output", message="All plots have been saved successfully!"
        )

    def show_nothing_to_plot(self):
        self.main_window.info_dialog(title="Fit Result", message="Nothing to plot yet")

    def reset_fit_data(self):
        self.fit_data = None

    def reset_fit_result(self):
        self.fit_result = None

    def reset_all(self):
        self.reset_fit_data()
        self.reset_fit_result()
        self.initial_guess_box.reset_initial_guess()
        self.plot_configuration_box.reset_plot_configuration()

    def set_parameters_number(self, func):
        if func is None:
            self.initial_guess_box.n = None
        else:
            self.initial_guess_box.n = func.n

    def init_chosen_records(self, data_dict):
        if data_dict is None:
            self.save_chosen_records([])
        else:
            self.save_chosen_records([True] * len(list(data_dict.values())[0]))

    def save_chosen_records(self, chosen_records):
        self.__chosen_records = chosen_records

    def __calculate_fit_data(self):
        if self.input_file_box.data_dict is None:
            self.fit_data = None
            return
        data_dict = OrderedDict()
        for key, value in self.input_file_box.data_dict.items():
            data_dict[key] = np.array(value)[self.__chosen_records]
        try:
            self.fit_data = FitData(
                x=data_dict[self.data_columns_box.x_column],
                xerr=data_dict[self.data_columns_box.xerr_column],
                y=data_dict[self.data_columns_box.y_column],
                yerr=data_dict[self.data_columns_box.yerr_column],
            )
        except EddingtonException as e:
            self.main_window.error_dialog(
                title="Fit data error", message=str(e),
            )
            self.fit_data = None
            return
        self.plot_configuration_box.set_xmin_xmax(self.fit_data.x)

    def __calculate_fit_result(self):
        self.fitting_function_box.initialize_fit_func()
        if (
            self.fit_data is None
            or self.fitting_function_box.fit_function is None
            or self.initial_guess_box.a0 is None
        ):
            self.fit_result = None
            return
        try:
            self.fit_result = fit_to_data(
                data=self.fit_data,
                func=self.fitting_function_box.fit_function,
                a0=self.initial_guess_box.a0,
            )
        except EddingtonException as e:
            self.main_window.error_dialog(
                title="Fit result error", message=str(e),
            )
            self.fit_result = None
            return


def main():
    return EddingtonGUI()
