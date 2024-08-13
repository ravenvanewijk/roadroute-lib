from shapely.geometry import LineString
import taxicab_st as ts

def reverse_linestring(ls):
    return LineString(ls.coords[::-1])

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

    # Use the nodes to extract all edges u, v of graph G that the vehicle completely traverses
    routepart_edges = zip(routepart[1][:-1], routepart[1][1:])

    # routepart at beginning
    route.append(routepart[2])

    # First time you have to get 2 speed limits, first wp spdlim does not matter, will be reached instantly
    spdlims.extend([def_spd] * (len(routepart[2].coords)))

    try:
        # For every pair of edges, append the route with the Shapely LineStrings
        for u, v in routepart_edges:
            # Some edges have this attribute embedded, when geometry is curved
            if 'geometry' in G.edges[(u, v, 0)]:
                route.append(G.edges[(u, v, 0)]['geometry'])
                spdlims.extend([G.edges[(u, v, 0)][speed_attr]] * (len(G.edges[(u, v, 0)]['geometry'].coords) - 1))
            # Other edges don't have this attribute. These are straight lines between their two nodes.
            else:
                # So, get a straight line between the nodes and append that line piece
                route.append(LineString([(G.nodes[u]['x'], G.nodes[u]['y']), 
                                        (G.nodes[v]['x'], G.nodes[v]['y'])]))
                spdlims.extend([G.edges[(u, v, 0)][speed_attr]])
    except IndexError:
        pass
    
    try:
        # Additional check for first linepart directionality. Sometimes it might be facing the wrong way.
        # The end of the beginning (incomplete) linestring should match
        try:
            if not route[1].coords[0] == routepart[2].coords[-1]:
                # Check if flipped version does align
                if route[1].coords[0] == routepart[2].coords[0]:
                    route[0] = reverse_linestring(route[0])
                else:
                    raise Exception('Taxicab alignment Error: Coordinates of beginning LineString does not align')
        except IndexError:
            pass
    except AttributeError:
        pass

    try:
        # Check whether final incomplete linestring is in proper direction, similar check
        try:
            if not route[-1].coords[-1] == routepart[3].coords[0]:
                # Check if flipped version does align
                if route[-1].coords[-1] == routepart[3].coords[-1]:
                    route.append(reverse_linestring(routepart[3]))

                # Rare exception where the first linepiece was added in 
                # the wrong direction. Only occurs where routepart[1] == []
                elif route[-1].coords[0] == routepart[3].coords[0]:
                    route[0] = reverse_linestring(route[0])
                    route.append(routepart[3])
                elif route[-1].coords[0] == routepart[3].coords[1]:
                    route[0] = reverse_linestring(route[0])
                    route.append(reverse_linestring(routepart[3]))
                else:
                    raise Exception('Taxicab alignment Error: Coordinates of final LineString does not align')
            else:
                route.append(routepart[3])
            spdlims.extend([def_spd] * (len(routepart[3].coords) - 1))
        except IndexError:
            pass
    except AttributeError or IndexError:
        pass

    return route, spdlims