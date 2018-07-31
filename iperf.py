import subprocess
import time

class Iperf3(object):

    def __init__(self, _ssh_machine1,
                 _ssh_key1,
                 _ssh_machine2,
                 _ssh_key2):
        print("*************************************")
        print("** Make sure SSH keys for servers  **")
        print("** SSH address should of form:     **")
        print("** name@IP                         **")
        print("** or                              **")        
        print("** name@hostname                   **")
        print("** Key should be a filepath        **")
        print("*************************************")
        self.ssh_machine1 = _ssh_machine1
        self.ssh_machine2 = _ssh_machine2
        self.ssh_key1     = _ssh_key1
        self.ssh_key2     = _ssh_key2

    def run_performance_tests(self,
                              use_udp=False, # protocol to be used 
                              bw='500M',       # bandwidth
                              duration='300', 
                              flow_num=20,
                              server_addr=None,
                              server_port=5201):
        sleep_between_serv_clients = 30
        s_cmd_base = 'iperf3 -s'
        c_cmd_base = 'iperf3 -c ' + self.ssh_machine2 + ' -b ' + bw + ' -t ' + duration
        if use_udp:
            c_cmd_base += ' -u'
        port=server_port
        for i in range(0,flow_num):
            outfile = 'iperf3_output.' + str(i)
            s_cmd = ['ssh','-i',self.ssh_key2,self.ssh_machine2,
                     'nohup',s_cmd_base,'-p',str(port+i),'&>',outfile]
            print("Running: {} as server".format(s_cmd))
            subprocess.Popen(s_cmd);

        time.sleep(sleep_between_serv_clients)

        for i in range(0,flow_num):
            outfile = 'iperf3_output.' + str(i)
            c_cmd = ['ssh','-i',self.ssh_key1,self.ssh_machine1,
                     'nohup',c_cmd_base,'-p',str(port+i),'&>',outfile]
            print("Running: {} as client".format(c_cmd))
            subprocess.Popen(c_cmd);

        print("Waiting for test to finish........")
        time.sleep(int(duration)+60)
        print("DONE")
        subprocess.Popen(['ssh','-i',self.ssh_key2,self.ssh_machine2,
                          "kill -9 $(ps aux | grep iperf | awk \'{print $2}\')"])


if __name__=="__main__":
    test = Iperf3('10.5.0.6',
                  '/home/ubuntu/id_iperf.key',
                  '10.5.0.19',
                  '/home/ubuntu/id_iperf.key')
    test.run_performance_tests(server_addr=test.ssh_machine2)
