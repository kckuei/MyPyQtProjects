# MyPyQtProjects

Miscellaneous small PyQt projects.

## Project 0: Simple DataFit and Interpolation Tool

Tool for [fitting and interpolating data](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/interpolator.py) using linear interpolation, regression, smoothing splines, or step interpolation. User inputs the x-y data, visualizes it, applies different fitting/interpolation methods, then generates the resampled data. Users can copy data directly, export to a CSV file, and highlight selected portions of the data in the plot.

![Smoothing spline](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/assets/example-1-spline.png?raw=true)

![Demo](https://github.com/kckuei/MyPyQtProjects/blob/main/interpolator/assets/peek_demo.gif?raw=true)

Dependencies
* `PySide6 6.7.1` for the GUI components
* `matplotlib 3.9.0` for plotting
* `numpy 1.26.4` for numerical operations
* `pandas 2.2.2` for data handling
* `scipy 1.13.1` for interpolation methods

## Project 1: Simple Annotation and Digitization Tool

Tool for [annotating dimensions and digitizing points](https://github.com/kckuei/MyPyQtProjects/blob/main/imagecal/imageviewer.py) from a user-specified image. This is a knockoff/discount version of two of my favorite/most-used tools at work, Revu BlueBeam, and WebPlotDigitizer. In annotation mode, the user can calibrate the scale, measure dimensions, areas, delete or toggle them on/off. In digitization mode, the user specifies an x- and y-axis, digitize points, or delete them.

Other Implementation Ideas:
* Bezier Curves Digitizer/Interpolator Tool
* Digitize by foreground color/pixel

Dependencies
* `PySide6 6.7.1` for the GUI components
* `matplotlib 3.9.0` for plotting
* `numpy 1.26.4` for numerical operations
* `pandas 2.2.2` for data handling

![Demo](https://github.com/kckuei/MyPyQtProjects/blob/main/imagecal/assets/peek_demo.gif?raw=true)


## Project 2: CPT/SPT Data Processing & Site Characterization Tool

## Other Notes

### Compiling Executables

Tested with `Pyinstaller 6.8.0`

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

### Dependencies

Saving the package list:

```bash
pip freeze > requirements.txt
```

Recreating environment:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/kckuei/MyPyQtProjects/blob/main/LICENSE.txt) file for details.