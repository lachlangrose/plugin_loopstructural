from LoopStructural import GeologicalModel
from LoopStructural.modelling.input import ProcessInputData
from LoopStructural.utils import EuclideanTransformation
from .vectorLayerWrapper import qgsLayerToDataFrame
import pandas as pd

class QgsProcessInputData(ProcessInputData):
    def __init__(
        self,
        basal_contacts,
        stratigraphic_column: dict,
        fault_trace,
        fault_properties,
        structural_data,
        dtm,
        columnmap: dict,
        roi,
        top: float,
        bottom: float,
        dip_direction: bool,
        rotation,
    ):

        contact_locations = qgsLayerToDataFrame(basal_contacts, dtm)
        fault_data = qgsLayerToDataFrame(fault_trace, dtm)
        contact_orientations = qgsLayerToDataFrame(structural_data, dtm)
        thicknesses = {}
        for key in stratigraphic_column.keys():
            thicknesses[key] = stratigraphic_column[key]['thickness']
        stratigraphic_order = [None] * len(thicknesses)
        for key in stratigraphic_column.keys():
            stratigraphic_order[stratigraphic_column[key]['order']] = key
        stratigraphic_order = [('sg', stratigraphic_order)]
        roidf = qgsLayerToDataFrame(roi, None)
        roi_rectangle = roi.extent()
        minx = roi_rectangle.xMinimum()
        maxx = roi_rectangle.xMaximum()
        miny = roi_rectangle.yMinimum()
        maxy = roi_rectangle.yMaximum()
        # transformer = EuclideanTransformation(minx,miny,rotation)

        origin = (minx, miny, bottom)
        maximum = (maxx, maxy, top)
        if contact_locations is not None:
            contact_locations = contact_locations.rename(columns={columnmap['unitname']: 'name'})[
                ['X', 'Y', 'Z', 'name']
            ]
        if fault_data is not None:
            fault_data = fault_data.rename(columns={columnmap['faultname']: 'fault_name'})[
                ['X', 'Y', 'Z', 'fault_name']
            ]
        if contact_orientations is not None:
            contact_orientations = contact_orientations.rename(
                columns={
                    columnmap['structure_unitname']: 'name',
                    columnmap['dip']: 'dip',
                    columnmap['orientation']: 'strike',
                }
            )[['X', 'Y', 'Z', 'dip', 'strike', 'name']]
            contact_orientations['dip'] = contact_orientations['dip'].astype(float)
            contact_orientations['strike'] = contact_orientations['strike'].astype(float)

            if dip_direction:
                contact_orientations['strike'] = contact_orientations['strike'] + 90
        fault_properties=pd.DataFrame(fault_properties,columns=['fault_name','dip','displacement','major_axis','intermediate_axis','minor_axis','active','azimuth','crs'])


        super().__init__(
            contacts=contact_locations,
            stratigraphic_order=stratigraphic_order,
            thicknesses=thicknesses,
            fault_locations=fault_data,
            contact_orientations=contact_orientations,
            fault_properties=fault_properties,
            origin=origin,
            maximum=maximum,
        )

    def get_model(self):
        return GeologicalModel.from_processor(self)
