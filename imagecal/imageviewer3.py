import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                               QGraphicsPixmapItem, QVBoxLayout, QWidget, QPushButton,
                               QHBoxLayout, QFileDialog, QInputDialog)
from PySide6.QtGui import QPixmap, QPainter, QPen, QImage, QFont, QPolygonF
from PySide6.QtCore import Qt, QEvent, QPointF, QRectF
import math

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scale_factor = None
        self.calibration_points = []  # Stores calibration points
        self.measurement_points = []  # Stores measurement points
        self.measurements = []  # Stores lines and distances
        self.areas = []  # Stores polygons and their areas
        self.current_polygon = []  # Stores points for the current polygon
        self.delete_mode = False
        self.measure_area_mode = False
        self.annotations_visible = True
        self.pen = QPen(Qt.red, 10, Qt.SolidLine)  # Initialize the pen attribute here
        self.clean_image = None  # This will hold the clean copy of the image
        self.delete_candidate = None  # To track which line is a candidate for deletion

    def initUI(self):
        self.setWindowTitle("Image Drawer")
        self.setGeometry(100, 100, 1000, 700)

        # Layout and central widget
        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        # Graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.pixmapItem = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmapItem)
        layout.addWidget(self.view)

        # Control buttons layout
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        # Load image button
        loadButton = QPushButton("Load Image", self)
        loadButton.clicked.connect(self.loadImage)
        buttons_layout.addWidget(loadButton)

        # Calibrate scale button
        calibrateButton = QPushButton("Calibrate Scale", self)
        calibrateButton.clicked.connect(self.calibrateScale)
        buttons_layout.addWidget(calibrateButton)

        # Measure distance button
        measureButton = QPushButton("Measure Distance", self)
        measureButton.clicked.connect(self.measureDistance)
        buttons_layout.addWidget(measureButton)

        # Measure area button
        areaButton = QPushButton("Measure Area", self)
        areaButton.clicked.connect(self.measureArea)
        buttons_layout.addWidget(areaButton)

        # Clear annotations button
        clearButton = QPushButton("Clear Annotations", self)
        clearButton.clicked.connect(self.clearAnnotations)
        buttons_layout.addWidget(clearButton)

        # Toggle visibility button
        toggleButton = QPushButton("Toggle Annotations", self)
        toggleButton.clicked.connect(self.toggleAnnotations)
        buttons_layout.addWidget(toggleButton)

        # Delete specific annotation button
        deleteButton = QPushButton("Delete Annotation", self)
        deleteButton.clicked.connect(self.deleteAnnotation)
        buttons_layout.addWidget(deleteButton)

        # Enable mouse tracking
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def loadImage(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.image = QImage(path)
            self.clean_image = self.image.copy()  # Store a clean copy of the image
            self.pixmapItem.setPixmap(QPixmap.fromImage(self.image))
            self.measurements.clear()
            self.calibration_points.clear()
            self.measurement_points.clear()
            self.areas.clear()
            self.current_polygon.clear()
            self.annotations_visible = True
            self.updateView()

    def eventFilter(self, source, event):
        if source is self.view.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.lastPoint = self.view.mapToScene(event.position().toPoint())
                if self.pointInImage(self.lastPoint):
                    if self.delete_mode:
                        self.handleDeleteAnnotation(self.lastPoint)
                    elif self.measure_area_mode:
                        self.handlePolygonPoint(self.lastPoint)
                    else:
                        self.handleMousePress(self.lastPoint)
        elif source is self.view.viewport() and event.type() == QEvent.MouseMove and self.delete_mode:
            self.lastPoint = self.view.mapToScene(event.position().toPoint())
            self.highlightDeleteCandidate(self.lastPoint)
        return super().eventFilter(source, event)

    def pointInImage(self, point):
        return (0 <= point.x() < self.image.width()) and (0 <= point.y() < self.image.height())

    def handleMousePress(self, point):
        if len(self.calibration_points) < 2:  # Calibration points
            self.calibration_points.append(point)
            self.markPoint(point)
            if len(self.calibration_points) == 2:
                self.promptScaleInput()
        else:  # Measurement points
            self.measurement_points.append(point)
            self.markPoint(point)
            if len(self.measurement_points) % 2 == 0:
                self.drawMeasurementLine()

    def handlePolygonPoint(self, point):
        if len(self.current_polygon) > 0 and self.calculateDistance(point, self.current_polygon[0]) < 10:
            # Close the polygon if the point is close to the first point
            self.calculateAndStoreArea(self.current_polygon)
            self.current_polygon = []
        else:
            self.current_polygon.append(point)
            self.markPoint(point)

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
        return area

    def promptScaleInput(self):
        distance, ok = QInputDialog.getDouble(self, "Input Scale", "Enter the distance between the two points:")
        if ok:
            pixel_distance = self.calculateDistance(self.calibration_points[0], self.calibration_points[1])
            self.scale_factor = distance / pixel_distance
            self.updateMeasurements()

    def calculateDistance(self, point1, point2):
        return math.sqrt((point1.x() - point2.x())**2 + (point1.y() - point2.y())**2)

    def updateMeasurements(self):
        for i, (p1, p2, _) in enumerate(self.measurements):
            pixel_distance = self.calculateDistance(p1, p2)
            real_distance = pixel_distance * self.scale_factor
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
        self.updateView()

    def measureArea(self):
        self.delete_mode = False
        self.measure_area_mode = not self.measure_area_mode
        self.current_polygon = []
        self.updateView()

    def clearAnnotations(self):
        self.measurement_points.clear()
        self.measurements.clear()
        self.areas.clear()
        self.updateView()

    def toggleAnnotations(self):
        self.annotations_visible = not self.annotations_visible
        self.updateView()

    def deleteAnnotation(self):
        self.delete_mode = not self.delete_mode
        self.measure_area_mode = False
        self.delete_candidate = None  # Reset the delete candidate 
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
        temp_image = self.clean_image.copy()  # Start with a clean copy of the original image
        painter = QPainter(temp_image)

        if self.annotations_visible:
            # Redraw calibration points
            painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
            for point in self.calibration_points:
                painter.drawEllipse(point, 5, 5)  # Draw circles for calibration points

            # Redraw measurement points
            painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
            for point in self.measurement_points:
                painter.drawPoint(point)

            # Redraw measurement lines
            for p1, p2, distance in self.measurements:
                if self.delete_mode and (p1, p2, distance) == self.delete_candidate:
                    painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))  # Highlight in yellow
                else:
                    painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawLine(p1, p2)
                mid_point = (p1 + p2) / 2
                painter.setFont(QFont("Arial", 14))
                painter.setPen(QPen(Qt.red))
                painter.drawText(mid_point, f"{distance:.2f}")

            # Redraw areas
            for polygon, area in self.areas:
                if self.delete_mode and polygon == self.delete_candidate:
                    painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))  # Highlight in yellow
                else:
                    painter.setPen(QPen(Qt.magenta, 2, Qt.SolidLine))
                painter.drawPolygon(polygon)
                mid_point = polygon.boundingRect().center()
                painter.setFont(QFont("Arial", 14))
                painter.setPen(QPen(Qt.red))
                painter.drawText(mid_point, f"{area:.2f}")

            # Draw current polygon in progress
            if self.measure_area_mode and len(self.current_polygon) > 0:
                painter.setPen(QPen(Qt.cyan, 2, Qt.SolidLine))
                for i in range(len(self.current_polygon) - 1):
                    painter.drawLine(self.current_polygon[i], self.current_polygon[i + 1])
                painter.drawLine(self.current_polygon[-1], self.lastPoint)

        painter.end()
        self.image = temp_image
        self.pixmapItem.setPixmap(QPixmap.fromImage(self.image))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    sys.exit(app.exec())
