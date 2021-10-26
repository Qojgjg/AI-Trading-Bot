import numpy as np
import math

"""
    Polynomial Encoders Nested (PEN). Ver 0.5.
"""

class Pen:
    def __init__( self, delta_x = 1, takeZero = False, takeEnd = False, \
        y0 = 1.0, len_x = 10, ymax = 10, left = 3, right = 6, relative = True ):
        
        super().__init__()

        self.maxGrad = np.log10(1.0 + 0.10) / 60 # 10% price change per 60 periods (minutes)

        self.delta_x = delta_x
        self.len_x = len_x
        self.relative = relative

        # model: chnage_rate( x ) = alpha * sigmoid( beta * ( x - xcenter ) ) + gamma
        self.alpha = ( ymax - y0 ) / ( self.sigmoid( right ) - self.sigmoid( left ) )
        self.beta = ( right - left ) / len_x
        self.xcenter = - len_x * left / ( right - left )
        self.gamma = y0 - self.alpha * self.sigmoid( self.beta * - self.xcenter )

        return


    def sigmoid( self, x):
        return 1.0/(1+ math.exp(-x))

    def ContinuousAverage( self, array, idx, neighbourhood ):
        minIdx = max( 0, idx - int(neighbourhood) )
        maxIdx = min( len(array) - 1, idx + int(neighbourhood) )
        sum = np.sum( array[ minIdx : maxIdx + 1 ] ); neigh = maxIdx + 1 - minIdx; fraction = neighbourhood - int(neighbourhood)
        if 1 <= minIdx and minIdx < len(array) + 1:
            sum += fraction * array[minIdx-1]; neigh += fraction
        if -1 <= maxIdx and maxIdx < len(array) - 1:
            sum += fraction * array[maxIdx+1]; neigh += fraction
        avg = sum / neigh

        return array[idx]


    def GetChangeWeight( self, x ) :
        return self.alpha * self.sigmoid( self.beta * ( x - self.xcenter ) ) + self.gamma

    def GetMinChangeRange( self, indi, idx, change ):
        weightedChange = change * self.GetChangeWeight( idx )       
        #neighbor = np.log10( 1+ weightedChange ) * 10000 # 100: imperical.
        # logRangeBottom = indi[idx] - -np.log10(1.0 - weightedChange) # Option for futures.
        base = indi[idx] # self.ContinuousAverage(indi, idx, neighbor)
        logRangeBottom = base - np.log10(1.0 + weightedChange) # Option for saving fluctuation resources.
        # logRangeBottom = indi[idx] - 0.5 * np.log10(1.0 + weightedChange) # Option for saving fluctuation resources more.
        logRangeTop = base + np.log10(1.0 + weightedChange)

        return logRangeBottom, logRangeTop


    def IsBigChange( self, indi, idxTimeward, nodeA, nodeB, change ): 
        node_from = min( nodeA, nodeB ) if idxTimeward else max( nodeA, nodeB )
        node_to = max( nodeA, nodeB ) if idxTimeward else min( nodeA, nodeB )
        weightedChange = change * self.GetChangeWeight( node_to )
        neighbor = np.log10( 1+ weightedChange ) * 10000 # 100: imperical.
        rangeBottom, rangeTop = self.GetMinChangeRange( indi, node_from, change )
        #valid = self.ContinuousAverage(indi, node_to, neighbor) <= rangeBottom or rangeTop <= self.ContinuousAverage(indi, node_to, neighbor)
        valid = indi[node_to] <= rangeBottom or rangeTop <= indi[node_to]

        return valid


    def GetRanges( self, indis, nodes, change ):
        ranges = np.zeros((0, 2), dtype = indis.dtype)
        for node in nodes :
            range = self.GetMinChangeRange( indis, node, change )
            ranges = np.append( ranges, np.expand_dims( np.array( range ), axis=0 ), axis=0 )

        return ranges


    def GetSimpleNodes( self, indi, takeZero = False, takeEnd = False, takeLastCandidate = False, start = 0, end = -1, maxNodes = -1, padding = False, change = 0.001, toggle = True, idxTimeward = True ):
        assert( maxNodes < len(indi) )
        assert( start < len(indi) )
        assert( self.len_x == len(indi) )
        if end == -1: end = len(indi)
        assert( start < end )

        maxNodes = len(indi) if maxNodes < 0 else maxNodes

        nodes = [start]
        candidate = start
        prover = start
        rising = False # any

        for prover in range( start + 1, end ):

            if self.IsBigChange( indi, idxTimeward, nodes[-1], prover, change ):
            # proof proved that candidate must be changed to itself.
            # Note proof is left to nodes[-1] on time axis. time(proof) < time(nodes[-1]) while proof > nodes[-1].

                if candidate == start :
                    # Just for initialization.
                    rising = ( indi[prover] > indi[ 0 ] )
                    candidate = prover

                if toggle and ( ( indi[prover] > indi[ candidate ] ) == rising ) :
                    # proof is in the same direction as before.
                    candidate = prover

                elif not toggle and (abs(prover - nodes[-1]) >= self.delta_x) :
                    # proof is in the same direction as before.
                    #new_nodes = self.AddGradientNodes( indi, nodes[-1], prover, change, toggle )
                    #nodes += new_nodes

                    nodes.append( prover )
                    candidate = prover

            if candidate != start and self.IsBigChange( indi, idxTimeward, candidate, prover, change ):
            # proof proved that candidate is eligible for node.
            # Note proof is left to candidate on time axis. time(proof) < time(candidate) while proof > candidate.

                # x,y is far from the candidate, which is, in turn, far from the last pole.
                # x,y is NOT in the same direction as before.
                # Try to collect more nodes between nodes[-1] and candidate.
                               
                nodes.append( candidate )
                candidate = prover
                rising = not rising

            if len(nodes) >= maxNodes : break

        # takeZero.
        if takeZero is True and 0 < nodes[0] :
            nodes.insert(0, 0)

        # take the last candidate.
        if takeLastCandidate and nodes[-1] < candidate and candidate < len( indi ) :
            nodes.append( candidate )

        # takeEnd.
        if takeEnd and nodes[-1] < len( indi ) :
            nodes.append( len( indi ) - 1 )

        nodes = sorted(list(set(nodes)))
        
        missings = maxNodes - len(nodes)
        if padding is True and missings > 0 :
            #nodes = nodes + [ nodes[-1] + int( (len(indi)-nodes[-1]) / missings * missing_i ) for missing_i in range(missings) ]
            nodes = nodes + [ nodes[-1] for missing_i in range(missings) ]
        elif missings < 0 :
            nodes = nodes[ : missings ]

        return np.array( nodes )


    def GetGradientNodes( self, indi, start, end, maxNodes, change, toggle, idxTimeward = True ) : # return nodes not inclusive of start and end.
        indi_local = np.zeros( ( len(indi),), dtype = type(indi) )
        gradient = ( indi[end] - indi[start] ) / ( end - start )      

        linear = [ indi[start] + (x - start) * gradient for x in range(start, end+1) ]
        
        # Option 1
        change = (0.2 + abs(gradient) / self.maxGrad) * change
        delta = indi[start : end+1] - np.array( linear, dtype= indi_local.dtype )
        
        """
        # Option 2
        change = change
        angle = np.arctan( 100000 * gradient )
        c = np.array( [ indi[i] - linear[i-start] for i in range(start, end+1) ] )
        b = np.cos( angle ) * c
        a = np.sin( angle ) * c
        delta = b
        """

        np.copyto( indi_local[start : end+1], delta )

        Px = self.GetSimpleNodes( indi_local, start = start, end = end, maxNodes = maxNodes, padding = False, change = change, toggle = toggle, idxTimeward = idxTimeward )
        Px = [ node for node in Px if start != node and node != end-1 ]

        return Px

    def GetNodes( self, indi, takeZero = False, start = 0, maxNodes = -1, padding = False, change = 0.001, toggle = False, idxTimeward = True ):
        if maxNodes < 0: maxNodes = len(indi)
        min2ndNode = len(indi); max1stNode = start

        start1 = start
        while start1 < min2ndNode :
            Px = self.GetSimpleNodes( indi, takeZero = False, start = start1, maxNodes = 2, padding = False, change = change, toggle = toggle, idxTimeward = idxTimeward )

            if len(Px) >= 2 :
                if min2ndNode > Px[1] : min2ndNode = Px[1]

                # Be conservative to keep near the starting point.
                if Px[1] <= min2ndNode :
                    if indi[ Px[0] ] < indi[ Px[1] ] and indi[max1stNode] > indi[Px[0]] : max1stNode = Px[0]
                    elif indi[ Px[0] ] > indi[ Px[1] ] and indi[max1stNode] < indi[Px[0]] : max1stNode = Px[0]
            
            start1 += 1

        nodes = self.GetSimpleNodes( indi, takeZero = takeZero, takeLastCandidate = True, start = max1stNode, maxNodes = maxNodes, padding = padding,  change = change, toggle = toggle, idxTimeward = idxTimeward )

        return nodes


    def JoinAssetsNodes( self, arr_indis, list_nodes, maxNodes, padding, change, cnt_refine = 1, idxTimeward = True ):

        total_nodes = sorted(list(set(np.concatenate( list_nodes ))))

        def AddGradiendNodes( total_nodes ):
            cnt_nodes = len( total_nodes )       
            idx_nodes = 0

            while idx_nodes < cnt_nodes - 1 :
                new_nodes = []
                #total_nodes = sorted(list(set( total_nodes )))
                for indis in arr_indis:
                    idx_nodes = 0
                    while idx_nodes < len(total_nodes) - 1 :
                        if abs(total_nodes[idx_nodes] - total_nodes[idx_nodes+1]) > 1:
                            new_nodes += self.GetGradientNodes( indis, total_nodes[idx_nodes], total_nodes[idx_nodes+1], maxNodes, change, toggle=False, idxTimeward = idxTimeward )
                            # new_nodes += self.GetGradientNodes( np.flip(indis), len(indis)-total_nodes[idx_nodes+1]-1, len(indis)-total_nodes[idx_nodes]-1, maxNodes, change, toggle=False, idxTimeward = not idxTimeward )
                        idx_nodes += 1

                total_nodes += new_nodes
                total_nodes = sorted(list(set( total_nodes )))

            return total_nodes


        #-------------------------------------------------- To improve ------------------------

        def RemoveDenseNodes( arr_indis, total_nodes ):
            cnt_nodes = len( total_nodes )       
            idx_nodes = 0

            while idx_nodes < cnt_nodes - 1 :
                
                node = total_nodes[ idx_nodes ]
                next_node = total_nodes[ idx_nodes + 1 ]
               
                next_node_valid = False
                for idx, indi in enumerate( arr_indis ):
                    if self.IsBigChange( indi, idxTimeward, node, next_node, change ):
                    # Note next_node is left to node in time axis. time(next_node) < time(node) while next_node > node.
                        next_node_valid = True; break
                
                if not next_node_valid : 
                    # node and next_node are not compatible. Remove next_node, which is farther past than node.
                    total_nodes.pop( idx_nodes + 1 )
                    cnt_nodes = len( total_nodes )
                    idx_nodes += 1 # Critical. Remove this line, all nodes will be removed.
                else :
                    idx_nodes += 1

            total_nodes = sorted(list(set( total_nodes )))
        
            return total_nodes

        # Little meaning in call this multiple times.
        total_nodes = AddGradiendNodes( total_nodes )

        #for _ in range( cnt_refine ):
        #    total_nodes = RemoveDenseNodes( arr_indis, total_nodes )


        missings = maxNodes - len(total_nodes)
        if padding is True and missings > 0 :
            #nodes = nodes + [ nodes[-1] + int( (len(indi)-nodes[-1]) / missings * missing_i ) for missing_i in range(missings) ]
            total_nodes = total_nodes + [ total_nodes[-1] for missing_i in range(missings) ]
        elif missings < 0 :
            total_nodes = total_nodes[ : missings ]

        return np.array( total_nodes )
            

    def ConvertToSequence( self, arr_indis, joint_nodes, idxTimeward ):
        if not idxTimeward: arr_indis = np.flip( arr_indis, axis = 1 )

        sequence = np.zeros( ( 0, 1 + len(arr_indis) ), dtype = arr_indis.dtype )

        item = [0.0] + [ indi[0] for indi in arr_indis ] # [ 0.0, indi1[0], indi2[0], ...]. 0.0: there is no previous node.

        length = len( arr_indis[0] )
        sequence = np.append( sequence, np.expand_dims( np.array(item, dtype=sequence.dtype), axis = 0 ), axis = 0 )

        for index, node in enumerate( joint_nodes ):
            if index == 0 : continue

            item = [ 1.0 * abs(joint_nodes[index-1] - joint_nodes[index]) / length ] + [ indi[index] for indi in arr_indis ]
            # item = [ normalized index distance from the previous node, indis values at current node ] ----------- 1 + # of indis.

            sequence = np.append( sequence, np.expand_dims( np.array(item, dtype=sequence.dtype), axis = 0 ), axis = 0 )
            
        if not idxTimeward: arr_indis = np.flip( arr_indis, axis = 1 ) # Restore.

        return sequence # This should be further normalized/regularized.




def CA( array, idx, neighbourhood ):
    minIdx = max( 0, idx - int(neighbourhood) )
    maxIdx = min( len(array) - 1, idx + int(neighbourhood) )
    sum = np.sum( array[ minIdx : maxIdx + 1 ] ); neigh = maxIdx + 1 - minIdx; fraction = neighbourhood - int(neighbourhood)
    if 1 <= minIdx and minIdx < len(array) + 1:
        sum += fraction * array[minIdx-1]; neigh += fraction
    if -1 <= maxIdx and maxIdx < len(array) - 1:
        sum += fraction * array[maxIdx+1]; neigh += fraction
    avg = sum / neigh

    return avg



