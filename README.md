# MyPyQtProjects


## Project 0: Simple DataFit and Interpolation Tool

Tool for [fitting and interpolating data](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/interpolator.py) using linear interpolation, regression, smoothing splines, or step interpolation. User inputs the x-y data, visualizes it, applies different fitting/interpolation methods, then generates the resampled data. Users can copy data directly, export to a CSV file, and highlight selected portions of the data in the plot.

![Smoothing spline](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/assets/example-1-spline.png?raw=true)

![Linear interpolation](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/assets/example-2-linearinterp.png?raw=true)

![Step interpolation](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/assets/example-3-step.png?raw=true)

Dependencies
* `PySide6` for the GUI components
* `matplotlib` for plotting
* `numpy` for numerical operations
* `pandas` for data handling
* `scipy` for interpolation methods

### Create Executables

Install PyInstaller:
Open your terminal or command prompt and run:

```bash
pip install pyinstaller
```

Create the Executable:
Navigate to the directory where your script is located and run:

```bash
pyinstaller --onefile --windowed your_script_name.py
```

Replace your_script_name.py with the name of your Python script.

    --`onefile` creates a single executable file.
    --`windowed` prevents a console window from appearing (useful for GUI applications).

Find the Executable:
After the process completes, you will find the executable in the dist folder within your project directory.