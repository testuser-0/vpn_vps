class Peer:
    def __init__(self, pk, ip):
        self.pk = pk
        self.ip = ip
    
    # client pub key
    def get_pk(self):
        return self.pk
    
    def get_ip(self):
        return self.ip

# Класс хранящий клиентов
class Peers:
    def __init__(self):
        self.peers = list()

    def add_peer(self, peer):
        # добавление peer в list peers
        d = {'PublicKey': peer.pk, 'AllowedIPs': peer.ip}
        self.peers.append(d)
    
    def write_conf(self, file):
        for i in self.peers:
            file.write('[Peer]\n')
            for key, value in i.items():
                file.write(f'{key} = {value}\n')
    
    def append_data(self, path, data):
        with open(path, 'a') as file:
            data.write_conf(file)
