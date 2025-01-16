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
)

import random
import os
from ...main import QgsProcessInputData

# from LoopStructural.visualisation import Loop3DView
# from loopstructural.gui.modelling.stratigraphic_column import StratigraphicColumnWidget
class ModellingWidget(QWidget):
    def __init__(self, parent: QWidget = None, mapCanvas=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), "modelling_widget.ui"), self)
        self.mapCanvas = mapCanvas
        self.rotationDoubleSpinBox.setValue(mapCanvas.rotation())
        self.basalContactsLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.unitNameField.setLayer(self.basalContactsLayer.currentLayer())
        self.faultTraceLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.faultTraceLayer.setAllowEmptyLayer(True)
        self.DtmLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.DtmLayer.setAllowEmptyLayer(True)
        self.structuralDataLayer.setFilters(QgsMapLayerProxyModel.PointLayer)

        self._basalContacts = None
        self._units = None
        self._faults = {}
        self._connectSignals()
        self.view = None
        self.model = None
        self.outputPath = ""

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

    def onInitialiseModel(self):
        columnmap = {
            'unitname': self.unitNameField.currentField(),
            'faultname': self.faultNameField.currentField(),
            'dip': self.dipField.currentField(),
            'orientation': self.orientationField.currentField(),
            'structure_unitname': self.structuralDataUnitName.currentField(),
        }
        try:
            processor = QgsProcessInputData(
                basal_contacts=self.basalContactsLayer.currentLayer(),
                stratigraphic_column=self._units,
                faults=self.faultTraceLayer.currentLayer(),
                structural_data=self.structuralDataLayer.currentLayer(),
                dtm=self.DtmLayer.currentLayer(),
                columnmap=columnmap,
                roi=self.roiLayer.currentLayer(),
                top=self.heightSpinBox.value(),
                bottom=self.depthSpinBox.value(),
                dip_direction=self.orientationType.currentIndex() == 1,
                rotation=self.rotationDoubleSpinBox.value(),
            )
            self.model = processor.get_model()
            for feature in self.model.features:
                item = QListWidgetItem()
                item.setText(feature.name)
                item.setBackground(
                    QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                )
                self.modelList.addItem(item)
        except Exception as e:
            print(e)

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
            print('Running model')
            self.model.update()
            print('Model updated')
        except Exception as e:
            print(e)

    def linkFieldToLayer(self, field, layer):
        pass

    def onBasalContactsChanged(self, layer):
        self.unitNameField.setLayer(layer)

    def onFaultTraceLayerChanged(self, layer):
        self.faultNameField.setLayer(layer)
        self.faultDipField.setLayer(layer)
        self.faultDisplacementField.setLayer(layer)

    def onUnitFieldChanged(self, field):
        unique_values = set()
        layer = self.unitNameField.layer()
        if layer:
            field_index = layer.fields().indexFromName(field)
            for feature in layer.getFeatures():
                unique_values.add(feature[field_index])
        self._units = dict(
            zip(
                list(unique_values),
                [{'thickness': 10.0, 'order': i} for i in range(len(unique_values))],
            )
        )
        self._initialiseStratigraphicColumn()

    def onFaultFieldChanged(self, field):
        name_field = self.faultNameField.currentField()
        dip_field = self.faultDipField.currentField()
        displacement_field = self.faultDisplacementField.currentField()
        layer = self.faultNameField.layer()
        if name_field and dip_field and displacement_field and layer:
            self._faults = {}
            for feature in layer.getFeatures():
                self._faults[feature[name_field]] = {
                    'dip': feature[dip_field],
                    'displacement': feature[displacement_field],
                }
            if self._faults:
                faults = list(self._faults.keys())
                self.faultSelection.clear()
                self.faultSelection.addItems(faults)

    def _initialiseStratigraphicColumn(self):
        while self.stratigraphicColumnContainer.count():
            child = self.stratigraphicColumnContainer.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for i, (unit, value) in enumerate(self._units.items()):
            label = QLabel(unit)
            spin_box = QDoubleSpinBox(maximum=10000, minimum=0)
            spin_box.setValue(value['thickness'])
            order = QSpinBox()
            order.setValue(value['order'])
            self.stratigraphicColumnContainer.addWidget(label, i, 0)
            self.stratigraphicColumnContainer.addWidget(spin_box, i, 1)
            self.stratigraphicColumnContainer.addWidget(order, i, 2)

    def onSaveModel(self):
        fileFormat = self.fileFormatCombo.currentText()
        path = self.outputPath
        name = self.modelNameLineEdit.text()
        filename = os.path.join(path, name + "." + fileFormat)

        self.model.save(filename=os.path.join(path, name + "." + fileFormat))
        self.model.bounding_box.vtk().save(os.path.join(path, name + "_bounding_box." + fileFormat))
        # if self.stratigraphicSurfacesCheckBox.isChecked():
        #     self.model.save_surfaces(
        #         os.path.join(path, name + "_surfaces." + fileFormat)
        #     )
        # if self.faultSurfacesCheckBox.isChecked():
        #     self.model.save_faults(os.path.join(path, name + "_faults." + fileFormat))
        # if self.blockModelCheckBox.isChecked():
        #     self.model.save_block_model(os.path.join(path, name + "_block." + fileFormat))
        # if self.blockModelCheckBox.isChecked():
        #     self.model.save_block_model(os.path.join(path, name + "_block." + fileFormat))
        # if self.
        # pass

    def onClickPath(self):
        self.outputPath = QFileDialog.getExistingDirectory(None, "Select output path for model")

        self.path.setText(self.outputPath)
        # if self.path:
        #     if os.path.exists(self.gridDirectory):
        #         self.output_directory = os.path.split(
        #             self.dlg.lineEdit_gridOutputDir.text()
        #         )[-1]
