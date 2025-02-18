import numpy as np
from qgis.core import QgsPointXY, QgsRaster


def createGrid(boundingBox, dtm):
    """Create a grid from a bounding box and a digital terrain model

    :param boundingBox: Bounding box of the grid
    :type boundingBox: tuple
    :param dtm: Digital Terrain Model
    :type dtm: _type_
    :return: the grid
    :rtype: _type_
    """
    minx, miny, maxx, maxy = boundingBox.corners_global[[0, 2], :2].flatten()
    x = np.linspace(minx, maxx, boundingBox.nsteps[0])
    y = np.linspace(miny, maxy, boundingBox.nsteps[1])
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    if dtm is not None:
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                p = QgsPointXY(X[i, j], Y[i, j])
                z_value = dtm.dataProvider().identify(p, QgsRaster.IdentifyFormatValue)
                if z_value.isValid():
                    z_value = z_value.results()[1]
                else:
                    z_value = -9999
                Z[i, j] = z_value
    pts = np.array([X.flatten(order='f'), Y.flatten(order='f'), Z.flatten(order='f')]).T
    return pts
