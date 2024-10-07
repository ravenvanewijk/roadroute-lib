from shapely.geometry import LineString
from shapely.ops import linemerge
import taxicab_st as ts
from osmnx.routing import route_to_gdf

def reverse_linestring(ls):
    return LineString(ls.coords[::-1])

def round_coords(coords, decimal_places=6):
    return tuple(round(coord, decimal_places) for coord in coords)

def roadroute(G, A, B, speed_attr='maxspeed_kts', def_spd=26.07):
    """Compute the road route from point A to point B using the taxicab distance.
    
    Args:
        - A: tuple/ list of floats, the starting point (lat, lon)
        - B: tuple/ list of floats, the destination point (lat, lon)
    """
    route = []
    spdlims = []
    routepart = ts.time.shortest_path(G, [A[0], A[1]], 
                                                [B[0], B[1]])

    if type(routepart[3]) != list:
        end_ls = linemerge([routepart[3]])
    else:
        end_ls = routepart[3]

    if type(routepart[2]) != list:
        begin_ls = linemerge([routepart[2]])
        # routepart at beginning        
        route.append(begin_ls)
        # First time you have to get 2 speed limits, first wp spdlim does not 
        # matter, will be reached instantly
        spdlims.extend([def_spd] * (len(begin_ls.coords)))
    
    else:
        begin_ls = routepart[2]
        # We dont have a beginning so we can just add the default speed to the
        # beginning
        spdlims.extend([def_spd])

    try:
        gdf = route_to_gdf(G,routepart[1])
        # For every pair of edges, append the route with the 
        # Shapely LineStrings
        for idx, row in gdf.iterrows():
            if 'geometry' in row:
                # Some edges have this attribute embedded
                route.append(row['geometry'])
                spdlims.extend([row[speed_attr]] * \
                    (len(row['geometry'].coords) - 1))
                # Other edges don't have this attribute. 
                # These are straight lines between their two nodes.
            else:
                # So, get a straight line between the nodes 
                # and append that line piece
                route.append(LineString([(G.nodes[u]['x'], G.nodes[u]['y']), 
                        (G.nodes[v]['x'], G.nodes[v]['y'])]))
                spdlims.extend([row[speed_attr]])

    except ValueError:
        # No edges in routepart[1], continue with route
        pass
    
    try:
        # Additional check for first linepart directionality. Sometimes it might be facing the wrong way.
        # The end of the beginning (incomplete) linestring should match
        try:
            if not route[1].coords[0] == begin_ls.coords[-1]:
                # Check if flipped version does align
                if route[1].coords[0] == begin_ls.coords[0]:
                    route[0] = reverse_linestring(route[0])
                else:
                    raise Exception('Taxicab alignment Error: Coordinates of beginning LineString ' +
                                    f'does not align in route from {A} to {B}')
        except IndexError:
            pass
    except AttributeError:
        pass

    try:
        # Check whether final incomplete linestring is in proper direction, similar check
        try:
            if not route[-1].coords[-1] == end_ls.coords[0]:
                # Check if flipped version does align
                if route[-1].coords[-1] == end_ls.coords[-1]:
                    route.append(reverse_linestring(end_ls))

                # Rare exception where the first linepiece was added in 
                # the wrong direction. Only occurs where routepart[1] == []
                elif route[-1].coords[0] == end_ls.coords[0]:
                    route[0] = reverse_linestring(route[0])
                    route.append(end_ls)
                elif route[-1].coords[0] == end_ls.coords[-1]:
                    route[0] = reverse_linestring(route[0])
                    route.append(reverse_linestring(end_ls))
                else:
                    if round_coords(route[-1].coords[-1]) == round_coords(end_ls.coords[0]):
                        # Get the current coordinates of end_ls
                        current_coords = list(end_ls.coords)
                        # Replace the beginning coordinate with the rounded version
                        current_coords[0] = round_coords(current_coords[0])
                        # Create a new LineString with the modified coordinates
                        end_ls = LineString(current_coords)
                        route.append(end_ls)
                    elif round_coords(route[-1].coords[-1]) == round_coords(end_ls.coords[-1]):
                        # Get the current coordinates of end_ls
                        current_coords = list(end_ls.coords)
                        # Replace the last coordinate with the rounded version
                        current_coords[-1] = round_coords(current_coords[-1])
                        # Create a new LineString with the modified coordinates
                        end_ls = LineString(current_coords)
                        route.append(end_ls)
                    elif round_coords(route[-1].coords[0]) == round_coords(end_ls.coords[0]):
                        route[0] = reverse_linestring(route[0])
                        # Get the current coordinates of end_ls
                        current_coords = list(end_ls.coords)
                        # Replace the beginning coordinate with the rounded version
                        current_coords[0] = round_coords(current_coords[0])
                        # Create a new LineString with the modified coordinates
                        end_ls = LineString(current_coords)
                        route.append(end_ls)
                    elif round_coords(route[-1].coords[0]) == round_coords(end_ls.coords[-1]):
                        route[0] = reverse_linestring(route[0])
                        # Get the current coordinates of end_ls
                        current_coords = list(end_ls.coords)
                        # Replace the last coordinate with the rounded version
                        current_coords[-1] = round_coords(current_coords[-1])
                        # Create a new LineString with the modified coordinates
                        end_ls = LineString(current_coords)
                        route.append(end_ls)
                    else:
                        raise Exception('Taxicab alignment Error: Coordinates of final LineString ' +
                                        f'does not align in route from {A} to {B}')
            else:
                route.append(end_ls)
            spdlims.extend([def_spd] * (len(end_ls.coords) - 1))
        except IndexError:
            pass
    except AttributeError or IndexError:
        pass
    # print(len(linemerge(route).coords), len(spdlims))
    return route, spdlims, routepart[4]



