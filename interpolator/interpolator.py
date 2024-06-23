'''
First PyQt Program: Simple Data Fit & Interpolator Program
2024-06-22 KCK

'''

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QTableWidget, QTableWidgetItem, QPushButton,
                               QLabel, QLineEdit, QSplitter, QComboBox, QFileDialog)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import pandas as pd
from scipy.interpolate import make_interp_spline
from scipy.interpolate import splrep, BSpline


class TableWidget(QTableWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy)
        self.addAction(copy_action)

        # Paste action
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste)
        self.addAction(paste_action)

        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected)
        self.addAction(delete_action)


    def copy(self):
        selected = self.selectedRanges()
        # if selected:
        #     data = ''
        #     for range in selected:
        #         for row in range(range.topRow(), range.bottomRow() + 1):
        #             for col in range(range.leftColumn(), range.rightColumn() + 1):
        #                 if self.item(row, col):
        #                     data += self.item(row, col).text() + '\t'
        #                 else:
        #                     data += '\t'
        #             data = data.strip() + '\n'
        #     QApplication.clipboard().setText(data.strip())
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return
        
        copied_data = ""
        for selection in selected_ranges:
            top_row, bottom_row = selection.topRow(), selection.bottomRow()
            left_col, right_col = selection.leftColumn(), selection.rightColumn()

            for row in range(top_row, bottom_row + 1):
                row_data = []
                for col in range(left_col, min(right_col + 1, 2)):  # limit to 2 columns
                    item = self.item(row, col)
                    row_data.append(item.text() if item else "")
                copied_data += "\t".join(row_data) + "\n"
        
        QApplication.clipboard().setText(copied_data.strip())

    def paste(self):
        clipboard = QApplication.clipboard()
        data = clipboard.text()
        if data:
            rows = data.split('\n')
            current_row = self.currentRow()
            current_col = self.currentColumn()
            
            # Check if we need to add rows
            required_rows = current_row + len(rows)
            if required_rows > self.rowCount():
                self.setRowCount(required_rows)
            
            for r, row_data in enumerate(rows):
                # cols = row_data.split('\t')
                
                # # Check if we need to add columns
                # required_cols = current_col + len(cols)
                # if required_cols > self.columnCount():
                #     self.setColumnCount(required_cols)

                cols = row_data.split('\t')[:2]  # Limit to 2 columns
                
                for c, col_data in enumerate(cols):
                    self.setItem(current_row + r, current_col + c, QTableWidgetItem(col_data))

    def delete_selected(self):
        for item in self.selectedItems():
            self.setItem(item.row(), item.column(), QTableWidgetItem(""))

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy()
        elif event.matches(QKeySequence.Paste):
            self.paste()
        elif event.key() in [Qt.Key_Backspace, Qt.Key_Delete]:
            self.delete_selected()
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DataFit & Interpolation Tool v1.0")

        self.x_data = []
        self.y_data = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        # Input column
        self.input_column = QVBoxLayout()
        self.layout.addLayout(self.input_column)

        # Plot column
        self.plot_column = QVBoxLayout()
        self.layout.addLayout(self.plot_column)

        # Output column
        self.output_column = QVBoxLayout()
        self.layout.addLayout(self.output_column)

        # Input column widgets
        self.input_label = QLabel("Input Data")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setStyleSheet("font-weight: bold")
        self.input_column.addWidget(self.input_label)

        self.input_table = TableWidget(10, 2)
        self.input_table.setHorizontalHeaderLabels(["X", "Y"])
        self.input_column.addWidget(self.input_table)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_table)
        self.clear_button.setStyleSheet("background-color: lightgrey; color: black;")
        self.input_column.addWidget(self.clear_button)

        self.add_button = QPushButton("Add Row")
        self.add_button.clicked.connect(self.add_row)
        self.add_button.setStyleSheet("background-color: lightgrey; color: black;")
        self.input_column.addWidget(self.add_button)

        self.swap_button = QPushButton("Swap X and Y")
        self.swap_button.clicked.connect(self.swap_x_y)
        self.swap_button.setStyleSheet("background-color: lightblue; color: black;")
        self.input_column.addWidget(self.swap_button)

        self.dropdown = QComboBox()
        self.dropdown.addItems(["Linear Interpolation", "Linear Regression", "Smoothing Spline", "Step Interpolation"])
        self.dropdown.setCurrentIndex(1)
        self.input_column.addWidget(self.dropdown)

        self.plot_button = QPushButton("Plot and Fit Regression")
        self.plot_button.clicked.connect(self.plot_and_fit)
        self.plot_button.setStyleSheet("background-color: lightpink; color: black;")
        self.input_column.addWidget(self.plot_button)

        self.coefficients_label = QLabel("Coefficients: ")
        self.input_column.addWidget(self.coefficients_label)

        self.dx_input = QLineEdit()
        self.dx_input.setPlaceholderText("Enter dx value")
        self.input_column.addWidget(self.dx_input)

        self.generate_button = QPushButton("Generate Sampled Data")
        self.generate_button.clicked.connect(self.generate_sampled_data)
        self.generate_button.setStyleSheet("background-color: lightgreen; color: black;")
        self.input_column.addWidget(self.generate_button)

        # Output column widgets
        self.output_label = QLabel("Output Data")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("font-weight: bold")
        self.output_column.addWidget(self.output_label)

        self.output_table = TableWidget(0, 2)
        self.output_table.setHorizontalHeaderLabels(["X", "Y (Fitted)"])
        self.output_table.itemSelectionChanged.connect(self.highlight_selected_data)
        self.output_column.addWidget(self.output_table)

        copy_output_button = QPushButton("Copy Output Table")
        copy_output_button.clicked.connect(self.copy_output_table)
        copy_output_button.setStyleSheet("background-color: lightgrey; color: black;")
        self.output_column.addWidget(copy_output_button)

        save_output_button = QPushButton("Save Output to CSV")
        save_output_button.clicked.connect(self.save_output_to_csv)
        save_output_button.setStyleSheet("background-color: lightgrey; color: black;")
        self.output_column.addWidget(save_output_button)

        # Plot column widgets
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.plot_column.addWidget(self.canvas)

        # Set initial window size and center it on the screen
        self.resize(1100, 600)
        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def add_row(self):
        row_position = self.input_table.rowCount()
        self.input_table.insertRow(row_position)

    def clear_table(self):
        self.input_table.clearContents()
        self.input_table.setRowCount(10)
        self.input_table.setColumnCount(2)

    def swap_x_y(self):
        for row in range(self.input_table.rowCount()):
            x_item = self.input_table.item(row, 0)
            y_item = self.input_table.item(row, 1)
            if x_item and y_item:
                x_text = x_item.text()
                y_text = y_item.text()
                self.input_table.setItem(row, 0, QTableWidgetItem(y_text))
                self.input_table.setItem(row, 1, QTableWidgetItem(x_text))

    def plot_and_fit(self):
        self.x_data = []
        self.y_data = []

        rows_to_delete = []
        for row in range(self.input_table.rowCount()):
            try:
                x_item = self.input_table.item(row, 0)
                y_item = self.input_table.item(row, 1)
                if x_item is None or y_item is None or x_item.text().strip() == "" or y_item.text().strip() == "":
                    rows_to_delete.append(row)
                    continue
                x = float(x_item.text())
                y = float(y_item.text())
                self.x_data.append(x)
                self.y_data.append(y)
            except ValueError:
                rows_to_delete.append(row)
                continue

        if len(self.x_data) < 2 or len(self.y_data) < 2:
            self.coefficients_label.setText("Coefficients: Error - Need at least two data points.")
            return

        # Delete rows with blank or invalid data
        for row in reversed(rows_to_delete):
            self.input_table.removeRow(row)

        self.x_data = np.array(self.x_data)
        self.y_data = np.array(self.y_data)

        method = self.dropdown.currentText()

        # Perform linear regression
        if method == 'Linear Regression':
            A = np.vstack([self.x_data, np.ones(len(self.x_data))]).T
            self.slope, self.intercept = np.linalg.lstsq(A, self.y_data, rcond=None)[0]
            self.coefficients_label.setText(f"Coefficients: Slope = {self.slope:.2f}, Intercept = {self.intercept:.2f}")
            self.y_fitted = self.slope * self.x_data + self.intercept
            self.x_fitted = self.x_data
        elif method == 'Linear Interpolation':
            # sorted_indices = np.argsort(self.x_data)
            # self.x_data = self.x_data[sorted_indices]
            # self.y_data = self.y_data[sorted_indices]
            # spline = make_interp_spline(self.x_data, self.y_data)
            # self.y_fitted = spline(self.x_data)
            # self.coefficients_label.setText("Interpolation: Linear")
            sorted_indices = np.argsort(self.x_data)
            self.x_data = self.x_data[sorted_indices]
            self.y_data = self.y_data[sorted_indices]
            self.y_fitted = np.interp(self.x_data, self.x_data, self.y_data)
            self.coefficients_label.setText("Interpolation: Linear")
            self.x_fitted = self.x_data
            if len(np.unique(self.x_data)) != len(self.x_data):
                self.coefficients_label.setText("Interpolation: Linear Error - X data not monotonically increasing.")
        elif method == 'Smoothing Spline':
            sorted_indices = np.argsort(self.x_data)
            self.x_data = self.x_data[sorted_indices]
            self.y_data = self.y_data[sorted_indices]
            tck = splrep(self.x_data, self.y_data, s=0)  # s=0 for smoothing spline
            self.x_fitted = np.linspace(self.x_data.min(), self.x_data.max(), 5000) # Use at least 5000 points for a good approx
            self.y_fitted = BSpline(*tck)(self.x_fitted)
            self.coefficients_label.setText("Interpolation: Spline")
        elif method == 'Step Interpolation':
            sorted_indices = np.argsort(self.x_data)
            self.x_data = self.x_data[sorted_indices]
            self.y_data = self.y_data[sorted_indices]
            self.x_fitted = np.linspace(self.x_data.min(), self.x_data.max(), 2000)
            indices = np.searchsorted(self.x_data, self.x_fitted, side='right') - 1
            indices = np.clip(indices, 0, len(self.y_data) - 1)
            self.y_fitted = self.y_data[indices]
            self.coefficients_label.setText("Interpolation: Step")

        # Plot data and regression line
        self.plot_data()

        # Pre-populate sampling dx if empty
        if self.dx_input.text() == "":
            dx = np.round((self.x_data.max() - self.x_data.min())/len(self.x_data)/0.1)*0.1
            self.dx_input.setText(str(dx))

    def plot_data(self):
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, 'o', mfc='w', label='Original data')
        if self.dropdown.currentText() == 'Step Interpolation':
            self.ax.step(self.x_fitted, self.y_fitted, where='post', c='r', label='Step Interpolated')
        elif self.dropdown.currentText() == 'Smoothing Spline':
            self.ax.plot(self.x_fitted, self.y_fitted, 'r', label='Spline Interpolated')
        else:
            self.ax.plot(self.x_fitted, self.y_fitted, 'r', label='Fitted/Interpolated')
        self.ax.legend()
        self.canvas.draw()

    def highlight_selected_data(self):
        selected_rows = sorted(set(idx.row() for idx in self.output_table.selectedIndexes()))

        # Redraw the original data plot
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, 'o', mfc='w', label='Original data')
        if self.dropdown.currentText() == 'Step Interpolation':
            self.ax.step(self.x_fitted, self.y_fitted, where='post', c='r', label='Step Interpolated')
        elif self.dropdown.currentText() == 'Smoothing Spline':
            self.ax.plot(self.x_fitted, self.y_fitted, 'r', label='Spline Interpolated')
        else:
            self.ax.plot(self.x_fitted, self.y_fitted, 'r', label='Fitted/Interpolated')

        self.plot_data()
        self.ax.plot(self.sampled_x, self.sampled_y, 'o', c='k', mfc='w', label='Output data')

        # Highlight selected data points
        selected_x = [float(self.output_table.item(row, 0).text()) for row in selected_rows]
        selected_y = [float(self.output_table.item(row, 1).text()) for row in selected_rows]
        self.ax.plot(selected_x, selected_y, 'o', c='b', mfc='y')

        self.ax.legend()
        self.canvas.draw()

    def generate_sampled_data(self):
        # Updat the fit in case the data was swapped or method changed between resampling
        self.plot_and_fit()
        
        dx = self.dx_input.text()
        try:
            dx = float(dx)
        except ValueError:
            return

        if len(self.x_data) == 0 or len(self.y_data) == 0:
            return

        min_x = min(self.x_data)
        max_x = max(self.x_data)
        sampled_x = np.arange(min_x, max_x, dx)

        method = self.dropdown.currentText()
        if method == 'Linear Regression':
            sampled_y = self.slope * sampled_x + self.intercept
        elif method == 'Linear Interpolation':
            # Sort the data by x before interpolation
            sorted_indices = np.argsort(self.x_data)
            x_sorted = self.x_data[sorted_indices]
            y_sorted = self.y_data[sorted_indices]
            sampled_y = np.interp(sampled_x, x_sorted, y_sorted)
        elif method == 'Smoothing Spline':
            sorted_indices = np.argsort(self.x_data)
            x_sorted = self.x_data[sorted_indices]
            y_sorted = self.y_data[sorted_indices]
            spline = make_interp_spline(x_sorted, y_sorted)
            sampled_y = spline(sampled_x)
        elif method == 'Step Interpolation':
            sorted_indices = np.argsort(self.x_data)
            x_sorted = self.x_data[sorted_indices]
            y_sorted = self.y_data[sorted_indices]
            indices = np.searchsorted(x_sorted, sampled_x, side='right') - 1
            indices = np.clip(indices, 0, len(y_sorted) - 1)
            sampled_y = y_sorted[indices]

        self.output_table.setRowCount(len(sampled_x))
        for i in range(len(sampled_x)):
            self.output_table.setItem(i, 0, QTableWidgetItem(f"{sampled_x[i]:.2f}"))
            self.output_table.setItem(i, 1, QTableWidgetItem(f"{sampled_y[i]:.2f}"))
        
        self.sampled_x = sampled_x
        self.sampled_y = sampled_y
        
        self.plot_data()
        self.ax.plot(sampled_x, sampled_y, 'o', c='k', mfc='w', label='Output data')
        self.ax.legend()
        self.canvas.draw()


    def copy_output_table(self):
        data = ""
        for row in range(self.output_table.rowCount()):
            row_data = []
            for col in range(self.output_table.columnCount()):
                item = self.output_table.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            data += "\t".join(row_data) + "\n"
        QApplication.clipboard().setText(data)

    def save_output_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV files (*.csv)")
        if path:
            data = []
            for row in range(self.output_table.rowCount()):
                row_data = []
                for col in range(self.output_table.columnCount()):
                    item = self.output_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            df = pd.DataFrame(data, columns=["X", "Y (Fitted)"])
            df.to_csv(path, index=False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
