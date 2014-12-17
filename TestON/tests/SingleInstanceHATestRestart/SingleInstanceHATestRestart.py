'''
Description: This test is to determine if a single
    instance ONOS 'cluster' can handle a restart

List of test cases:
CASE1: Compile ONOS and push it to the test machines
CASE2: Assign mastership to controllers
CASE3: Assign intents
CASE4: Ping across added host intents
CASE5: Reading state of ONOS
CASE6: The Failure case. Since this is the Sanity test, we do nothing.
CASE7: Check state after control plane failure
CASE8: Compare topo
CASE9: Link s3-s28 down
CASE10: Link s3-s28 up
CASE11: Switch down
CASE12: Switch up
CASE13: Clean up
CASE14: start election app on all onos nodes
CASE15: Check that Leadership Election is still functional
'''
class SingleInstanceHATestRestart:

    def __init__(self) :
        self.default = ''

    def CASE1(self,main) :
        '''
        CASE1 is to compile ONOS and push it to the test machines

        Startup sequence:
        git pull
        mvn clean install
        onos-package
        cell <name>
        onos-verify-cell
        NOTE: temporary - onos-remove-raft-logs
        onos-install -f
        onos-wait-for-start
        '''
        import time
        main.log.report("ONOS Single node cluster restart HA test - initialization")
        main.case("Setting up test environment")

        # load some vairables from the params file
        PULL_CODE = False
        if main.params['Git'] == 'True':
            PULL_CODE = True
        cell_name = main.params['ENV']['cellName']

        #set global variables
        global ONOS1_ip
        global ONOS1_port
        global ONOS2_ip
        global ONOS2_port
        global ONOS3_ip
        global ONOS3_port
        global ONOS4_ip
        global ONOS4_port
        global ONOS5_ip
        global ONOS5_port
        global ONOS6_ip
        global ONOS6_port
        global ONOS7_ip
        global ONOS7_port
        global num_controllers

        ONOS1_ip = main.params['CTRL']['ip1']
        ONOS1_port = main.params['CTRL']['port1']
        ONOS2_ip = main.params['CTRL']['ip2']
        ONOS2_port = main.params['CTRL']['port2']
        ONOS3_ip = main.params['CTRL']['ip3']
        ONOS3_port = main.params['CTRL']['port3']
        ONOS4_ip = main.params['CTRL']['ip4']
        ONOS4_port = main.params['CTRL']['port4']
        ONOS5_ip = main.params['CTRL']['ip5']
        ONOS5_port = main.params['CTRL']['port5']
        ONOS6_ip = main.params['CTRL']['ip6']
        ONOS6_port = main.params['CTRL']['port6']
        ONOS7_ip = main.params['CTRL']['ip7']
        ONOS7_port = main.params['CTRL']['port7']
        num_controllers = int(main.params['num_controllers'])


        main.step("Applying cell variable to environment")
        cell_result = main.ONOSbench.set_cell(cell_name)
        verify_result = main.ONOSbench.verify_cell()

        #FIXME:this is short term fix
        main.log.report("Removing raft logs")
        main.ONOSbench.onos_remove_raft_logs()
        main.log.report("Uninstalling ONOS")
        main.ONOSbench.onos_uninstall(ONOS1_ip)
        main.ONOSbench.onos_uninstall(ONOS2_ip)
        main.ONOSbench.onos_uninstall(ONOS3_ip)
        main.ONOSbench.onos_uninstall(ONOS4_ip)
        main.ONOSbench.onos_uninstall(ONOS5_ip)
        main.ONOSbench.onos_uninstall(ONOS6_ip)
        main.ONOSbench.onos_uninstall(ONOS7_ip)

        clean_install_result = main.TRUE
        git_pull_result = main.TRUE

        main.step("Compiling the latest version of ONOS")
        if PULL_CODE:
            main.step("Git checkout and pull master")
            main.ONOSbench.git_checkout("master")
            git_pull_result = main.ONOSbench.git_pull()

            main.step("Using mvn clean & install")
            clean_install_result = main.TRUE
            if git_pull_result == main.TRUE:
                clean_install_result = main.ONOSbench.clean_install()
            else:
                main.log.warn("Did not pull new code so skipping mvn "+ \
                        "clean install")
        main.ONOSbench.get_version(report=True)

        cell_result = main.ONOSbench.set_cell("SingleHA")
        verify_result = main.ONOSbench.verify_cell()
        main.step("Creating ONOS package")
        package_result = main.ONOSbench.onos_package()

        main.step("Installing ONOS package")
        onos1_install_result = main.ONOSbench.onos_install(options="-f",
                node=ONOS1_ip)


        main.step("Checking if ONOS is up yet")
        #TODO check bundle:list?
        for i in range(2):
            onos1_isup = main.ONOSbench.isup(ONOS1_ip)
            if onos1_isup:
                break
        if not onos1_isup:
            main.log.report("ONOS1 didn't start!")

        # TODO: if it becomes an issue, we can retry this step  a few times


        cli_result = main.ONOScli1.start_onos_cli(ONOS1_ip)

        main.step("Start Packet Capture MN")
        main.Mininet2.start_tcpdump(
                str(main.params['MNtcpdump']['folder'])+str(main.TEST)+"-MN.pcap",
                intf = main.params['MNtcpdump']['intf'],
                port = main.params['MNtcpdump']['port'])


        case1_result = (clean_install_result and package_result and
                cell_result and verify_result and onos1_install_result and
                onos1_isup and cli_result)

        utilities.assert_equals(expect=main.TRUE, actual=case1_result,
                onpass="Test startup successful",
                onfail="Test startup NOT successful")


        if case1_result==main.FALSE:
            main.cleanup()
            main.exit()

    def CASE2(self,main) :
        '''
        Assign mastership to controllers
        '''
        import time
        import json
        import re

        main.log.report("Assigning switches to controllers")
        main.case("Assigning Controllers")
        main.step("Assign switches to controllers")

        for i in range (1,29):
           main.Mininet1.assign_sw_controller(sw=str(i),
                    ip1=ONOS1_ip,port1=ONOS1_port)

        mastership_check = main.TRUE
        for i in range (1,29):
            response = main.Mininet1.get_sw_controller("s"+str(i))
            try:
                main.log.info(str(response))
            except:
                main.log.info(repr(response))
            if re.search("tcp:"+ONOS1_ip,response):
                mastership_check = mastership_check and main.TRUE
            else:
                mastership_check = main.FALSE
        if mastership_check == main.TRUE:
            main.log.report("Switch mastership assigned correctly")
        utilities.assert_equals(expect = main.TRUE,actual=mastership_check,
                onpass="Switch mastership assigned correctly",
                onfail="Switches not assigned correctly to controllers")



    def CASE3(self,main) :
        """
        Assign intents

        """
        #FIXME: we must reinstall intents until we have a persistant datastore!
        import time
        import json
        import re
        main.log.report("Adding host intents")
        main.case("Adding host Intents")

        main.step("Discovering  Hosts( Via pingall for now)")
        #FIXME: Once we have a host discovery mechanism, use that instead

        #install onos-app-fwd
        main.log.info("Install reactive forwarding app")
        main.ONOScli1.feature_install("onos-app-fwd")

        #REACTIVE FWD test
        ping_result = main.FALSE
        time1 = time.time()
        ping_result = main.Mininet1.pingall()
        time2 = time.time()
        main.log.info("Time for pingall: %2f seconds" % (time2 - time1))

        #uninstall onos-app-fwd
        main.log.info("Uninstall reactive forwarding app")
        main.ONOScli1.feature_uninstall("onos-app-fwd")
        #timeout for fwd flows
        time.sleep(10)

        main.step("Add  host intents")
        #TODO:  move the host numbers to params
        import json
        intents_json= json.loads(main.ONOScli1.hosts())
        intent_add_result = True
        for i in range(8,18):
            main.log.info("Adding host intent between h"+str(i)+" and h"+str(i+10))
            host1 =  "00:00:00:00:00:" + str(hex(i)[2:]).zfill(2).upper()
            host2 =  "00:00:00:00:00:" + str(hex(i+10)[2:]).zfill(2).upper()
            host1_id = main.ONOScli1.get_host(host1)['id']
            host2_id = main.ONOScli1.get_host(host2)['id']
            #NOTE: get host can return None
            if host1_id and host2_id:
                tmp_result = main.ONOScli1.add_host_intent(host1_id, host2_id )
            else:
                main.log.error("Error, get_host() failed")
                tmp_result = main.FALSE
            intent_add_result = bool(intent_add_result and tmp_result)
        utilities.assert_equals(expect=True, actual=intent_add_result,
                onpass="Switch mastership correctly assigned",
                onfail="Error in (re)assigning switch mastership")
        #TODO Check if intents all exist in datastore
        #NOTE: Do we need to print this once the test is working?
        #main.log.info(json.dumps(json.loads(main.ONOScli1.intents(json_format=True)),
        #    sort_keys=True, indent=4, separators=(',', ': ') ) )

    def CASE4(self,main) :
        """
        Ping across added host intents
        """
        description = " Ping across added host intents"
        main.log.report(description)
        main.case(description)
        Ping_Result = main.TRUE
        for i in range(8,18):
            ping = main.Mininet1.pingHost(src="h"+str(i),target="h"+str(i+10))
            Ping_Result = Ping_Result and ping
            if ping==main.FALSE:
                main.log.warn("Ping failed between h"+str(i)+" and h" + str(i+10))
            elif ping==main.TRUE:
                main.log.info("Ping test passed!")
                Ping_Result = main.TRUE
        if Ping_Result==main.FALSE:
            main.log.report("Intents have not been installed correctly, pings failed.")
        if Ping_Result==main.TRUE:
            main.log.report("Intents have been installed correctly and verified by pings")
        utilities.assert_equals(expect = main.TRUE,actual=Ping_Result,
                onpass="Intents have been installed correctly and pings work",
                onfail ="Intents have not been installed correctly, pings failed." )

    def CASE5(self,main) :
        '''
        Reading state of ONOS
        '''
        import time
        import json
        from subprocess import Popen, PIPE
        from sts.topology.teston_topology import TestONTopology # assumes that sts is already in you PYTHONPATH

        main.log.report("Setting up and gathering data for current state")
        main.case("Setting up and gathering data for current state")
        #The general idea for this test case is to pull the state of (intents,flows, topology,...) from each ONOS node
        #We can then compare them with eachother and also with past states

        main.step("Get the Mastership of each switch from each controller")
        global mastership_state
        mastership_state = []

        #Assert that each device has a master
        roles_not_null = main.ONOScli1.roles_not_null()
        utilities.assert_equals(expect = main.TRUE,actual=roles_not_null,
                onpass="Each device has a master",
                onfail="Some devices don't have a master assigned")


        ONOS1_mastership = main.ONOScli1.roles()
        #print json.dumps(json.loads(ONOS1_mastership), sort_keys=True, indent=4, separators=(',', ': '))
        #TODO: Make this a meaningful check
        if "Error" in ONOS1_mastership or not ONOS1_mastership:
            main.log.report("Error in getting ONOS roles")
            main.log.warn("ONOS1 mastership response: " + repr(ONOS1_mastership))
            consistent_mastership = main.FALSE
        else:
            mastership_state = ONOS1_mastership
            consistent_mastership = main.TRUE


        main.step("Get the intents from each controller")
        global intent_state
        intent_state = []
        ONOS1_intents = main.ONOScli1.intents( json_format=True )
        intent_check = main.FALSE
        if "Error" in ONOS1_intents or not ONOS1_intents:
            main.log.report("Error in getting ONOS intents")
            main.log.warn("ONOS1 intents response: " + repr(ONOS1_intents))
        else:
            intent_check = main.TRUE


        main.step("Get the flows from each controller")
        global flow_state
        flow_state = []
        ONOS1_flows = main.ONOScli1.flows( json_format=True )
        flow_check = main.FALSE
        if "Error" in ONOS1_flows or not ONOS1_flows:
            main.log.report("Error in getting ONOS intents")
            main.log.warn("ONOS1 flows repsponse: "+ ONOS1_flows)
        else:
            #TODO: Do a better check, maybe compare flows on switches?
            flow_state = ONOS1_flows
            flow_check = main.TRUE


        main.step("Get the OF Table entries")
        global flows
        flows=[]
        for i in range(1,29):
            flows.append(main.Mininet2.get_flowTable(1.3, "s"+str(i)))

        #TODO: Compare switch flow tables with ONOS flow tables

        main.step("Create TestONTopology object")
        ctrls = []
        count = 1
        temp = ()
        temp = temp + (getattr(main,('ONOS' + str(count))),)
        temp = temp + ("ONOS"+str(count),)
        temp = temp + (main.params['CTRL']['ip'+str(count)],)
        temp = temp + (eval(main.params['CTRL']['port'+str(count)]),)
        ctrls.append(temp)
        MNTopo = TestONTopology(main.Mininet1, ctrls) # can also add Intent API info for intent operations

        main.step("Collecting topology information from ONOS")
        devices = []
        devices.append( main.ONOScli1.devices() )
        '''
        hosts = []
        hosts.append( main.ONOScli1.hosts() )
        '''
        ports = []
        ports.append( main.ONOScli1.ports() )
        links = []
        links.append( main.ONOScli1.links() )


        main.step("Comparing ONOS topology to MN")
        devices_results = main.TRUE
        ports_results = main.TRUE
        links_results = main.TRUE
        for controller in range(num_controllers):
            if devices[controller] or not "Error" in devices[controller]:
                current_devices_result =  main.Mininet1.compare_switches(MNTopo, json.loads(devices[controller]))
            else:
                current_devices_result = main.FALSE
            utilities.assert_equals(expect=main.TRUE, actual=current_devices_result,
                    onpass="ONOS"+str(int(controller+1))+" Switches view is correct",
                    onfail="ONOS"+str(int(controller+1))+" Switches view is incorrect")

            if ports[controller] or not "Error" in ports[controller]:
                current_ports_result =  main.Mininet1.compare_ports(MNTopo, json.loads(ports[controller]))
            else:
                current_ports_result = main.FALSE
            utilities.assert_equals(expect=main.TRUE, actual=current_ports_result,
                    onpass="ONOS"+str(int(controller+1))+" ports view is correct",
                    onfail="ONOS"+str(int(controller+1))+" ports view is incorrect")

            if links[controller] or not "Error" in links[controller]:
                current_links_result =  main.Mininet1.compare_links(MNTopo, json.loads(links[controller]))
            else:
                current_links_result = main.FALSE
            utilities.assert_equals(expect=main.TRUE, actual=current_links_result,
                    onpass="ONOS"+str(int(controller+1))+" links view is correct",
                    onfail="ONOS"+str(int(controller+1))+" links view is incorrect")

            devices_results = devices_results and current_devices_result
            ports_results = ports_results and current_ports_result
            links_results = links_results and current_links_result

        topo_result = devices_results and ports_results and links_results
        utilities.assert_equals(expect=main.TRUE, actual=topo_result,
                onpass="Topology Check Test successful",
                onfail="Topology Check Test NOT successful")

        final_assert = main.TRUE
        final_assert = final_assert and topo_result and flow_check \
                and intent_check and consistent_mastership and roles_not_null
        utilities.assert_equals(expect=main.TRUE, actual=final_assert,
                onpass="State check successful",
                onfail="State check NOT successful")


    def CASE6(self,main) :
        '''
        The Failure case.
        '''
        import time

        main.log.report("Restart ONOS node")
        main.log.case("Restart ONOS node")
        main.ONOSbench.onos_kill(ONOS1_ip)
        start = time.time()

        main.step("Checking if ONOS is up yet")
        count = 0
        while count < 10:
            onos1_isup = main.ONOSbench.isup(ONOS1_ip)
            if onos1_isup == main.TRUE:
                elapsed = time.time() - start
                break
            else:
                count = count + 1

        cli_result = main.ONOScli1.start_onos_cli(ONOS1_ip)

        case_results = main.TRUE and onos1_isup and cli_result
        utilities.assert_equals(expect=main.TRUE, actual=case_results,
                onpass="ONOS restart successful",
                onfail="ONOS restart NOT successful")
        main.log.info("ESTIMATE: ONOS took %s seconds to restart" % str(elapsed) )
        time.sleep(5)

    def CASE7(self,main) :
        '''
        Check state after ONOS failure
        '''
        import os
        import json
        main.case("Running ONOS Constant State Tests")

        #Assert that each device has a master
        roles_not_null = main.ONOScli1.roles_not_null()
        utilities.assert_equals(expect = main.TRUE,actual=roles_not_null,
                onpass="Each device has a master",
                onfail="Some devices don't have a master assigned")



        main.step("Check if switch roles are consistent across all nodes")
        ONOS1_mastership = main.ONOScli1.roles()
        #FIXME: Refactor this whole case for single instance
        #print json.dumps(json.loads(ONOS1_mastership), sort_keys=True, indent=4, separators=(',', ': '))
        if "Error" in ONOS1_mastership or not ONOS1_mastership:
            main.log.report("Error in getting ONOS mastership")
            main.log.warn("ONOS1 mastership response: " + repr(ONOS1_mastership))
            consistent_mastership = main.FALSE
        else:
            consistent_mastership = main.TRUE
            main.log.report("Switch roles are consistent across all ONOS nodes")
        utilities.assert_equals(expect = main.TRUE,actual=consistent_mastership,
                onpass="Switch roles are consistent across all ONOS nodes",
                onfail="ONOS nodes have different views of switch roles")


        description2 = "Compare switch roles from before failure"
        main.step(description2)

        current_json = json.loads(ONOS1_mastership)
        old_json = json.loads(mastership_state)
        mastership_check = main.TRUE
        for i in range(1,29):
            switchDPID = str(main.Mininet1.getSwitchDPID(switch="s"+str(i)))

            current = [switch['master'] for switch in current_json if switchDPID in switch['id']]
            old = [switch['master'] for switch in old_json if switchDPID in switch['id']]
            if current == old:
                mastership_check = mastership_check and main.TRUE
            else:
                main.log.warn("Mastership of switch %s changed" % switchDPID)
                mastership_check = main.FALSE
        if mastership_check == main.TRUE:
            main.log.report("Mastership of Switches was not changed")
        utilities.assert_equals(expect=main.TRUE,actual=mastership_check,
                onpass="Mastership of Switches was not changed",
                onfail="Mastership of some switches changed")
        mastership_check = mastership_check and consistent_mastership



        main.step("Get the intents and compare across all nodes")
        ONOS1_intents = main.ONOScli1.intents( json_format=True )
        intent_check = main.FALSE
        if "Error" in ONOS1_intents or not ONOS1_intents:
            main.log.report("Error in getting ONOS intents")
            main.log.warn("ONOS1 intents response: " + repr(ONOS1_intents))
        else:
            intent_check = main.TRUE
            main.log.report("Intents are consistent across all ONOS nodes")
        utilities.assert_equals(expect = main.TRUE,actual=intent_check,
                onpass="Intents are consistent across all ONOS nodes",
                onfail="ONOS nodes have different views of intents")

        #NOTE: Hazelcast has no durability, so intents are lost
        '''
        main.step("Compare current intents with intents before the failure")
        if intent_state == ONOS1_intents:
            same_intents = main.TRUE
            main.log.report("Intents are consistent with before failure")
        #TODO: possibly the states have changed? we may need to figure out what the aceptable states are
        else:
            same_intents = main.FALSE
        utilities.assert_equals(expect = main.TRUE,actual=same_intents,
                onpass="Intents are consistent with before failure",
                onfail="The Intents changed during failure")
        intent_check = intent_check and same_intents
        '''



        main.step("Get the OF Table entries and compare to before component failure")
        Flow_Tables = main.TRUE
        flows2=[]
        for i in range(28):
            main.log.info("Checking flow table on s" + str(i+1))
            tmp_flows = main.Mininet2.get_flowTable(1.3, "s"+str(i+1))
            flows2.append(tmp_flows)
            temp_result = main.Mininet2.flow_comp(flow1=flows[i],flow2=tmp_flows)
            Flow_Tables = Flow_Tables and temp_result
            if Flow_Tables == main.FALSE:
                main.log.info("Differences in flow table for switch: "+str(i+1))
        if Flow_Tables == main.TRUE:
            main.log.report("No changes were found in the flow tables")
        utilities.assert_equals(expect=main.TRUE,actual=Flow_Tables,
                onpass="No changes were found in the flow tables",
                onfail="Changes were found in the flow tables")


        #Test of LeadershipElection

        leader = ONOS1_ip
        leader_result = main.TRUE
        for controller in range(1,num_controllers+1):
            node = getattr( main, ( 'ONOScli' + str( controller ) ) )#loop through ONOScli handlers
            leaderN = node.election_test_leader()
            #verify leader is ONOS1
            #NOTE even though we restarted ONOS, it is the only one so onos 1 must be leader
            if leaderN == leader:
                #all is well
                pass
            elif leaderN == main.FALSE:
                #error in  response
                main.log.report("Something is wrong with election_test_leader function, check the error logs")
                leader_result = main.FALSE
            elif leader != leaderN:
                leader_result = main.FALSE
                main.log.report("ONOS" + str(controller) + " sees "+str(leaderN) +
                        " as the leader of the election app. Leader should be "+str(leader) )
        if leader_result:
            main.log.report("Leadership election tests passed(consistent view of leader across listeners and a new leader was re-elected if applicable)")
        utilities.assert_equals(expect=main.TRUE, actual=leader_result,
                onpass="Leadership election passed",
                onfail="Something went wrong with Leadership election")


        result = mastership_check and intent_check and Flow_Tables and roles_not_null\
                and leader_result
        result = int(result)
        if result == main.TRUE:
            main.log.report("Constant State Tests Passed")
        utilities.assert_equals(expect=main.TRUE,actual=result,
                onpass="Constant State Tests Passed",
                onfail="Constant state tests failed")

    def CASE8 (self,main):
        '''
        Compare topo
        '''
        import sys
        sys.path.append("/home/admin/sts") # Trying to remove some dependancies, #FIXME add this path to params
        from sts.topology.teston_topology import TestONTopology # assumes that sts is already in you PYTHONPATH
        import json
        import time

        description ="Compare ONOS Topology view to Mininet topology"
        main.case(description)
        main.log.report(description)
        main.step("Create TestONTopology object")
        ctrls = []
        count = 1
        temp = ()
        temp = temp + (getattr(main,('ONOS' + str(count))),)
        temp = temp + ("ONOS"+str(count),)
        temp = temp + (main.params['CTRL']['ip'+str(count)],)
        temp = temp + (eval(main.params['CTRL']['port'+str(count)]),)
        ctrls.append(temp)
        MNTopo = TestONTopology(main.Mininet1, ctrls) # can also add Intent API info for intent operations

        main.step("Comparing ONOS topology to MN")
        devices_results = main.TRUE
        ports_results = main.TRUE
        links_results = main.TRUE
        topo_result = main.FALSE
        elapsed = 0
        count = 0
        main.step("Collecting topology information from ONOS")
        start_time = time.time()
        while topo_result == main.FALSE and elapsed < 60:
            count = count + 1
            if count > 1:
                MNTopo = TestONTopology(main.Mininet1, ctrls) # can also add Intent API info for intent operations
            cli_start = time.time()
            devices = []
            devices.append( main.ONOScli1.devices() )
            '''
            hosts = []
            hosts.append( main.ONOScli1.hosts() )
            '''
            ports = []
            ports.append( main.ONOScli1.ports() )
            links = []
            links.append( main.ONOScli1.links() )
            elapsed = time.time() - start_time
            print "CLI time: " + str(time.time() - cli_start)

            for controller in range(num_controllers):
                if devices[controller] or not "Error" in devices[controller]:
                    current_devices_result =  main.Mininet1.compare_switches(MNTopo, json.loads(devices[controller]))
                else:
                    current_devices_result = main.FALSE
                utilities.assert_equals(expect=main.TRUE, actual=current_devices_result,
                        onpass="ONOS"+str(int(controller+1))+" Switches view is correct",
                        onfail="ONOS"+str(int(controller+1))+" Switches view is incorrect")

                if ports[controller] or not "Error" in ports[controller]:
                    current_ports_result =  main.Mininet1.compare_ports(MNTopo, json.loads(ports[controller]))
                else:
                    current_ports_result = main.FALSE
                utilities.assert_equals(expect=main.TRUE, actual=current_ports_result,
                        onpass="ONOS"+str(int(controller+1))+" ports view is correct",
                        onfail="ONOS"+str(int(controller+1))+" ports view is incorrect")

                if links[controller] or not "Error" in links[controller]:
                    current_links_result =  main.Mininet1.compare_links(MNTopo, json.loads(links[controller]))
                else:
                    current_links_result = main.FALSE
                utilities.assert_equals(expect=main.TRUE, actual=current_links_result,
                        onpass="ONOS"+str(int(controller+1))+" links view is correct",
                        onfail="ONOS"+str(int(controller+1))+" links view is incorrect")
            devices_results = devices_results and current_devices_result
            ports_results = ports_results and current_ports_result
            links_results = links_results and current_links_result
            topo_result = devices_results and ports_results and links_results

        topo_result = topo_result and int(count <= 2)
        main.log.report("Very crass estimate for topology discovery/convergence(note it takes about 1 seconds to read the topology from each ONOS instance): " +\
                str(elapsed) + " seconds, " + str(count) +" tries" )
        if elapsed > 60:
            main.log.report("Giving up on topology convergence")
        utilities.assert_equals(expect=main.TRUE, actual=topo_result,
                onpass="Topology Check Test successful",
                onfail="Topology Check Test NOT successful")
        if topo_result == main.TRUE:
            main.log.report("ONOS topology view matches Mininet topology")


    def CASE9 (self,main):
        '''
        Link s3-s28 down
        '''
        #NOTE: You should probably run a topology check after this

        link_sleep = float(main.params['timers']['LinkDiscovery'])

        description = "Turn off a link to ensure that Link Discovery is working properly"
        main.log.report(description)
        main.case(description)


        main.step("Kill Link between s3 and s28")
        Link_Down = main.Mininet1.link(END1="s3",END2="s28",OPTION="down")
        main.log.info("Waiting " + str(link_sleep) + " seconds for link down to be discovered")
        time.sleep(link_sleep)
        utilities.assert_equals(expect=main.TRUE,actual=Link_Down,
                onpass="Link down succesful",
                onfail="Failed to bring link down")
        #TODO do some sort of check here

    def CASE10 (self,main):
        '''
        Link s3-s28 up
        '''
        #NOTE: You should probably run a topology check after this

        link_sleep = float(main.params['timers']['LinkDiscovery'])

        description = "Restore a link to ensure that Link Discovery is working properly"
        main.log.report(description)
        main.case(description)

        main.step("Bring link between s3 and s28 back up")
        Link_Up = main.Mininet1.link(END1="s3",END2="s28",OPTION="up")
        main.log.info("Waiting " + str(link_sleep) + " seconds for link up to be discovered")
        time.sleep(link_sleep)
        utilities.assert_equals(expect=main.TRUE,actual=Link_Up,
                onpass="Link up succesful",
                onfail="Failed to bring link up")
        #TODO do some sort of check here


    def CASE11 (self, main) :
        '''
        Switch Down
        '''
        #NOTE: You should probably run a topology check after this
        import time

        switch_sleep = float(main.params['timers']['SwitchDiscovery'])

        description = "Killing a switch to ensure it is discovered correctly"
        main.log.report(description)
        main.case(description)

        #TODO: Make this switch parameterizable
        main.step("Kill s28 ")
        main.log.report("Deleting s28")
        main.Mininet1.del_switch("s28")
        main.log.info("Waiting " + str(switch_sleep) + " seconds for switch down to be discovered")
        time.sleep(switch_sleep)
        device = main.ONOScli1.get_device(dpid="0028")
        #Peek at the deleted switch
        main.log.warn( str(device) )
        result = main.FALSE
        if device and device['available'] == False:
            result = main.TRUE
        utilities.assert_equals(expect=main.TRUE,actual=result,
                onpass="Kill switch succesful",
                onfail="Failed to kill switch?")

    def CASE12 (self, main) :
        '''
        Switch Up
        '''
        #NOTE: You should probably run a topology check after this
        import time

        switch_sleep = float(main.params['timers']['SwitchDiscovery'])
        description = "Adding a switch to ensure it is discovered correctly"
        main.log.report(description)
        main.case(description)

        main.step("Add back s28")
        main.log.report("Adding back s28")
        main.Mininet1.add_switch("s28", dpid = '0000000000002800')
        #TODO: New dpid or same? Ask Thomas?
        main.Mininet1.add_link('s28', 's3')
        main.Mininet1.add_link('s28', 's6')
        main.Mininet1.add_link('s28', 'h28')
        main.Mininet1.assign_sw_controller(sw="28",
                ip1=ONOS1_ip,port1=ONOS1_port)
        main.log.info("Waiting " + str(switch_sleep) + " seconds for switch up to be discovered")
        time.sleep(switch_sleep)
        device = main.ONOScli1.get_device(dpid="0028")
        #Peek at the deleted switch
        main.log.warn( str(device) )
        result = main.FALSE
        if device and device['available'] == True:
            result = main.TRUE
        utilities.assert_equals(expect=main.TRUE,actual=result,
                onpass="add switch succesful",
                onfail="Failed to add switch?")

    def CASE13 (self, main) :
        '''
        Clean up
        '''
        import os
        import time
        #printing colors to terminal
        colors = {}
        colors['cyan']   = '\033[96m'
        colors['purple'] = '\033[95m'
        colors['blue']   = '\033[94m'
        colors['green']  = '\033[92m'
        colors['yellow'] = '\033[93m'
        colors['red']    = '\033[91m'
        colors['end']    = '\033[0m'
        description = "Test Cleanup"
        main.log.report(description)
        main.case(description)
        main.step("Killing tcpdumps")
        main.Mininet2.stop_tcpdump()

        main.step("Checking ONOS Logs for errors")
        print colors['purple'] + "Checking logs for errors on ONOS1:" + colors['end']
        print main.ONOSbench.check_logs(ONOS1_ip)
        main.step("Copying MN pcap and ONOS log files to test station")
        testname = main.TEST
        teststation_user = main.params['TESTONUSER']
        teststation_IP = main.params['TESTONIP']
        #NOTE: MN Pcap file is being saved to ~/packet_captures
        #       scp this file as MN and TestON aren't necessarily the same vm
        #FIXME: scp
        #####mn files
        #TODO: Load these from params
        #NOTE: must end in /
        log_folder = "/opt/onos/log/"
        log_files = ["karaf.log", "karaf.log.1"]
        #NOTE: must end in /
        dst_dir = "~/packet_captures/"
        for f in log_files:
            main.ONOSbench.handle.sendline( "scp sdn@"+ONOS1_ip+":"+log_folder+f+" "+
                    teststation_user +"@"+teststation_IP+":"+\
                    dst_dir + str(testname) + "-ONOS1-"+f )
            main.ONOSbench.handle.expect("\$")
            print main.ONOSbench.handle.before

        #std*.log's
        #NOTE: must end in /
        log_folder = "/opt/onos/var/"
        log_files = ["stderr.log", "stdout.log"]
        #NOTE: must end in /
        dst_dir = "~/packet_captures/"
        for f in log_files:
            main.ONOSbench.handle.sendline( "scp sdn@"+ONOS1_ip+":"+log_folder+f+" "+
                    teststation_user +"@"+teststation_IP+":"+\
                    dst_dir + str(testname) + "-ONOS1-"+f )


        #sleep so scp can finish
        time.sleep(10)
        main.step("Packing and rotating pcap archives")
        os.system("~/TestON/dependencies/rotate.sh "+ str(testname))


        #TODO: actually check something here
        utilities.assert_equals(expect=main.TRUE, actual=main.TRUE,
                onpass="Test cleanup successful",
                onfail="Test cleanup NOT successful")

    def CASE14 ( self, main ) :
        '''
        start election app on all onos nodes
        '''
        leader_result = main.TRUE
        #install app on onos 1
        main.log.info("Install leadership election app")
        main.ONOScli1.feature_install("onos-app-election")
        #wait for election
        #check for leader
        leader = main.ONOScli1.election_test_leader()
        #verify leader is ONOS1
        if leader == ONOS1_ip:
            #all is well
            pass
        elif leader == None:
            #No leader elected
            main.log.report("No leader was elected")
            leader_result = main.FALSE
        elif leader == main.FALSE:
            #error in  response
            #TODO: add check for "Command not found:" in the driver, this means the app isn't loaded
            main.log.report("Something is wrong with election_test_leader function, check the error logs")
            leader_result = main.FALSE
        else:
            #error in  response
            main.log.report("Unexpected response from election_test_leader function:'"+str(leader)+"'")
            leader_result = main.FALSE




        #install on other nodes and check for leader.
        #Should be onos1 and each app should show the same leader
        for controller in range(2,num_controllers+1):
            node = getattr( main, ( 'ONOScli' + str( controller ) ) )#loop through ONOScli handlers
            node.feature_install("onos-app-election")
            leaderN = node.election_test_leader()
            #verify leader is ONOS1
            if leaderN == ONOS1_ip:
                #all is well
                pass
            elif leaderN == main.FALSE:
                #error in  response
                #TODO: add check for "Command not found:" in the driver, this means the app isn't loaded
                main.log.report("Something is wrong with election_test_leader function, check the error logs")
                leader_result = main.FALSE
            elif leader != leaderN:
                leader_result = main.FALSE
                main.log.report("ONOS" + str(controller) + " sees "+str(leaderN) +
                        " as the leader of the election app. Leader should be "+str(leader) )
        if leader_result:
            main.log.report("Leadership election tests passed(consistent view of leader across listeners and a leader was elected)")
        utilities.assert_equals(expect=main.TRUE, actual=leader_result,
                onpass="Leadership election passed",
                onfail="Something went wrong with Leadership election")

    def CASE15 ( self, main ) :
        '''
        Check that Leadership Election is still functional
        '''
        leader_result = main.TRUE
        description = "Check that Leadership Election is still functional"
        main.log.report(description)
        main.case(description)
        main.step("Find current leader and withdraw")
        leader = main.ONOScli1.election_test_leader()
        #TODO: do some sanity checking on leader before using it
        withdraw_result = main.FALSE
        if leader == ONOS1_ip:
            old_leader = getattr( main, "ONOScli1" )
        elif leader == None or leader == main.FALSE:
            main.log.report("Leader for the election app should be an ONOS node,"\
                    +"instead got '"+str(leader)+"'")
            leader_result = main.FALSE
        withdraw_result = old_leader.election_test_withdraw()


        main.step("Make sure new leader is elected")
        leader_list = []
        leaderN =  main.ONOScli1.election_test_leader() 
        if leaderN == leader:
            main.log.report("ONOS"+str(controller)+" still sees " + str(leader) +\
                    " as leader after they withdrew")
            leader_result = main.FALSE
        elif leaderN == main.FALSE:
            #error in  response
            #TODO: add check for "Command not found:" in the driver, this means the app isn't loaded
            main.log.report("Something is wrong with election_test_leader function, check the error logs")
            leader_result = main.FALSE
        elif leaderN == None:
            main.log.info("There is no leader after the app withdrew from election")
        if leader_result:
            main.log.report("Leadership election tests passed(There is no leader after the old leader resigned)")
        utilities.assert_equals(expect=main.TRUE, actual=leader_result,
                onpass="Leadership election passed",
                onfail="Something went wrong with Leadership election")


        main.step("Run for election on old leader(just so everyone is in the hat)")
        run_result = old_leader.election_test_run()
        leader = main.ONOScli1.election_test_leader()
        #verify leader is ONOS1
        if leader == ONOS1_ip:
            leader_result = main.TRUE
        else:
            leader_result = main.FALSE
        #TODO: assert on  run and withdraw results?

        utilities.assert_equals(expect=main.TRUE, actual=leader_result,
                onpass="Leadership election passed",
                onfail="ONOS1's election app was not leader after it re-ran for election")

