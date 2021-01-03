"""Window that presents matplotlib figures."""
from pathlib import Path
from typing import Callable

import toga
from matplotlib.figure import Figure
from toga.style import Pack
from toga.style.pack import COLUMN
from toga_chart import Chart

from eddington_gui.boxes.eddington_box import EddingtonBox
from eddington_gui.consts import FontSize


class FigureWindow(toga.Window):  # pylint: disable=too-few-public-methods
    """
    Window that contains a chart with a *matplotlib* figure.

    This is made using toga.Chart widget.
    """

    def __init__(
        self,
        plot_method: Callable[[], Figure],
        title: str,
        app: toga.App,
        font_size: FontSize,
    ):
        """Initialize window."""
        self.plot_method = plot_method
        with self.plot_method() as figure:
            super().__init__(
                title=title,
                size=(1, 1.35) * (figure.get_size_inches() * figure.get_dpi()),
            )
            chart = Chart()

            save_button = toga.Button(label="Save", on_press=self.save_figure)
            save_box = EddingtonBox(children=[save_button])
            chart_box = EddingtonBox(
                children=[chart],
                style=Pack(height=(figure.get_size_inches() * figure.get_dpi())[1]),
            )
            main_box = EddingtonBox(
                children=[chart_box, save_box], style=Pack(direction=COLUMN)
            )
            self.content = main_box
            main_box.set_font_size(font_size)
            chart.draw(figure)
        self.app = app

    def save_figure(self, widget):  # pylint: disable=unused-argument
        """Save file dialog."""
        try:
            output_path = Path(
                self.save_file_dialog(
                    title="Save Figure",
                    suggested_filename="fig",
                    file_types=["png", "jpg", "pdf"],
                )
            )
        except ValueError:
            return

        suffix = output_path.suffix
        if suffix in [".png", ".jpg", ".pdf"]:
            with self.plot_method() as figure:
                figure.savefig(fname=output_path)
        else:
            self.error_dialog(
                title="Invalid File Suffix",
                message=f"Cannot save figure with suffix {suffix} . \n"
                f"allowed formats: png, jpg, pdf.",
            )
