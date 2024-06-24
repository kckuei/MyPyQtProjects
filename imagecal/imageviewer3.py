import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                               QGraphicsPixmapItem, QVBoxLayout, QWidget, QPushButton,
                               QHBoxLayout, QFileDialog, QInputDialog)
from PySide6.QtGui import QPixmap, QPainter, QPen, QImage, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QEvent
import math

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scale_factor = None
        self.calibration_points = []
        self.measurement_points = []
        self.measurements = []
        self.delete_mode = False
        self.annotations_visible = True
        self.pen = QPen(Qt.red, 10, Qt.SolidLine)  # Initialize the pen attribute here
        self.clean_image = None  # This will hold the clean copy of the image

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
            self.annotations_visible = True
            self.updateView()

    def eventFilter(self, source, event):
        if source is self.view.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.lastPoint = self.view.mapToScene(event.position().toPoint())
                if self.delete_mode:
                    self.handleDeleteAnnotation(self.lastPoint)
                else:
                    self.handleMousePress(self.lastPoint)
        return super().eventFilter(source, event)

    def handleMousePress(self, point):
        if len(self.calibration_points) < 2:
            self.calibration_points.append(point)
            self.markPoint(point)
            if len(self.calibration_points) == 2:
                self.promptScaleInput()
        elif len(self.measurement_points) < 2:
            self.measurement_points.append(point)
            self.markPoint(point)
            if len(self.measurement_points) == 2:
                self.drawMeasurementLine()

    def promptScaleInput(self):
        distance, ok = QInputDialog.getDouble(self, "Input Scale", "Enter the distance between the two points:")
        if ok:
            pixel_distance = self.calculateDistance(self.calibration_points[0], 
                                                    self.calibration_points[1])
            self.scale_factor = distance / pixel_distance

    def calculateDistance(self, point1, point2):
        return math.sqrt((point1.x() - point2.x())**2 + (point1.y() - point2.y())**2)

    def markPoint(self, point):
        painter = QPainter(self.image)
        painter.setPen(self.pen)
        painter.drawPoint(point)
        painter.end()
        self.pixmapItem.setPixmap(QPixmap.fromImage(self.image))

    def drawMeasurementLine(self):
        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        painter.drawLine(self.measurement_points[0], self.measurement_points[1])

        pixel_distance = self.calculateDistance(self.measurement_points[0], 
                                                self.measurement_points[1])
        real_distance = pixel_distance * self.scale_factor
        mid_point = (self.measurement_points[0] + self.measurement_points[1]) / 2
        painter.setFont(QFont("Arial", 14))
        painter.setPen(QPen(Qt.red))
        painter.drawText(mid_point, f"{real_distance:.2f}")

        painter.end()
        self.measurements.append((self.measurement_points[0], 
                                  self.measurement_points[1], 
                                  real_distance))
        self.pixmapItem.setPixmap(QPixmap.fromImage(self.image))
        self.measurement_points.clear()

    def calibrateScale(self):
        self.calibration_points.clear()
        self.measurement_points.clear()

    def measureDistance(self):
        self.measurement_points.clear()

    def clearAnnotations(self):
        self.measurements.clear()
        self.updateView()

    def toggleAnnotations(self):
        self.annotations_visible = not self.annotations_visible
        self.updateView()

    def deleteAnnotation(self):
        self.delete_mode = not self.delete_mode

    # def handleDeleteAnnotation(self, point):
    #     print("here")
    #     for i, (p1, p2, distance) in enumerate(self.measurements):
    #         print(i, p1, p2)
    #         path = QPainterPath()
    #         path.moveTo(p1)
    #         path.lineTo(p2)
    #         if path.contains(point):
    #             del self.measurements[i]
    #             self.updateView()
    #             break
    def handleDeleteAnnotation(self, point):
        def pointToLineDistance(p, p1, p2):
            """Calculate the perpendicular distance from point p to the line segment p1-p2."""
            if p1 == p2:
                return math.hypot(p.x() - p1.x(), p.y() - p1.y())
            else:
                n = abs((p2.y() - p1.y()) * p.x() - (p2.x() - p1.x()) * p.y() + p2.x() * p1.y() - p2.y() * p1.x())
                d = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
                return n / d

        threshold = 5.0  # Adjust the threshold as needed
        for i, (p1, p2, distance) in enumerate(self.measurements):
            if pointToLineDistance(point, p1, p2) <= threshold:
                del self.measurements[i]
                self.updateView()
                break



    def updateView(self):
        temp_image = self.clean_image.copy()  # Start with a clean copy of the original image
        painter = QPainter(temp_image)
        if self.annotations_visible:
            for p1, p2, distance in self.measurements:
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawLine(p1, p2)
                mid_point = (p1 + p2) / 2
                painter.setFont(QFont("Arial", 14))
                painter.setPen(QPen(Qt.red))
                painter.drawText(mid_point, f"{distance:.2f}")
        painter.end()
        self.image = temp_image
        self.pixmapItem.setPixmap(QPixmap.fromImage(self.image))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    sys.exit(app.exec())
