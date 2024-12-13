from LoopStructural import GeologicalModel
from LoopStructural.modelling.input import ProcessInputData
from .vectorLayerWrapper import qgsLayerToDataFrame


class QgsProcessInputData(ProcessInputData):
    def __init__(self, basal_contacts , stratigraphic_column: dict, faults, structural_data, dtm, columnmap:dict,roi, top:float, bottom:float,dip_direction:bool):
        
        contact_locations = qgsLayerToDataFrame(basal_contacts,dtm)
        fault_data = qgsLayerToDataFrame(faults,dtm)
        contact_orientations = qgsLayerToDataFrame(structural_data,dtm)
        thicknesses = {}
        for key in stratigraphic_column.keys():
            thicknesses[key] = stratigraphic_column[key]['thickness']
        stratigraphic_order = [None]*len(thicknesses)
        for key in stratigraphic_column.keys():
            stratigraphic_order[stratigraphic_column[key]['order']] = key
        stratigraphic_order=[('sg',stratigraphic_order)]
        roidf = qgsLayerToDataFrame(roi,None)
        minx = roidf['X'].namin()
        maxx = roidf['X'].max()
        miny = roidf['Y'].min()
        maxy = roidf['Y'].max()
        origin = (minx, miny, bottom)
        maximum = (maxx, maxy, top)
        if contact_locations is not None:
            contact_locations = contact_locations.rename(columns={columnmap['unitname']:'name'})[['X','Y','Z','name']]
        if fault_data is not None:
            fault_data = fault_data.rename(columns={columnmap['faultname']:'fault_name'})[['X','Y','Z','fault_name']]
        if contact_orientations is not None:
            contact_orientations = contact_orientations.rename(columns={columnmap['structure_unitname']:'name',
                                                                        columnmap['dip']:'dip',
                                                                        columnmap['orientation']:'strike'})[['X','Y','Z','dip','strike','name']]
            contact_orientations['dip'] = contact_orientations['dip'].astype(float)
            contact_orientations['strike'] = contact_orientations['strike'].astype(float)

            if dip_direction:
                contact_orientations['strike'] = contact_orientations['strike'] + 90


                        
        super().__init__(contacts = contact_locations, 
                        stratigraphic_order=stratigraphic_order,
                        thicknesses=thicknesses,
                        fault_locations=fault_data, 
                        contact_orientations=contact_orientations,
                        origin=origin,
                        maximum=maximum,)

    def get_model(self):
        return GeologicalModel.from_processor(self)