#!/usr/bin/python

'''
An example showing how to add and delete hosts, switches, and links
in a CLI.

Note: UserSwitch is not currently supported.
'''

from mininet.topo import SingleSwitchTopo
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel, info, error, debug

class alterableCLI( CLI ):
    "allow addition and deletion of objects from CLI"
    
    def do_delswitch( self, line ):
        "usage: delswitch switchname"
        args = line.split()
        if len( args ) != 1:
            error( 'usage: delswitch switchname\n' )
            return
        switchname = args[ 0 ]
        if switchname not in self.mn.nameToNode.keys():
            error( '*** no switch named %s\n' % switchname )
            return
        switch = self.mn.nameToNode[ switchname ]
        self.mn.removeNode( switch )

    def do_dellink( self, line ):
        "usage: dellink node1 node2"
        args = line.split()
        if len( args ) != 2:
            error( 'usage: dellink node1 node2\n' )
            return
        node1Name = args[ 0 ]
        node2Name = args[ 1 ]
        for node in node1Name, node2Name:
            if node not in self.mn.nameToNode.keys():
                error( '*** no node named %s\n' % node )
                return
        node1 = self.mn.nameToNode[ node1Name ]
        node2 = self.mn.nameToNode[ node2Name ]
        self.mn.delLink( node1, node2 )

    def do_delhost( self, line ):
        "usage: delhost hostname"
        args = line.split()
        if len( args ) != 1:
            error( 'usage: delhost hostname\n' )
            return
        hostname = args[ 0 ]
        if hostname not in self.mn.nameToNode.keys():
            error( '*** no host named %s\n' % hostname )
            return
        host = self.mn.nameToNode[ hostname ]
        self.mn.removeNode( host )

    def do_addhost( self, line ):
        "usage: addhost hostname [ switch ]"
        args = line.split()
        if len( args ) < 1 or len( args ) > 2:
           error( 'usage: addhost hostname [ switch ]\n' )
           return
        if len( args ) == 2:
            connectSwitch = True
        else:
            connectSwitch = False
        hostname = args[ 0 ]
        if hostname in self.mn:
            error( '%s already exists!\n' % hostname )
            return
        if connectSwitch:
            switchname = args[ 1 ]
            if switchname not in self.mn:
                error( '%s doesnt exist!\n' % switchname )
                return
            switch = self.mn.nameToNode[ switchname ]
        host = self.mn.addHost( hostname )
        if connectSwitch:
            link = self.mn.addLink( host, switch )
            switch.attach( link.intf2 )
            host.configDefault()
        else:
            host.config()

    def do_addswitch( self, line ):
        "usage: addswitch switchname"
        args = line.split()
        if len( args ) != 1:
            error( 'usage: addswitch switchname\n' )
            return
        switchname = args[ 0 ]
        if switchname in self.mn:
            error( '%s already exists!\n' % switchname )
            return
        switch = self.mn.addSwitch( switchname )
        switch.start( self.mn.controllers )

    def do_addlink( self, line ):
        "usage: addlink node1 node2"
        args = line.split()
        if len( args ) < 2:
            error( 'usage: addlink node1 node2\n' )
            return
        node1Name = args[ 0 ]
        node2Name = args[ 1 ]
        for node in node1Name, node2Name:
            if node not in self.mn:
                error( '%s doesnt exist!\n' % node )
                return
        node1 = self.mn.nameToNode[ node1Name ]
        node2 = self.mn.nameToNode[ node2Name ]
        link = self.mn.addLink( node1, node2  )
        for node in node1, node2:
            if node in self.mn.hosts:
                node.configDefault( **node.params )
            elif node in self.mn.switches:
                if node is node1:
                    node.attach( link.intf1 )
                if node is node2:
                    node.attach( link.intf2 )

class alterNet( Mininet ):

    # I was a little confused about this datastructure upon first look. maybe this will help others?
    def getNodeLinks( self, node ):
        """Get all of the links attached to a node.
           node: node name
           returns: dictionary of interfaces to connected nodes"""
        interfaces = []
        nodeLinks = {}
        for intf in node.intfList():
            if intf.link:
                intfs = [ intf.link.intf1, intf.link.intf2 ]
                intfs.remove( intf )
                interfaces += intfs
                nodeLinks[ intfs[ 0 ] ] = intfs[ 0 ].node 
        return nodeLinks

    def removeNode( self, node ):
        """remove a node from a running network
           returns True if successful"""
        if node not in self.hosts + self.switches:
            error( '%s doesnt exist!\n' % node )
            return 0
        node.stop()
        node.cleanup()
        nodeLinks = self.getNodeLinks( node )
        for intf, n in nodeLinks.items():
            del n.intfs[ n.ports[ intf ] ]
            del n.ports[ intf ]
        if node in self.hosts:
            self.hosts.remove( node )
        elif node in self.switches:
            self.switches.remove( node )
            info( '\n' )
        del self.nameToNode[ node.name ]
        return 1

    def delLink( self, node1, node2 ):
        """delete a link from mininet while running
           returns True if successful"""
        for intf in node1.intfList():
            if intf.link:
                intf1 = intf
                intfs = [ intf.link.intf1, intf.link.intf2 ]
                intfs.remove( intf )
                intf2 = intfs[0]
                if intf2 in node2.intfList():
                    intf.link.delete()
                    port1 = node1.ports[ intf1 ]
                    port2 = node2.ports[ intf2 ]
                    del node1.nameToIntf[ intf1.name ]
                    del node2.nameToIntf[ intf2.name ]
                    del node1.intfs[ port1 ]
                    del node2.intfs[ port2 ]
                    del node1.ports[ intf1 ]
                    del node2.ports[ intf2 ]
                    return True
        debug( '*** warning: no link between %s and %s\n' %( node1, node2 ) )
        return False



def testCLI():
    net = alterNet(topo = SingleSwitchTopo())
    net.start()
    alterableCLI( net )
    net.stop()

def testAPI():
    net = alterNet(topo = SingleSwitchTopo())
    net.start()
    net.pingAll()
    net.delLink( net.hosts[0], net.switches[ 0 ] )
    net.pingAll()
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    testCLI()
    #testAPI()
