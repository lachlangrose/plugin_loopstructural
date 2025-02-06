from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsMapLayerProxyModel

from PyQt5.QtCore import QSize

from qgis.PyQt.QtWidgets import (
    QWidget,
    QListWidgetItem,
    QTableWidgetItem,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QFileDialog,
    QPushButton,
    QColorDialog,
)
from qgis.core import QgsProject, QgsEllipse, QgsPoint, QgsVectorLayer, QgsFeature
import random
import os
from ...main import QgsProcessInputData
from ...main.geometry.calculateLineAzimuth import calculateAverageAzimuth
from LoopStructural.utils import random_hex_colour
from qgis.core import QgsField
from PyQt5.QtCore import QVariant

# from LoopStructural.visualisation import Loop3DView
# from loopstructural.gui.modelling.stratigraphic_column import StratigraphicColumnWidget
class ModellingWidget(QWidget):
    def __init__(self, parent: QWidget = None, mapCanvas=None, logger=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), "modelling_widget.ui"), self)
        self.mapCanvas = mapCanvas
        self.rotationDoubleSpinBox.setValue(mapCanvas.rotation())
        self._set_layer_filters()
        # self.unitNameField.setLayer(self.basalContactsLayer.currentLayer())
        self.logger = logger
        self._basalContacts = None
        self._units = None
        self._faults = {}
        self._connectSignals()
        self.view = None
        self.model = None
        self.outputPath = ""

    def _set_layer_filters(self):
        # Set filters for the layer selection comboboxes
        # basal contacts can be line or points
        self.basalContactsLayer.setFilters(
            QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.PointLayer
        )
        self.basalContactsLayer.setAllowEmptyLayer(True)
        # Structural data can only be points
        self.structuralDataLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.basalContactsLayer.setAllowEmptyLayer(True)
        # fault traces can be lines or points
        self.faultTraceLayer.setFilters(
            QgsMapLayerProxyModel.LineLayer | QgsMapLayerProxyModel.PointLayer
        )
        self.faultTraceLayer.setAllowEmptyLayer(True)
        # dtm can only be a raster
        self.DtmLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.DtmLayer.setAllowEmptyLayer(True)

        # evaluate on model layer
        self.evaluateModelOnLayerSelector.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.evaluateModelOnLayerSelector.setAllowEmptyLayer(True)
        # evaluate on feature layer
        self.evaluateFeatureLayerSelector.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.evaluateFeatureLayerSelector.setAllowEmptyLayer(True)

    def _connectSignals(self):
        self.basalContactsLayer.layerChanged.connect(self.onBasalContactsChanged)
        self.structuralDataLayer.layerChanged.connect(self.onStructuralDataLayerChanged)
        self.unitNameField.fieldChanged.connect(self.onUnitFieldChanged)
        self.faultTraceLayer.layerChanged.connect(self.onFaultTraceLayerChanged)
        self.faultNameField.fieldChanged.connect(self.onFaultFieldChanged)
        self.faultDipField.fieldChanged.connect(self.onFaultFieldChanged)
        self.faultDisplacementField.fieldChanged.connect(self.onFaultFieldChanged)
        self.orientationType.currentIndexChanged.connect(self.onOrientationTypeChanged)
        self.orientationField.fieldChanged.connect(self.onOrientationFieldChanged)
        self.initModel.clicked.connect(self.onInitialiseModel)
        self.rotationDoubleSpinBox.valueChanged.connect(self.onRotationChanged)
        self.runModelButton.clicked.connect(self.onRunModel)
        self.pathButton.clicked.connect(self.onClickPath)
        self.saveButton.clicked.connect(self.onSaveModel)
        self.path.textChanged.connect(self.onPathTextChanged)
        self.faultSelection.currentIndexChanged.connect(self.onSelectedFaultChanged)
        self.faultDipValue.valueChanged.connect(
            lambda value: self.updateFaultProperty('dip', value)
        )
        self.faultDisplacementValue.valueChanged.connect(
            lambda value: self.updateFaultProperty('displacement', value)
        )
        self.faultActiveCheckBox.stateChanged.connect(
            lambda value: self.updateFaultProperty('active', value)
        )
        self.faultMajorAxisLength.valueChanged.connect(
            lambda value: self.updateFaultProperty('major_axis', value)
        )
        self.faultIntermediateAxisLength.valueChanged.connect(
            lambda value: self.updateFaultProperty('intermediate_axis', value)
        )
        self.faultMinorAxisLength.valueChanged.connect(
            lambda value: self.updateFaultProperty('minor_axis', value)
        )
        # self.faultCentreX.valueChanged.connect(lambda value: self.updateFaultProperty('centre', value))
        # self.faultCentreY.valueChanged.connect(lambda value: self.updateFaultProperty('centre', value))
        # self.faultCentreZ.valueChanged.connect(lambda value: self.updateFaultProperty('centre', value))
        self.addFaultElipseToMap.clicked.connect(self.drawFaultElipse)
        self.addModelContactsToProject.clicked.connect(self.onAddModelContactsToProject)
        self.addFaultDisplacementsToProject.clicked.connect(self.onAddFaultDisplacmentsToProject)
        self.evaluateModelOnLayer.clicked.connect(self.onEvaluateModelOnLayer)
        self.evaluateFeatureOnLayer.clicked.connect(self.onEvaluateFeatureOnLayer)
        self.addMappedLithologiesToProject.clicked.connect(self.onAddModelledLithologiesToProject)
        self.addFaultTracesToProject.clicked.connect(self.onAddFaultTracesToProject)
        self.addScalarFieldToProject.clicked.connect(self.onAddScalarFieldToProject)
        self.saveThicknessOrderButton.clicked.connect(self.saveThicknessOrder)

    def onInitialiseModel(self):

        columnmap = {
            'unitname': self.unitNameField.currentField(),
            'faultname': self.faultNameField.currentField(),
            'dip': self.dipField.currentField(),
            'orientation': self.orientationField.currentField(),
            'structure_unitname': self.structuralDataUnitName.currentField(),
        }
        processor = QgsProcessInputData(
            basal_contacts=self.basalContactsLayer.currentLayer(),
            stratigraphic_column=self._units,
            fault_trace=self.faultTraceLayer.currentLayer(),
            fault_properties=self._faults,
            structural_data=self.structuralDataLayer.currentLayer(),
            dtm=self.DtmLayer.currentLayer(),
            columnmap=columnmap,
            roi=self.roiLayer.currentLayer(),
            top=self.heightSpinBox.value(),
            bottom=self.depthSpinBox.value(),
            dip_direction=self.orientationType.currentIndex() == 1,
            rotation=self.rotationDoubleSpinBox.value(),
        )
        self.processor = processor
        self.model = processor.get_model()
        self.logger(message="Model initialised", log_level=1, push=True)

        # for feature in self.model.features:
        #     item = QListWidgetItem()
        #     item.setText(feature.name)
        #     item.setBackground(
        #         QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        #     )
        #     self.modelList.addItem(item)

    def onOrientationTypeChanged(self, index):
        if index == 0:
            self.orientationLabel.setText("Strike")
        else:
            self.orientationLabel.setText("Dip Direction")

    def onRotationChanged(self, rotation):
        self.mapCanvas.setRotation(rotation)

    def onOrientationFieldChanged(self, field):
        pass

    def onStructuralDataLayerChanged(self, layer):
        self.orientationField.setLayer(layer)
        self.dipField.setLayer(layer)
        self.structuralDataUnitName.setLayer(layer)
        # self.dipField.setValidator(QDoubleValidator(0.0, 360.0, 2))
        # self.orientationField.setValidator(QDoubleValidator(0.0, 360.0, 2))

    def onRunModel(self):
        try:

            self.model.update(progressbar=False)
            self._model_updated()
            self.logger(message="Model run", log_level=1, push=True)

        except Exception as e:
            self.logger(
                message=str(e),
                log_level=2,
                push=True,
            )

    def _model_updated(self):
        self.addScalarFieldComboBox.clear()
        self.evaluateFeatureFeatureSelector.clear()
        for feature in self.model.features:
            self.addScalarFieldComboBox.addItem(feature.name)
            self.evaluateFeatureFeatureSelector.addItem(feature.name)
        self.addScalarFieldComboBox.setCurrentIndex(0)
        self.evaluateFeatureFeatureSelector.setCurrentIndex(0)

    def onAddModelContactsToProject(self):
        pass

    def onAddFaultDisplacmentsToProject(self):
        pass

    def onEvaluateModelOnLayer(self):
        pass

    def onEvaluateFeatureOnLayer(self):
        pass

    def onAddModelledLithologiesToProject(self):
        pass

    def onAddFaultTracesToProject(self):
        pass

    def onAddScalarFieldToProject(self):
        pass

    def onBasalContactsChanged(self, layer):
        self.unitNameField.setLayer(layer)

    def onFaultTraceLayerChanged(self, layer):
        self.faultNameField.setLayer(layer)
        self.faultDipField.setLayer(layer)
        self.faultDisplacementField.setLayer(layer)
        self._faults = {}  # reset faults
        self.onSelectedFaultChanged(-1)
        self.initFaultSelector()

    def onUnitFieldChanged(self, field):
        unique_values = set()
        attributes = {}
        layer = self.unitNameField.layer()
        if layer:
            fields = {}
            fields['unitname'] = layer.fields().indexFromName(field)
            if '_ls_th' in [field.name() for field in layer.fields()]:
                fields['thickness'] = layer.fields().indexFromName('_ls_th')
            if '_ls_or' in [field.name() for field in layer.fields()]:
                fields['order'] = layer.fields().indexFromName('_ls_or')
            if '_ls_col' in [field.name() for field in layer.fields()]:
                fields['colour'] = layer.fields().indexFromName('_ls_col')
            field_index = layer.fields().indexFromName(field)

            for feature in layer.getFeatures():
                unique_values.add(str(feature[field_index]))
                attributes[str(feature[field_index])] = {}
                for k in fields:
                    if feature[fields[k]] != None:
                        attributes[str(feature[field_index])][k] = feature[fields[k]]
        colours = random_hex_colour(n=len(unique_values))
        self._units = dict(
            zip(
                list(unique_values),
                [
                    {
                        'thickness': attributes[u]['thickness']
                        if 'thickness' in attributes[u]
                        else 10.0,
                        'order': int(attributes[u]['order']) if 'order' in attributes[u] else i,
                        'name': u,
                        'colour': str(attributes[u]['colour']) if 'colour' in attributes[u] else colours[i],
                    }
                    for i, u in enumerate(unique_values)
                ],
            )
        )
        self._initialiseStratigraphicColumn()

    def initFaultSelector(self):
        self.faultSelection.clear()
        self.resetFaultField()
        if self._faults:
            faults = list(self._faults.keys())
            self.faultSelection.addItems(faults)

    def onFaultFieldChanged(self, field):
        name_field = self.faultNameField.currentField()
        dip_field = self.faultDipField.currentField()
        displacement_field = self.faultDisplacementField.currentField()
        layer = self.faultNameField.layer()
        if name_field and layer:
            self._faults = {}
            for feature in layer.getFeatures():
                self._faults[str(feature[name_field])] = {
                    'dip': feature.attributeMap().get(dip_field, 0),
                    'displacement': feature.attributeMap().get(displacement_field, 0),
                    'centre': feature.geometry().centroid().asPoint(),
                    'major_axis': feature.geometry().length(),
                    'intermediate_axis': feature.geometry().length(),
                    'minor_axis': feature.geometry().length() / 3,
                    'active': True,
                    "azimuth": calculateAverageAzimuth(feature.geometry()),
                    "crs": layer.crs().authid(),
                }
        self.initFaultSelector()

    def onSelectedFaultChanged(self, index):
        if index >= 0:
            fault = self.faultSelection.currentText()
            self.faultDipValue.setValue(self._faults[fault]['dip'])
            self.faultDisplacementValue.setValue(self._faults[fault]['displacement'])
            self.faultActiveCheckBox.setChecked(self._faults[fault]['active'])
            self.faultMajorAxisLength.setValue(self._faults[fault]['major_axis'])
            self.faultIntermediateAxisLength.setValue(self._faults[fault]['intermediate_axis'])
            self.faultMinorAxisLength.setValue(self._faults[fault]['minor_axis'])
            self.faultCentreX.setValue(self._faults[fault]['centre'].x())
            self.faultCentreY.setValue(self._faults[fault]['centre'].y())
            # self.faultCentreZ.setValue(self._faults[fault]['centre'].z())
            self._onActiveFaultChanged(self._faults[fault]['active'])

    def resetFaultField(self):
        self.faultDipValue.setValue(0)
        self.faultDisplacementValue.setValue(0)
        self.faultActiveCheckBox.setChecked(0)
        self.faultMajorAxisLength.setValue(0)
        self.faultIntermediateAxisLength.setValue(0)
        self.faultMinorAxisLength.setValue(0)
        self.faultCentreX.setValue(0)
        self.faultCentreY.setValue(0)
        # self.faultCentreZ.setValue(self._faults[fault]['centre'].z())
        self._onActiveFaultChanged(False)

    def _onActiveFaultChanged(self, value):
        self.faultDipValue.setEnabled(value)
        self.faultDisplacementValue.setEnabled(value)
        self.faultMajorAxisLength.setEnabled(value)
        self.faultIntermediateAxisLength.setEnabled(value)
        self.faultMinorAxisLength.setEnabled(value)
        self.faultCentreX.setEnabled(value)
        self.faultCentreY.setEnabled(value)
        # self.faultCentreZ.setEnabled(value)

    def updateFaultProperty(self, prop, value):
        fault = self.faultSelection.currentText()
        if fault not in self._faults:
            return
        self._faults[fault][prop] = value
        if prop == 'active':
            self._onActiveFaultChanged(value)

    def drawFaultElipse(self):
        fault = self.faultSelection.currentText()
        if fault:
            centre = self._faults[fault]['centre']
            major_axis = self._faults[fault]['major_axis']
            intermediate_axis = self._faults[fault]['intermediate_axis']
            minor_axis = self._faults[fault]['minor_axis']
            azimuth = self._faults[fault].get('azimuth', 0)
            crs = self._faults[fault].get('crs', 'EPSG:4326')
            # Create an ellipsoid centered at the fault center
            ellipsoid = QgsEllipse(
                QgsPoint(centre.x(), centre.y()), major_axis / 2, minor_axis / 2, azimuth
            )

            # Add the ellipsoid to the map canvas
            ellipsoid_layer = QgsVectorLayer(f"Polygon?crs={crs}", f"{fault}:  Ellipsoid", "memory")
            ellipsoid_layer_provider = ellipsoid_layer.dataProvider()
            ellipsoid_feature = QgsFeature()
            ellipsoid_feature.setGeometry(ellipsoid.toPolygon())
            ellipsoid_layer_provider.addFeatures([ellipsoid_feature])

            QgsProject.instance().addMapLayer(ellipsoid_layer)

    def _getSortedStratigraphicColumn(self):

        return sorted(self._units.items(), key=lambda x: x[1]['order'])

    def _initialiseStratigraphicColumn(self):
        while self.stratigraphicColumnContainer.count():
            child = self.stratigraphicColumnContainer.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # self.stratigraphicColumnContainer.setColumnCount(5)
        # self.stratigraphicColumnContainer.setRowCount(len(self._units))
        # self.stratigraphicColumnContainer.setHorizontalHeaderLabels(
        #     ["Unit", "Thickness", "Order","Up","Down"]
        # )
        def create_lambda(i, direction):
            return lambda: self.onOrderChanged(i, i + direction)

        def create_color_picker(unit):
            def pick_color():
                color = QColorDialog.getColor()
                if color.isValid():
                    self._units[unit]['colour'] = color.name()
                    self._initialiseStratigraphicColumn()

            return pick_color

        for i, (unit, value) in enumerate(self._getSortedStratigraphicColumn()):
            label = QLabel(unit)
            spin_box = QDoubleSpinBox(maximum=10000, minimum=0)
            spin_box.setValue(value['thickness'])
            order = QLabel()
            order.setText(str(value['order']))
            up = QPushButton("↑")
            down = QPushButton("↓")
            color_picker = QPushButton("Pick Colour")
            # Set background color for the row
            background_color = value.get('colour', "#ffffff")
            label.setStyleSheet(f"background-color: {background_color};")
            spin_box.setStyleSheet(f"background-color: {background_color};")
            order.setStyleSheet(f"background-color: {background_color};")
            up.setStyleSheet(f"background-color: {background_color};")
            down.setStyleSheet(f"background-color: {background_color};")
            color_picker.setStyleSheet(f"background-color: {background_color};")
            self.stratigraphicColumnContainer.addWidget(label, i, 0)
            self.stratigraphicColumnContainer.addWidget(spin_box, i, 1)
            self.stratigraphicColumnContainer.addWidget(order, i, 2)
            self.stratigraphicColumnContainer.addWidget(up, i, 3)
            self.stratigraphicColumnContainer.addWidget(down, i, 4)
            self.stratigraphicColumnContainer.addWidget(color_picker, i, 5)
            up.clicked.connect(create_lambda(i, -1))
            down.clicked.connect(create_lambda(i, 1))
            color_picker.clicked.connect(create_color_picker(unit))
            spin_box.valueChanged.connect(lambda value, unit=unit: self.onThicknessChanged(unit, value))
    def onOrderChanged(self, old_index, new_index):
        if new_index < 0 or new_index >= len(self._units):
            return
        units = dict(self._units)  # update a copy
        for unit, value in self._units.items():
            if value['order'] == old_index:
                units[unit]['order'] = new_index
            elif value['order'] == new_index:
                units[unit]['order'] = old_index
        self._units = units  # set to copy
        self._initialiseStratigraphicColumn()
    def onThicknessChanged(self, unit, value):
        self._units[unit]['thickness'] = value
    

    def onSaveModel(self):
        try:

            fileFormat = self.fileFormatCombo.currentText()
            path = self.path.text()  #
            name = self.modelNameLineEdit.text()
            if fileFormat == 'python':
                fileFormat = 'pkl'
                self.model.to_file(os.path.join(path, name + "." + fileFormat))
                self.processor.to_file(os.path.join(path, name + "_processor." + fileFormat))
                return

            filename = os.path.join(path, name + "." + fileFormat)

            self.model.save(
                filename=os.path.join(path, name + "." + fileFormat),
                block_model=self.blockModelCheckBox.isChecked(),
                stratigraphic_surfaces=self.stratigraphicSurfacesCheckBox.isChecked(),
                fault_surfaces=self.faultSurfacesCheckBox.isChecked(),
                stratigraphic_data=self.stratigraphicDataCheckBox.isChecked(),
                fault_data=self.faultDataCheckBox.isChecked(),
            )
            self.logger(message=f"Model saved to {path}", log_level=1, push=True)
        except Exception as e:
            self.logger(
                message=str(e),
                log_level=2,
                push=True,
            )

    def saveThicknessOrder(self):
        layer = self.basalContactsLayer.currentLayer()
        layer.startEditing()
        field_names = ["_ls_th", "_ls_or","_ls_col"]
        field_types = [QVariant.Double, QVariant.Int, QVariant.String]
        for field_name, field_type in zip(field_names, field_types):

            if field_name not in [field.name() for field in layer.fields()]:
                layer.dataProvider().addAttributes([QgsField(field_name, field_type)])
                layer.updateFields()
        for unit, value in self._units.items():
            for feature in layer.getFeatures():
                if feature.attributeMap().get(self.unitNameField.currentField()) == unit:
                    feature[field_names[0]] = value['thickness']
                    feature[field_names[1]] = value['order']
                    feature[field_names[2]] = value['colour']
                    layer.updateFeature(feature)
        layer.commitChanges()
        layer.updateFields()
        self.logger(message=f"Thickness, colour and order saved to {layer.name()}", log_level=1, push=True)

    def onPathTextChanged(self, text):
        self.outputPath = text

    def onClickPath(self):
        self.outputPath = QFileDialog.getExistingDirectory(None, "Select output path for model")

        self.path.setText(self.outputPath)
        # if self.path:
        #     if os.path.exists(self.gridDirectory):
        #         self.output_directory = os.path.split(
        #             self.dlg.lineEdit_gridOutputDir.text()
        #         )[-1]
