from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsMapLayerProxyModel

from PyQt5.QtCore import QSize

from qgis.PyQt.QtWidgets import QWidget, QListWidgetItem, QTableWidgetItem, QLabel, QDoubleSpinBox, QSpinBox

import random
import os
from ...main import QgsProcessInputData
# from loopstructural.gui.modelling.stratigraphic_column import StratigraphicColumnWidget
class ModellingWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__),"modelling_widget.ui"), self)
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
        self.initModel.clicked.connect(self.initialiseModel)

        # self.runModel.clicked.connect(self.runModel)
    def initialiseModel(self):
        columnmap = {'unitname':self.unitNameField.currentField(),
        'faultname':self.faultNameField.currentField(),
        'dip':self.dipField.currentField(),
        'orientation':self.orientationField.currentField(),
        'structure_unitname':self.structuralDataUnitName.currentField()
        }
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
            dip_direction=self.orientationType.currentIndex()==1
        )
        self.model = processor.get_model()
    # def runModel(self):
    #     self.model.update()

    def onOrientationTypeChanged(self, index):
        if index == 0:
            self.orientationLabel.setText("Strike")
        else:
            self.orientationLabel.setText("Dip Direction")

    def onOrientationFieldChanged(self, field):
        pass
    def onStructuralDataLayerChanged(self, layer):
        self.orientationField.setLayer(layer)
        self.dipField.setLayer(layer)
        self.structuralDataUnitName.setLayer(layer)
        # self.dipField.setValidator(QDoubleValidator(0.0, 360.0, 2))
        # self.orientationField.setValidator(QDoubleValidator(0.0, 360.0, 2))
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
        self._units = dict(zip(list(unique_values),[{'thickness':10.,'order':i} for i in range(len(unique_values))]))
        self._initialiseStratigraphicColumn()
    def onFaultFieldChanged(self, field):
        name_field = self.faultNameField.currentField()
        dip_field = self.faultDipField.currentField()
        displacement_field = self.faultDisplacementField.currentField()
        layer = self.faultNameField.layer()
        if name_field and dip_field and displacement_field and layer:
            self._faults = {}
            for feature in layer.getFeatures():
                self._faults[feature[name_field]] = {'dip':feature[dip_field],'displacement':feature[displacement_field]}
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
            spin_box = QDoubleSpinBox()
            spin_box.setValue(value['thickness'])
            order = QSpinBox()
            order.setValue(value['order'])
            self.stratigraphicColumnContainer.addWidget(label, i, 0)
            self.stratigraphicColumnContainer.addWidget(spin_box, i, 1)
            self.stratigraphicColumnContainer.addWidget(order, i, 2)
    

