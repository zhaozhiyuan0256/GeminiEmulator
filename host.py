import paramiko


class Host:
    def __init__(
        self,
        host_ip,
        ssh_port,
        username,
        password,
        type = None,
        parent_host_name = None,
        nic_name = None,
        ovs_port = None,
        mac_address = None,
    ):
        self.host_ip = host_ip
        self.ssh_port = ssh_port
        self.username = username
        self.password = password

        self.type = type
        self.parent_host_name = parent_host_name
        self.nic_name = nic_name
        self.ovs_port = ovs_port
        self.mac_address = mac_address

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(
            self.host_ip,
            self.ssh_port,
            username=self.username,
            password=self.password,
        )

    def close(self):
        self.client.close()

    def execute(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode("utf-8")
