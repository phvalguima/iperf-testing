import subprocess
import time
import os
import stat
import threading
import uuid

class Iperf3(object):

    def __init__(self, _ssh_machine1,
                 _ssh_key1,
                 _ssh_machine2,
                 _ssh_key2):
        self.ssh_machine1 = _ssh_machine1
        self.ssh_machine2 = _ssh_machine2
        self.ssh_key1     = _ssh_key1
        self.ssh_key2     = _ssh_key2



    def generate_test_file(self,
                           command_list,
                           filename):
        
        with open(filename, 'w') as f:
            f.write("#!/bin/bash\n")
            for command in command_list:
                f.write(" ".join(command) + "\n")
                f.write("sleep 5\n")
        os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)


    def get_result_value_from_client_iperf_file(self,client_file):
        print(client_file)
        proc = subprocess.Popen(['./get_value.sh',client_file],stdout=subprocess.PIPE)
        proc.wait()
        value_bytes = proc.communicate()[0].decode('utf-8')
        value=''.join(str(v) for v in value_bytes)
        # May return \n only
        if not value or ('\n' in value and len(value)==1):
            return None
        print(value)
        proc = subprocess.Popen(['./get_metric.sh',client_file],stdout=subprocess.PIPE)
        proc.wait()
        metric_bytes = proc.communicate()[0].decode('utf-8')
        metric=''.join(str(v) for v in metric_bytes)
        if 'M' in metric:
            return float(value)
        if 'G' in metric:
            return (float(value) * 1000.0)
        return(float(value) * 0.001)

    
    def get_results(self,
                    client_key,
                    client_addr,
                    flow_num=20):
        sum = 0.0
        filepath='./' + client_addr + '_'
        filepath += str(uuid.uuid4())
        filepath += '/'
        os.mkdir(filepath)
        scp = subprocess.Popen(['scp','-i',client_key,client_addr + ':~/iperf3_output.*',filepath])
        scp.wait()
        failed_flows = 0
        for i in range(0,flow_num):
            outfile = filepath + 'iperf3_output.' + str(i)
            res = self.get_result_value_from_client_iperf_file(outfile)
            if res == None:
                failed_flows += 1
            else:
                sum += res
            
        print('Total is: {} Mbps'.format(sum))
        print('Mean is: {} Mbps'.format(sum/float(flow_num)))
        
        
    def run_performance_tests(self,
                              use_udp=False, # protocol to be used 
                              bw='500M',       # bandwidth
                              duration='300', 
                              flow_num=20,
                              server_addr=None,
                              server_port=5201,
                              server_file='server_file.sh',
                              client_file='client_file.sh'):
        sleep_between_serv_clients = 30
        s_cmd_base = 'iperf3 -s -1'
        c_cmd_base = 'iperf3 -c ' + self.ssh_machine2 + ' -b ' + bw + ' -t ' + duration
        if use_udp:
            c_cmd_base += ' -u'
        port=server_port
        s_cmd_list = []
        for i in range(0,flow_num):
            outfile = 'iperf3_output.' + str(i)
            #s_cmd = ['ssh','-i',self.ssh_key2,self.ssh_machine2,
            #         'nohup',s_cmd_base,'-p',str(port+i),'&>',outfile]
            s_cmd = ['nohup',s_cmd_base,'-p',str(port+i),'&>',outfile,'&']
            s_cmd_list.append(s_cmd)
            
        self.generate_test_file(s_cmd_list,server_file)
        s_scp = subprocess.Popen(['scp','-i',self.ssh_key2,server_file,self.ssh_machine2 + ':~/']);
        s_scp.wait()
        #print("Running: {} as server".format(s_cmd))
        subprocess.Popen(['ssh','-i',self.ssh_key2,self.ssh_machine2,'./' + server_file])

        
        time.sleep(sleep_between_serv_clients)

        c_cmd_list = []
        for i in range(0,flow_num):
            outfile = 'iperf3_output.' + str(i)
            #c_cmd = ['ssh','-i',self.ssh_key1,self.ssh_machine1,
            #         'nohup',c_cmd_base,'-p',str(port+i),'&>',outfile]
            c_cmd = ['nohup',c_cmd_base,'-p',str(port+i),'&>',outfile,'&']
            c_cmd_list.append(c_cmd)

        self.generate_test_file(c_cmd_list,client_file)
        c_scp = subprocess.Popen(['scp','-i',self.ssh_key1,client_file,self.ssh_machine1 + ':~/']);
        c_scp.wait()
        #print("Running: {} as server".format(c_cmd))
        subprocess.Popen(['ssh','-i',self.ssh_key1,self.ssh_machine1,'./' + client_file])


        print("Waiting for test to finish........")
        time.sleep(int(duration) + sleep_between_serv_clients)
        print("DONE")
        #subprocess.Popen(['ssh','-i',self.ssh_key2,self.ssh_machine2,
        #                  "kill -9 $(ps aux | grep iperf | awk \'{print $2}\')"])
        self.get_results(client_key=self.ssh_key1,
                         client_addr=self.ssh_machine1,
                         flow_num=flow_num)
        


if __name__=="__main__":
    print("*************************************")
    print("** Make sure SSH keys for servers  **")
    print("** SSH address should of form:     **")
    print("** name@IP                         **")
    print("** or                              **")        
    print("** name@hostname                   **")
    print("** Key should be a filepath        **")
    print("**                                 **")
    print("** Make sure iperf3 is installed   **")
    print("*************************************")

    ##### test STARTUP parameters:
    use_udp=False
    bw='500M'
    duration='300'
    flow_num=20
    server_addr=None
    server_port=5201
    
    ####
    # test_list syntax:
    # ( IP MACHINE 1, KEY MACHINE 1, IP MACHINE 2, KEY MACHINE 2)
    test_list = [('10.5.0.3','./id_iperf_test','10.5.0.30','./id_iperf_test')]
                 #('10.5.0.3','./id_iperf_test','10.5.0.30','./id_iperf_test')]
    thread_list = []
    for tup in test_list:
        test = Iperf3(tup[0],tup[1],tup[2],tup[3])
        thread = threading.Thread(test.run_performance_tests(use_udp=use_udp,
                                                             bw=bw,
                                                             duration=duration,
                                                             flow_num=flow_num,
                                                             server_port=server_port))
        thread_list.append(thread)
        thread.start()

    #waiting threads to finish:
    for t in thread_list:
        t.join()
    
    