# import osmnx as ox
# import numpy as np
# import matplotlib.pyplot as plt
# import pandas as pd
# from shapely import Point
# from shapely.ops import linemerge



# def plot_graph(G, custs, lines=[]):
#     """Plots the graph of the selected gpkg file as well as customer 
#     locations"""
#     # Plot city graph
#     fig, ax = ox.plot_graph(G, show=False, close=False)
#     # Plot the customers
#     locs_scatter = ax.scatter([point.x for _, point in custs.items()],
#                                     [point.y for _, point in custs.items()],
#                                     c='red', s=30, zorder=10, label='L&R locations')

#     for line in lines:
#         x, y = line.xy
#         ax.plot(x, y, marker='o')  # Plot the line with markers at vertices
#         ax.plot(x[-1],y[-1],'rs') 

#     # Show the plot with a legend
#     ax.legend(handles=[locs_scatter])
#     plt.show()


# def str_interpret(value):
#     return value  # Ensure the value remains a string

# G = ox.load_graphml(filepath='roadroute_lib/Buffalo.graphml',
#                         edge_dtypes={'osmid': str_interpret,
#                                     'reversed': str_interpret})

# # A = np.array([42.876466914460224, -78.78590820757644])
# # B = np.array([42.868358900000004, -78.8312416])
# # # A = (G.nodes[7779745399]['y'], G.nodes[7779745399]['x'])
# # # B = (G.nodes[11209177619]['y'], G.nodes[11209177619]['x'])
# # A = np.array([42.88189546413181, -78.74404160878684])
# # # B = np.array([42.88198599999998, -78.746419])
# # A = np.array([42.948108, -78.762627])
# # B = np.array([42.894466, -78.717194])

# # A = np.array([42.92238771355551, -78.83363366913012])
# # B = np.array([42.92179680000001, -78.8336239])
# # A = np.array([42.961694872237025, -78.7593302452336])
# # B = np.array([ 42.965185599999984, -78.7593501])

# # A = np.array([42.99148177004806, -78.77108391446286])
# # B = np.array([ 42.99134759999998, -78.7821653])

# # A = np.array([ 42.959665588770186, -78.76380033011569])
# # B = np.array([42.959674699999994, -78.7635801])

# # B = np.array([47.5665561, -122.3895247])
# # A = np.array([47.625187, -122.352789])
# # A = np.array([47.680838, -122.104114])
# # B = np.array([47.682122, -122.10635])
# # A = np.array([47.608602, -122.285365])
# # B = np.array([47.574254, -122.326014])

# # A = np.array([47.638784, -122.203969])
# # B = np.array([47.656661, -122.30764])

# # A = np.array([47.637992, -122.191499])
# # B = np.array([47.640464, -122.192521])

# # A = np.array([ 42.92305694340832, -78.79219871640545])
# # B = np.array([42.915278, -78.807147])


# # A = np.array([ 42.88555098277178, -78.73841364608232])
# # B = np.array([42.8840926, -78.7405278])

# # A = np.array([ 42.884176113364624, -78.73975253760874])
# # B = np.array([42.8840926, -78.7405278])

# # A = np.array([ 42.88555098277178, -78.73841364608232])
# # B = np.array([42.8840926, -78.7405278])

# A = np.array([ 42.87751705032876, -78.87284030250486])
# B = np.array([42.8806299, -78.8796273])


# # A = np.array([47.547134, -122.336966])
# # B = np.array([47.538336, -122.295355])
# # A = np.array([42.875181199999986, -78.861864])
# # B = np.array([ 42.856027, -78.867927])

# custs = pd.Series([Point(A[1], A[0]), Point(B[1], B[0])])
# q,w,e= roadroute(G,A,B)   
# q_merged = linemerge(q)
# a=1
# # plot_graph(G, custs, [q[8]])
# # plot_graph(G,custs, [q[7]])