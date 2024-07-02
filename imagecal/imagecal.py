import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                               QGraphicsPixmapItem, QVBoxLayout, QWidget, QPushButton,
                               QHBoxLayout, QFileDialog, QInputDialog, QSlider, QTabWidget,
                               QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QComboBox, QLabel, QGridLayout)
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QImage, QFont, QPolygonF, QColor
from PySide6.QtCore import Qt, QEvent, QPointF
import math

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scale_factor = None
        self.calibration_points = []  # Stores calibration points
        self.measurement_points = []  # Stores measurement points
        self.measurements = []  # Stores lines and distances
        self.areas = []  # Stores polygons and their areas
        self.current_polygon = []  # Stores points for the current polygon
        self.delete_mode = False
        self.delete_point_mode = False
        self.measure_area_mode = False
        self.annotations_visible = True
        self.text_labels_visible = True
        self.pen = QPen(Qt.red, 10, Qt.SolidLine)  # Initialize the pen attribute here
        self.clean_image = None  # This will hold the clean copy of the image
        self.delete_candidate = None  # To track which line is a candidate for deletion
        self.delete_point_candidate = None  # To track which point is a candidate for deletion
        self.zoom_factor = 1.0
        self.x_axis = None
        self.y_axis = None
        self.xmin = 0
        self.xmax = 100
        self.ymin = 0
        self.ymax = 100
        self.digitize_mode = False
        self.digitized_points = []
        self.picking_axes_points = False
        self.current_axes_points = []
        self.selected_point = None
        self.selected_points = []  # Initialize selected_points

        self.annotation_view = QGraphicsView()
        self.digitize_view = QGraphicsView()
        
        self.annotation_scene = QGraphicsScene()
        self.digitize_scene = QGraphicsScene()

        self.annotation_pixmapItem = QGraphicsPixmapItem()
        self.digitize_pixmapItem = QGraphicsPixmapItem()

        self.annotation_scene.addItem(self.annotation_pixmapItem)
        self.digitize_scene.addItem(self.digitize_pixmapItem)

        self.annotation_view.setScene(self.annotation_scene)
        self.digitize_view.setScene(self.digitize_scene)

        # Table for digitized points
        self.pointsTable = QTableWidget()
        self.pointsTable.setColumnCount(2)
        self.pointsTable.setHorizontalHeaderLabels(["X", "Y"])
        self.pointsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pointsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pointsTable.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pointsTable.itemSelectionChanged.connect(self.highlightSelectedPoints)
        self.pointsTable.installEventFilter(self)

        # Enable mouse tracking
        self.annotation_view.setMouseTracking(True)
        self.digitize_view.setMouseTracking(True)
        
        self.annotation_view.viewport().installEventFilter(self)
        self.digitize_view.viewport().installEventFilter(self)
        
        # Default colors
        self.axis_color = Qt.black
        self.axis_text_color = Qt.black
        self.point_color = Qt.blue
        self.label_color = Qt.black

        # Units
        self.length_units = ["inches", "feet", "cm", "meters", "miles", "km"]
        self.area_units = ["sq. inches", "sq. feet", "sq. cm", "sq. meters", "sq. miles", "sq. km", "acres"]
        self.current_length_unit = "meters"
        self.current_area_unit = "sq. meters"

        # Initialize size attributes
        self.point_size = 10
        self.line_width = 2
        self.text_size = 14

        self.orthographic_mode = False  # Initialize orthographic mode

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image Annotater and Digitizing Tool v1.0")
        self.setGeometry(100, 100, 1000, 700)

        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.switchTab)
        
        self.tabs.addTab(self.createAnnotationTab(), "Annotate")
        self.tabs.addTab(self.createDigitizeTab(), "Digitize")
        self.setCentralWidget(self.tabs)

    def createAnnotationTab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        # Control buttons layout
        buttons_layout = QVBoxLayout()

        # Load image button
        loadButton = QPushButton("Load Image", self)
        loadButton.clicked.connect(self.loadImage)
        buttons_layout.addWidget(loadButton)

        # Calibrate scale button
        calibrateButton = QPushButton("Calibrate Scale", self)
        calibrateButton.clicked.connect(self.calibrateScale)
        buttons_layout.addWidget(calibrateButton)

        # Measure distance button
        self.measureButton = QPushButton("Measure Distance", self)
        self.measureButton.setCheckable(True)
        self.measureButton.clicked.connect(self.measureDistance)
        buttons_layout.addWidget(self.measureButton)

        # Measure area button
        self.areaButton = QPushButton("Measure Area", self)
        self.areaButton.setCheckable(True)
        self.areaButton.clicked.connect(self.measureArea)
        buttons_layout.addWidget(self.areaButton)

        # Clear annotations button
        clearButton = QPushButton("Clear Annotations", self)
        clearButton.clicked.connect(self.clearAnnotations)
        buttons_layout.addWidget(clearButton)

        # Toggle visibility button
        toggleButton = QPushButton("Toggle Annotations", self)
        toggleButton.setCheckable(True)
        toggleButton.clicked.connect(self.toggleAnnotations)
        buttons_layout.addWidget(toggleButton)

        # Delete specific annotation button
        self.deleteButton = QPushButton("Delete Annotation", self)
        self.deleteButton.setCheckable(True)
        self.deleteButton.clicked.connect(self.deleteAnnotation)
        buttons_layout.addWidget(self.deleteButton)

        # Zoom in and zoom out buttons
        zoomButtonsLayout = QHBoxLayout()
        zoomInButton = QPushButton("Zoom In", self)
        zoomInButton.clicked.connect(self.zoomIn)
        zoomButtonsLayout.addWidget(zoomInButton)

        zoomOutButton = QPushButton("Zoom Out", self)
        zoomOutButton.clicked.connect(self.zoomOut)
        zoomButtonsLayout.addWidget(zoomOutButton)
        buttons_layout.addLayout(zoomButtonsLayout)

        # Orthographic mode button
        orthoButton = QPushButton("Orthographic Mode", self)
        orthoButton.setCheckable(True)
        orthoButton.clicked.connect(lambda checked: self.toggleOrthographicMode(checked))
        buttons_layout.addWidget(orthoButton)

        # Unit selection dropdowns
        lengthUnitDropdown = QComboBox()
        lengthUnitDropdown.addItems(self.length_units)
        lengthUnitDropdown.setCurrentText(self.current_length_unit)
        lengthUnitDropdown.currentTextChanged.connect(self.updateLengthUnit)
        buttons_layout.addWidget(lengthUnitDropdown)

        areaUnitDropdown = QComboBox()
        areaUnitDropdown.addItems(self.area_units)
        areaUnitDropdown.setCurrentText(self.current_area_unit)
        areaUnitDropdown.currentTextChanged.connect(self.updateAreaUnit)
        buttons_layout.addWidget(areaUnitDropdown)

        # Scrollbars for point size, line width, and text label size
        pointSizeSlider = QSlider(Qt.Horizontal)
        pointSizeSlider.setRange(1, 20)
        pointSizeSlider.setValue(self.point_size)
        pointSizeSlider.setFixedWidth(200)
        pointSizeSlider.setTickPosition(QSlider.TicksBelow)
        pointSizeSlider.setTickInterval(1)
        pointSizeSlider.valueChanged.connect(self.updatePointSize)
        buttons_layout.addWidget(QLabel("Point Size"))
        buttons_layout.addWidget(pointSizeSlider)
        
        lineWidthSlider = QSlider(Qt.Horizontal)
        lineWidthSlider.setRange(1, 20)
        lineWidthSlider.setValue(self.line_width)
        lineWidthSlider.setFixedWidth(200)
        lineWidthSlider.setTickPosition(QSlider.TicksBelow)
        lineWidthSlider.setTickInterval(1)
        lineWidthSlider.valueChanged.connect(self.updateLineWidth)
        buttons_layout.addWidget(QLabel("Line Width"))
        buttons_layout.addWidget(lineWidthSlider)

        textSizeSlider = QSlider(Qt.Horizontal)
        textSizeSlider.setRange(1, 41)
        textSizeSlider.setValue(self.text_size)
        textSizeSlider.setFixedWidth(200)
        textSizeSlider.setTickPosition(QSlider.TicksBelow)
        textSizeSlider.setTickInterval(2)
        textSizeSlider.valueChanged.connect(self.updateTextSize)
        buttons_layout.addWidget(QLabel("Text Label Size"))
        buttons_layout.addWidget(textSizeSlider)

        # Move buttons up
        buttons_layout.addStretch(1)

        layout.addLayout(buttons_layout)
        layout.addWidget(self.annotation_view)

        tab.setLayout(layout)
        return tab

    def createDigitizeTab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        # Control buttons layout
        controls_layout = QVBoxLayout()

        # Add image button
        addButton = QPushButton("Add Image", self)
        addButton.clicked.connect(self.loadImage)
        controls_layout.addWidget(addButton)

        # Draw axes button
        self.drawAxesButton = QPushButton("Draw Axes", self)
        self.drawAxesButton.setCheckable(True)
        self.drawAxesButton.clicked.connect(self.drawAxes)
        controls_layout.addWidget(self.drawAxesButton)

        # Digitize points button
        self.digitizePointsButton = QPushButton("Digitize Points", self)
        self.digitizePointsButton.setCheckable(True)
        self.digitizePointsButton.clicked.connect(self.digitizePoints)
        controls_layout.addWidget(self.digitizePointsButton)

        # Delete digitized points button
        self.deletePointsButton = QPushButton("Delete Points", self)
        self.deletePointsButton.setCheckable(True)
        self.deletePointsButton.clicked.connect(self.deleteDigitizedPoints)
        controls_layout.addWidget(self.deletePointsButton)

        # Clear all points button
        clearPointsButton = QPushButton("Clear All Points", self)
        clearPointsButton.clicked.connect(self.clearAllPoints)
        controls_layout.addWidget(clearPointsButton)

        # Zoom in and zoom out buttons
        zoomButtonsLayout = QHBoxLayout()
        zoomInButton = QPushButton("Zoom In", self)
        zoomInButton.clicked.connect(self.zoomIn)
        zoomButtonsLayout.addWidget(zoomInButton)

        zoomOutButton = QPushButton("Zoom Out", self)
        zoomOutButton.clicked.connect(self.zoomOut)
        zoomButtonsLayout.addWidget(zoomOutButton)
        controls_layout.addLayout(zoomButtonsLayout)

        # Toggle text labels button
        toggleTextLabelsButton = QPushButton("Toggle Text Labels", self)
        toggleTextLabelsButton.setCheckable(True)
        toggleTextLabelsButton.clicked.connect(lambda checked: self.toggleTextLabels(checked))
        controls_layout.addWidget(toggleTextLabelsButton)

        # Save points to CSV button
        savePointsButton = QPushButton("Save Points", self)
        savePointsButton.clicked.connect(self.savePoints)
        controls_layout.addWidget(savePointsButton)

        # Input fields for axes values
        formLayout = QFormLayout()
        self.xminField = QLineEdit(str(self.xmin))
        self.xmaxField = QLineEdit(str(self.xmax))
        self.yminField = QLineEdit(str(self.ymin))
        self.ymaxField = QLineEdit(str(self.ymax))

        self.xminField.editingFinished.connect(self.updateAxesValues)
        self.xmaxField.editingFinished.connect(self.updateAxesValues)
        self.yminField.editingFinished.connect(self.updateAxesValues)
        self.ymaxField.editingFinished.connect(self.updateAxesValues)

        formLayout.addRow("Xmin:", self.xminField)
        formLayout.addRow("Xmax:", self.xmaxField)
        formLayout.addRow("Ymin:", self.yminField)
        formLayout.addRow("Ymax:", self.ymaxField)

        controls_layout.addLayout(formLayout)

        # Dropdowns for changing colors
        colorLayout = QFormLayout()
        self.axisColorDropdown = QComboBox()
        self.axisColorDropdown.addItems(["Black", "Red", "Green", "Blue", "Yellow"])
        self.axisColorDropdown.currentTextChanged.connect(self.updateColors)

        self.axisTextColorDropdown = QComboBox()
        self.axisTextColorDropdown.addItems(["Black", "Red", "Green", "Blue", "Yellow"])
        self.axisTextColorDropdown.currentTextChanged.connect(self.updateColors)

        self.pointColorDropdown = QComboBox()
        self.pointColorDropdown.addItems(["Blue", "Red", "Green", "Black", "Yellow"])
        self.pointColorDropdown.currentTextChanged.connect(self.updateColors)

        self.labelColorDropdown = QComboBox()
        self.labelColorDropdown.addItems(["Black", "Red", "Green", "Blue", "Yellow"])
        self.labelColorDropdown.currentTextChanged.connect(self.updateColors)

        colorLayout.addRow("Axis Color:", self.axisColorDropdown)
        colorLayout.addRow("Axis Text Color:", self.axisTextColorDropdown)
        colorLayout.addRow("Point Color:", self.pointColorDropdown)
        colorLayout.addRow("Label Color:", self.labelColorDropdown)

        controls_layout.addLayout(colorLayout)

        # Scrollbars for point size, line width, and text label size
        pointSizeSlider = QSlider(Qt.Horizontal)
        pointSizeSlider.setRange(1, 20)
        pointSizeSlider.setValue(self.point_size)
        pointSizeSlider.setFixedWidth(200)
        pointSizeSlider.setTickPosition(QSlider.TicksBelow)
        pointSizeSlider.setTickInterval(1)
        pointSizeSlider.valueChanged.connect(self.updatePointSize)
        controls_layout.addWidget(QLabel("Point Size"))
        controls_layout.addWidget(pointSizeSlider)

        lineWidthSlider = QSlider(Qt.Horizontal)
        lineWidthSlider.setRange(1, 20)
        lineWidthSlider.setValue(self.line_width)
        lineWidthSlider.setFixedWidth(200)
        lineWidthSlider.setTickPosition(QSlider.TicksBelow)
        lineWidthSlider.setTickInterval(1)
        lineWidthSlider.valueChanged.connect(self.updateLineWidth)
        controls_layout.addWidget(QLabel("Line Width"))
        controls_layout.addWidget(lineWidthSlider)

        textSizeSlider = QSlider(Qt.Horizontal)
        textSizeSlider.setRange(1, 41)
        textSizeSlider.setValue(self.text_size)
        textSizeSlider.setFixedWidth(200)
        textSizeSlider.setTickPosition(QSlider.TicksBelow)
        textSizeSlider.setTickInterval(2)
        textSizeSlider.valueChanged.connect(self.updateTextSize)
        controls_layout.addWidget(QLabel("Text Label Size"))
        controls_layout.addWidget(textSizeSlider)

        # Move buttons up
        controls_layout.addStretch(1)

        layout.addLayout(controls_layout, stretch=1)

        side_layout = QVBoxLayout()

        # Add pointsTable to the side layout
        side_layout.addWidget(self.pointsTable)

        side_widget = QWidget()
        side_widget.setLayout(side_layout)

        layout.addWidget(self.digitize_view, stretch=4)
        layout.addWidget(side_widget, stretch=1)

        tab.setLayout(layout)
        
        return tab

    def loadImage(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.image = QImage(path)
            self.clean_image = self.image.copy()  # Store a clean copy of the image
            self.annotation_pixmapItem.setPixmap(QPixmap.fromImage(self.image))
            self.digitize_pixmapItem.setPixmap(QPixmap.fromImage(self.image))
            self.measurements.clear()
            self.calibration_points.clear()
            self.measurement_points.clear()
            self.areas.clear()
            self.current_polygon.clear()
            self.digitized_points.clear()
            self.current_axes_points.clear()
            self.annotations_visible = True
            self.updateView()

    def eventFilter(self, source, event):
        if isinstance(source.parent(), QGraphicsView) and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.lastPoint = source.parent().mapToScene(event.position().toPoint())
                if self.pointInImage(self.lastPoint):
                    if self.delete_mode:
                        self.handleDeleteAnnotation(self.lastPoint)
                    elif self.delete_point_mode:
                        self.handleDeletePoint(self.lastPoint)
                    elif self.measure_area_mode:
                        self.handlePolygonPoint(self.lastPoint)
                    elif self.digitize_mode:
                        self.handleDigitizePoint(self.lastPoint)
                    elif self.picking_axes_points:
                        self.handleAxesPoint(self.lastPoint)
                    else:
                        self.handleMousePress(self.lastPoint)
        elif isinstance(source.parent(), QGraphicsView) and event.type() == QEvent.MouseMove:
            self.lastPoint = source.parent().mapToScene(event.position().toPoint())
            if self.delete_mode:
                self.highlightDeleteCandidate(self.lastPoint)
            elif self.delete_point_mode:
                self.highlightDeletePointCandidate(self.lastPoint)
            elif self.picking_axes_points:
                self.updateView()
        elif event.type() == QEvent.Wheel:
            self.handleWheelEvent(event, source.parent())
        elif isinstance(source, QTableWidget) and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
                self.handleDeletePointFromTable()
            elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                self.copyPointsToClipboard()
        return super().eventFilter(source, event)

    def pointInImage(self, point):
        return self.clean_image and (0 <= point.x() < self.image.width()) and (0 <= point.y() < self.image.height())

    def handleMousePress(self, point):
        
        if len(self.calibration_points) < 2: 
         # Calibration points
            self.calibration_points.append(point)
            self.markPoint(point)
            if len(self.calibration_points) == 2:
                self.promptScaleInput()        
                self.measureButton.setChecked(True)
        else: 
        # Measurement points
            # Project the second point if orthographic mode
            if self.orthographic_mode and len(self.measurement_points) % 2 == 1:
                p1 = self.measurement_points[-1]
                point = self.getOrthographicProjection(p1, point)

            self.measurement_points.append(point)
            self.markPoint(point)
            if len(self.measurement_points) % 2 == 0:
                self.drawMeasurementLine()

    # Handles appending polygon points and closing of polygons
    def handlePolygonPoint(self, point): 
        if self.orthographic_mode and len(self.current_polygon) > 0:
            # Project current pioint if orthographic mode on
            point = self.getOrthographicProjection(self.current_polygon[-1], point)
        
        if len(self.current_polygon) > 0 and self.calculateDistance(point, self.current_polygon[0]) < 10:
            # Close the polygon if the point is close to the first point
            self.calculateAndStoreArea(self.current_polygon)
            self.current_polygon = []
        else:
            # Append point
            self.current_polygon.append(point)
            self.markPoint(point)

    def handleDigitizePoint(self, point):
        x, y = self.convertToCoordinates(point)
        self.digitized_points.append((point, x, y))  # Store the original point as well
        self.markPoint(point)
        self.updatePointsTable()
        self.updateView()

    def handleAxesPoint(self, point):
        if self.orthographic_mode and len(self.current_axes_points) > 0:
            point = self.getOrthographicProjection(self.current_axes_points[-1], point)
        self.current_axes_points.append(point)
        self.markPoint(point)
        if len(self.current_axes_points) == 2:
            self.x_axis = self.current_axes_points[:2]
        elif len(self.current_axes_points) == 4:
            self.y_axis = self.current_axes_points[2:]
            self.picking_axes_points = False
            self.digitize_mode = True
            self.drawAxesButton.setChecked(self.picking_axes_points)
            self.digitizePointsButton.setChecked(self.digitize_mode)
        self.updateView()

    def handleDeletePoint(self, point):
        if self.delete_point_candidate:
            self.digitized_points = [dp for dp in self.digitized_points if dp[0] != self.delete_point_candidate[0]]
            self.delete_point_candidate = None
            self.updatePointsTable()
            self.updateView()

    def handleDeletePointFromTable(self):
        selected_rows = sorted(set(item.row() for item in self.pointsTable.selectedItems()))
        for row in reversed(selected_rows):
            del self.digitized_points[row]
        self.updatePointsTable()
        self.updateView()

    def highlightDeletePointCandidate(self, point):
        threshold = 5.0  # Adjust the threshold as needed
        for original_point, x, y in self.digitized_points:
            if math.hypot(point.x() - original_point.x(), point.y() - original_point.y()) <= threshold:
                self.delete_point_candidate = (original_point, x, y)
                self.updateView()
                return

        self.delete_point_candidate = None
        self.updateView()

    def highlightSelectedPoints(self):
        selected_rows = sorted(set(item.row() for item in self.pointsTable.selectedItems()))
        self.selected_points = [self.digitized_points[row] for row in selected_rows]
        self.updateView()

    def calculateAndStoreArea(self, polygon_points):
        if len(polygon_points) < 3:
            return  # Not a polygon
        polygon = QPolygonF(polygon_points)
        area = self.calculatePolygonArea(polygon)
        self.areas.append((polygon, area))
        self.updateView()

    def calculatePolygonArea(self, polygon):
        area = 0.0
        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]
            area += p1.x() * p2.y() - p2.x() * p1.y()
        area = abs(area) / 2.0
        area *= (self.scale_factor ** 2)  # Convert to real world units
        area = self.convertAreaUnits(area, from_unit="sq. meters", to_unit=self.current_area_unit)
        return area

    def promptScaleInput(self):
        distance, ok = QInputDialog.getDouble(self, "Input Scale", f"Enter the distance between the two points in {self.current_length_unit}:")
        if ok:
            pixel_distance = self.calculateDistance(self.calibration_points[0], self.calibration_points[1])
            distance_in_meters = self.convertLengthUnits(distance, from_unit=self.current_length_unit, to_unit="meters")
            self.scale_factor = distance_in_meters / pixel_distance
            self.updateMeasurements()

    def calculateDistance(self, point1, point2):
        return math.sqrt((point1.x() - point2.x())**2 + (point1.y() - point2.y())**2)

    def updateMeasurements(self):
        for i, (p1, p2, _) in enumerate(self.measurements):
            pixel_distance = self.calculateDistance(p1, p2)
            real_distance = pixel_distance * self.scale_factor
            real_distance = self.convertLengthUnits(real_distance, from_unit="meters", to_unit=self.current_length_unit)
            self.measurements[i] = (p1, p2, real_distance)

        for i, (polygon, _) in enumerate(self.areas):
            real_area = self.calculatePolygonArea(polygon)
            self.areas[i] = (polygon, real_area)

        self.updateView()

    def markPoint(self, point):
        self.updateView()

    def drawMeasurementLine(self):
        p1 = self.measurement_points[-2]
        p2 = self.measurement_points[-1]
        pixel_distance = self.calculateDistance(p1, p2)
        real_distance = pixel_distance * self.scale_factor
        real_distance = self.convertLengthUnits(real_distance, from_unit="meters", to_unit=self.current_length_unit)
        self.measurements.append((p1, p2, real_distance))
        self.updateView()

    def calibrateScale(self):
        self.delete_mode = False
        self.measure_area_mode = False
        self.calibration_points.clear()
        self.updateView()

    def measureDistance(self):
        self.delete_mode = False
        self.measure_area_mode = False
        if len(self.calibration_points) < 2:
            # Ensure we only keep calibration points if calibration is not completed
            self.measurement_points.clear()
        self.measureButton.setChecked(True)
        self.areaButton.setChecked(False)
        self.deleteButton.setChecked(False)
        self.updateView()

    def measureArea(self):
        self.delete_mode = False
        self.measure_area_mode = not self.measure_area_mode
        self.current_polygon = []
        self.areaButton.setChecked(self.measure_area_mode)
        self.measureButton.setChecked(False)
        self.deleteButton.setChecked(False)
        self.updateView()

    def clearAnnotations(self):
        self.measurement_points.clear()
        self.measurements.clear()
        self.areas.clear()
        self.digitized_points.clear()
        self.current_axes_points.clear()
        self.updatePointsTable()
        self.updateView()

    def toggleAnnotations(self):
        self.annotations_visible = not self.annotations_visible
        self.updateView()

    def deleteAnnotation(self):
        self.delete_mode = not self.delete_mode
        self.measure_area_mode = False
        self.digitize_mode = False
        self.picking_axes_points = False
        self.delete_candidate = None  # Reset the delete candidate 
        self.deleteButton.setChecked(self.delete_mode)
        self.measureButton.setChecked(False)
        self.areaButton.setChecked(False)
        self.updateView()

    def deleteDigitizedPoints(self):
        self.delete_point_mode = not self.delete_point_mode
        self.delete_point_candidate = None  # Reset the delete point candidate
        self.deletePointsButton.setChecked(self.delete_point_mode)
        self.digitizePointsButton.setChecked(False)
        self.updateView()

    def clearAllPoints(self):
        self.digitized_points.clear()
        self.delete_point_mode = False
        self.digitize_mode = True
        self.digitizePointsButton.setChecked(self.digitize_mode)
        self.deletePointsButton.setChecked(self.delete_point_mode)
        self.updatePointsTable()
        self.updateView()

    def toggleTextLabels(self, checked):
        self.text_labels_visible = not checked
        self.updateView()

    def handleDeleteAnnotation(self, point):
        if self.delete_candidate:
            if isinstance(self.delete_candidate, tuple) and len(self.delete_candidate) == 3:
                self.measurements.remove(self.delete_candidate)
                p1, p2, _ = self.delete_candidate
                if p1 in self.measurement_points:
                    self.measurement_points.remove(p1)
                if p2 in self.measurement_points:
                    self.measurement_points.remove(p2)
            elif isinstance(self.delete_candidate, QPolygonF):
                self.areas = [area for area in self.areas if area[0] != self.delete_candidate]
            self.delete_candidate = None
            self.updateView()

    def highlightDeleteCandidate(self, point):
        def pointToLineDistance(p, p1, p2):
            """Calculate the perpendicular distance from point p to the line segment p1-p2."""
            line_mag = math.sqrt((p2.x() - p1.x()) ** 2 + (p2.y() - p1.y()) ** 2)
            if line_mag < 0.000001:
                return math.hypot(p.x() - p1.x(), p.y() - p1.y())

            u1 = ((p.x() - p1.x()) * (p2.x() - p1.x()) + (p.y() - p1.y()) * (p2.y() - p1.y())) / (line_mag ** 2)
            u = max(min(u1, 1.0), 0.0)
            ix = p1.x() + u * (p2.x() - p1.x())
            iy = p1.y() + u * (p2.y() - p1.y())
            dist = math.sqrt((p.x() - ix) ** 2 + (p.y() - iy) ** 2)

            return dist

        threshold = 5.0  # Adjust the threshold as needed
        for p1, p2, distance in self.measurements:
            if pointToLineDistance(point, p1, p2) <= threshold:
                self.delete_candidate = (p1, p2, distance)
                self.updateView()
                return

        for polygon, area in self.areas:
            if polygon.containsPoint(point, Qt.OddEvenFill):
                self.delete_candidate = polygon
                self.updateView()
                return

        self.delete_candidate = None
        self.updateView()

    def updateView(self):
        if not self.clean_image:
            return
        
        temp_image = self.clean_image.copy()  # Start with a clean copy of the original image

        if self.tabs.currentIndex() == 0:
            # ANNOTAITON TAB

            painter = QPainter(temp_image)
            if self.annotations_visible:
                # Redraw calibration points
                for point in self.calibration_points:
                    painter.setPen(QPen(Qt.black, self.point_size / 4))  # Set black pen for the outline
                    painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))  # Set green brush for fill
                    painter.drawEllipse(point, self.point_size / 2, self.point_size / 2)  # Draw circles for calibration points

                if len(self.calibration_points) > 1:
                    painter.setPen(QPen(Qt.green, self.line_width, Qt.DotLine))
                    painter.drawLine(self.calibration_points[-2], self.calibration_points[-1])

                # Redraw measurement points
                painter.setPen(QPen(Qt.red, self.point_size, Qt.SolidLine))
                for point in self.measurement_points:
                    painter.drawPoint(point)

                # Redraw measurement lines
                for p1, p2, distance in self.measurements:
                    if self.delete_mode and (p1, p2, distance) == self.delete_candidate:
                        painter.setPen(QPen(Qt.yellow, self.line_width, Qt.SolidLine))  # Highlight in yellow
                    else:
                        painter.setPen(QPen(Qt.blue, self.line_width, Qt.SolidLine))
                    painter.drawLine(p1, p2)
                    mid_point = (p1 + p2) / 2
                    painter.setFont(QFont("Arial", self.text_size))
                    painter.setPen(QPen(Qt.red))
                    painter.drawText(mid_point, f"{distance:.2f} {self.current_length_unit}")

                # Redraw areas
                for polygon, area in self.areas:
                    # Draws the area and text
                    if self.delete_mode and polygon == self.delete_candidate:
                        painter.setPen(QPen(Qt.yellow, self.line_width, Qt.SolidLine))  # Highlight in yellow
                    else:
                        painter.setPen(QPen(Qt.magenta, self.line_width, Qt.SolidLine))
                    painter.setBrush(Qt.NoBrush)  # No fill
                    painter.drawPolygon(polygon)
                    mid_point = polygon.boundingRect().center()
                    painter.setFont(QFont("Arial", self.text_size))
                    painter.setPen(QPen(Qt.red))
                    painter.drawText(mid_point, f"{area:.2f} {self.current_area_unit}")

                    # Redraw points at the vertices of the polygon
                    painter.setBrush(QBrush(Qt.red))  # Set brush for the points
                    for point in polygon:
                        painter.drawEllipse(point, self.point_size / 2, self.point_size / 2)  # Draw circles for vertices

                # Draw current polygon in progress
                if self.measure_area_mode and len(self.current_polygon) > 0:
                    painter.setPen(QPen(Qt.cyan, self.line_width, Qt.SolidLine))
                    for i in range(len(self.current_polygon) - 1):
                        painter.drawLine(self.current_polygon[i], self.current_polygon[i + 1])
                        painter.drawPoint(point)

                    if self.orthographic_mode:
                        if len(self.current_polygon) > 1:
                            point = self.getOrthographicProjection(self.current_polygon[-2], self.current_polygon[-1])
                            painter.drawLine(self.current_polygon[-2], point)
                    else:
                        painter.drawLine(self.current_polygon[-1], self.lastPoint)

                    # Redraw points at the vertices of the polygon
                    painter.setBrush(QBrush(Qt.red))  # Set brush for the points
                    for point in self.current_polygon:
                        painter.drawEllipse(point, self.point_size / 2, self.point_size / 2)  # Draw circles for vertices




            self.annotation_pixmapItem.setPixmap(QPixmap.fromImage(temp_image))

        elif self.tabs.currentIndex() == 1:
            # DIGITIZATION TAB

            painter = QPainter(temp_image)
            # Draw x and y axes
            if self.x_axis:
                painter.setPen(QPen(self.axis_color, self.line_width, Qt.SolidLine))
                painter.drawLine(self.x_axis[0], self.x_axis[1])
                self.drawArrow(painter, self.x_axis[0], self.x_axis[1])
                painter.setFont(QFont("Arial", self.text_size))
                painter.setPen(QPen(self.axis_text_color))
                painter.drawText(self.x_axis[1], f"X: {self.xmin} to {self.xmax}")
            if self.y_axis:
                painter.setPen(QPen(self.axis_color, self.line_width, Qt.SolidLine))
                painter.drawLine(self.y_axis[0], self.y_axis[1])
                self.drawArrow(painter, self.y_axis[0], self.y_axis[1])
                painter.setFont(QFont("Arial", self.text_size))
                painter.setPen(QPen(self.axis_text_color))
                painter.drawText(self.y_axis[1], f"Y: {self.ymin} to {self.ymax}")

            # Draw digitized points
            for original_point, x, y in self.digitized_points:
                if (self.delete_point_mode and self.delete_point_candidate == (original_point, x, y)) or \
                   (self.selected_point == (original_point, x, y)):
                    painter.setPen(QPen(Qt.yellow, self.point_size, Qt.SolidLine))  # Highlight in yellow
                elif any(selected == (original_point, x, y) for selected in self.selected_points):
                    painter.setPen(QPen(Qt.green, self.point_size, Qt.SolidLine))  # Highlight selected points in green
                else:
                    painter.setPen(QPen(self.point_color, self.point_size, Qt.SolidLine))
                painter.drawPoint(original_point)
                if self.text_labels_visible:
                    painter.setFont(QFont("Arial", self.text_size))
                    painter.setPen(QPen(self.label_color))
                    painter.drawText(original_point, f"({x:.2f}, {y:.2f})")

            # Draw current axis line in progress
            if self.picking_axes_points and len(self.current_axes_points) == 1:
                painter.setPen(QPen(self.axis_color, self.line_width, Qt.DashLine))
                painter.drawLine(self.current_axes_points[0], self.lastPoint)
            elif self.picking_axes_points and len(self.current_axes_points) == 3:
                painter.setPen(QPen(self.axis_color, self.line_width, Qt.DashLine))
                painter.drawLine(self.current_axes_points[2], self.lastPoint)

            self.digitize_pixmapItem.setPixmap(QPixmap.fromImage(temp_image))

        painter.end()

    def handleWheelEvent(self, event, source):
        if isinstance(source, QGraphicsView):
            zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            source.scale(zoom_factor, zoom_factor)

    def zoomIn(self):
        if self.tabs.currentIndex() == 0:
            self.annotation_view.scale(1.25, 1.25)
        else:
            self.digitize_view.scale(1.25, 1.25)

    def zoomOut(self):
        if self.tabs.currentIndex() == 0:
            self.annotation_view.scale(0.8, 0.8)
        else:
            self.digitize_view.scale(0.8, 0.8)

    def zoomSliderChanged(self, value):
        scale_factor = value / 100.0
        if self.tabs.currentIndex() == 0:
            self.annotation_view.resetTransform()
            self.annotation_view.scale(scale_factor, scale_factor)
        else:
            self.digitize_view.resetTransform()
            self.digitize_view.scale(scale_factor, scale_factor)

    def drawAxes(self):
        self.digitize_mode = False
        self.delete_mode = False
        self.delete_point_mode = False
        self.picking_axes_points = True
        self.current_axes_points.clear()
        self.updateView()

    def digitizePoints(self):
        self.digitize_mode = not self.digitize_mode
        self.delete_mode = False
        self.delete_point_mode = False
        self.digitizePointsButton.setChecked(self.digitize_mode)
        self.deletePointsButton.setChecked(False)
        self.updateView()

    def convertToCoordinates(self, point):
        if self.x_axis and self.y_axis:
            x0, x1 = self.x_axis
            y0, y1 = self.y_axis

            dx = (point.x() - x0.x()) / (x1.x() - x0.x()) * (self.xmax - self.xmin) + self.xmin
            dy = (point.y() - y0.y()) / (y1.y() - y0.y()) * (self.ymax - self.ymin) + self.ymin

            return dx, dy
        return 0, 0

    def convertFromCoordinates(self, x, y):
        if self.x_axis and self.y_axis:
            px = self.x_axis[0].x() + (x - self.xmin) / (self.xmax - self.xmin) * (self.x_axis[1].x() - self.x_axis[0].x())
            py = self.y_axis[0].y() + (y - self.ymin) / (self.ymax - self.ymin) * (self.y_axis[1].y() - self.y_axis[0].y())
            return QPointF(px, py)
        return QPointF()

    def updateAxesValues(self):
        try:
            new_xmin = float(self.xminField.text())
            new_xmax = float(self.xmaxField.text())
            new_ymin = float(self.yminField.text())
            new_ymax = float(self.ymaxField.text())

            if new_xmin < new_xmax and new_ymin < new_ymax:
                self.xmin = new_xmin
                self.xmax = new_xmax
                self.ymin = new_ymin
                self.ymax = new_ymax
                self.updatePointsTable()  # Update points table with new values
                self.updateView()
            else:
                # Revert to previous values if validation fails
                self.xminField.setText(str(self.xmin))
                self.xmaxField.setText(str(self.xmax))
                self.yminField.setText(str(self.ymin))
                self.ymaxField.setText(str(self.ymax))

        except ValueError:
            pass  # Invalid input, ignore

    def updatePointsTable(self):
        self.pointsTable.setRowCount(len(self.digitized_points))
        for i, (original_point, _, _) in enumerate(self.digitized_points):
            x, y = self.convertToCoordinates(original_point)
            self.digitized_points[i] = (original_point, x, y)  # Update the stored x, y values
            self.pointsTable.setItem(i, 0, QTableWidgetItem(f"{x:.2f}"))
            self.pointsTable.setItem(i, 1, QTableWidgetItem(f"{y:.2f}"))

    def drawArrow(self, painter, p1, p2):
        arrow_size = 10
        line_angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        
        arrow_p1 = QPointF(
            p2.x() - arrow_size * math.cos(line_angle - math.pi / 6),
            p2.y() - arrow_size * math.sin(line_angle - math.pi / 6)
        )
        arrow_p2 = QPointF(
            p2.x() - arrow_size * math.cos(line_angle + math.pi / 6),
            p2.y() - arrow_size * math.sin(line_angle + math.pi / 6)
        )

        painter.drawLine(p2, arrow_p1)
        painter.drawLine(p2, arrow_p2)

    def updateColors(self):
        color_map = {
            "Black": Qt.black,
            "Red": Qt.red,
            "Green": Qt.green,
            "Blue": Qt.blue,
            "Yellow": Qt.yellow
        }
        self.axis_color = color_map[self.axisColorDropdown.currentText()]
        self.axis_text_color = color_map[self.axisTextColorDropdown.currentText()]
        self.point_color = color_map[self.pointColorDropdown.currentText()]
        self.label_color = color_map[self.labelColorDropdown.currentText()]
        self.updateView()

    def savePoints(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Points", "", "CSV Files (*.csv)")
        if path:
            df = pd.DataFrame([(x, y) for _, x, y in self.digitized_points], columns=["X", "Y"])
            df.to_csv(path, index=False)

    def copyPointsToClipboard(self):
        if not self.digitized_points:
            return

        df = pd.DataFrame([(x, y) for _, x, y in self.digitized_points], columns=["X", "Y"])
        df.to_clipboard(index=False)

    def switchTab(self, index):
        if index == 0:
            self.digitize_mode = False
            self.delete_point_mode = False
            self.picking_axes_points = False
        else:
            self.measure_area_mode = False
            self.delete_mode = False
        self.updateView()

    def updateLengthUnit(self, unit):
        self.current_length_unit = unit
        self.updateMeasurements()

    def updateAreaUnit(self, unit):
        self.current_area_unit = unit
        self.updateMeasurements()

    def convertLengthUnits(self, value, from_unit, to_unit):
        conversion_factors = {
            "meters": 1.0,
            "inches": 39.3701,
            "feet": 3.28084,
            "cm": 100.0,
            "miles": 0.000621371,
            "km": 0.001
        }
        value_in_meters = value / conversion_factors[from_unit]
        return value_in_meters * conversion_factors[to_unit]

    def convertAreaUnits(self, value, from_unit, to_unit):
        conversion_factors = {
            "sq. meters": 1.0,
            "sq. inches": 1550.0031,
            "sq. feet": 10.7639,
            "sq. cm": 10000.0,
            "sq. miles": 3.861e-7,
            "sq. km": 1e-6,
            "acres": 0.000247105
        }
        value_in_sq_meters = value / conversion_factors[from_unit]
        return value_in_sq_meters * conversion_factors[to_unit]

    def updatePointSize(self, value):
        self.point_size = value
        self.updateView()

    def updateLineWidth(self, value):
        self.line_width = value
        self.updateView()

    def updateTextSize(self, value):
        self.text_size = value
        self.updateView()

    def toggleOrthographicMode(self, checked):
        self.orthographic_mode = checked
        self.updateView()

    def getOrthographicProjection(self, last_point, current_point):
        dx = current_point.x() - last_point.x()
        dy = current_point.y() - last_point.y()
        if abs(dx) > abs(dy):
            return QPointF(current_point.x(), last_point.y())
        else:
            return QPointF(last_point.x(), current_point.y())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    sys.exit(app.exec())
