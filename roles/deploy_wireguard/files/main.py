#!/usr/bin/python3
import os
import configparser
import re
import socket

import peer

hostname = socket.gethostname()
wireguardIP = f'{socket.gethostbyname(hostname)}:51830'

# добавить возможность генерирования новых конфигов
wireguardConfFile = '/etc/wireguard/wg0.conf'
wireguardPubKeyFile = '/etc/wireguard/publickey'
rootClientFolder = '/etc/wireguard/clients/'

reg_all = r"AllowedIPs.*\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.(?P<last_oktet>\d{1,3}))"
reg_ip = r"AllowedIPs.*\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
reg_last_oktet = r"AllowedIPs.*\s\d{1,3}\.\d{1,3}\.\d{1,3}\.(?P<last_oktet>\d{1,3})"

dns = "10.0.0.1"

# Метод создания директорий
def createFolder(dir_path):
     os.makedirs(dir_path, mode=0o700,exist_ok=False)

# Метод генерирования клиентских ключей
def generateClientKeys(priv, pub):
    os.system(f'wg genkey | tee {priv} | wg pubkey |  tee {pub} > /dev/null 2>&1')

# Функция получения информации из файла
def getFileContent(file_path):
    with open(file_path) as file:
        file_content = file.read().rstrip()
        return(file_content)

# Функция генерирования клиентоского конфига. Данный конфиг должен отправлятся клиенту ввиде текстовго документа и QR кода
def generateClientConfig(client_priv_key, free_ip, dns, wireguard_pub, wireguard_ip):
    config = configparser.RawConfigParser()
    # "сохранение" исходного регистра конфига
    config.optionxform = lambda option:option
    config['Interface']={'PrivateKey': getFileContent(client_priv_key),
                         'Address': free_ip,
                         'DNS': dns}
    config['Peer']={'PublicKey': getFileContent(wireguard_pub),
                    'Endpoint': wireguard_ip,
                    'AllowedIPs': '0.0.0.0/0',
                    'PersistentKeepalive':'20'}
    return(config)

# Функция поиска ip в файле
def getClientsNetworkData(wg_conf, reg):
    # Cоздаем список, для заполнения его найденными ip
    list = []
    # комплируем regex
    reg_compile = re.compile(reg)
    with open(wg_conf) as file:
            ips = reg_compile.findall(file.read())
            for i in ips:
                list.append(int(i))
    return list

# Временное решение, необходимо сделать поиск "свободных" ip
def getNewIP(ips_list):
    if not ips_list:
        ips_list = [1]
    ip = max(ips_list) + 1
    if ip > 1 and ip < 255:
        return ip
    else:
        # cделать нормальную обработку
        return None

# Метод записи данных
def writeData(path, data):
    with open(path, 'w') as file:
        data.write(file)

# Метод создания QR кода, необходима установка qrencode
def makeQR(config, path):
    os.system(f'qrencode -t PNG --output={path} < {config}')

# restart wireguard wg
def restartWireguard():
    os.system('systemctl restart wg-quick@wg0')

# Запрашиваем имя клиента
name = input("Enter client name:\n")
# ip клиента с маской. В дальнейшем,  необходимо найти "свободные адреса"
free_ip = f'10.0.0.{getNewIP(getClientsNetworkData(wireguardConfFile, reg_last_oktet))}/32'
# Переменная пути к папке клиента, которую необходимо создать
client_dir = os.path.join(rootClientFolder, name)
# Переменные пути, по которой будет лежать конфиг, публичный и приватный ключ клиента
client_pub_key = os.path.join(client_dir, f"{name}.key.pub")
client_priv_key = os.path.join(client_dir, f"{name}.key")
client_conf = os.path.join(client_dir, f"{name}.conf")
client_qr_code = os.path.join(client_dir, f"{name}.png")

# Cоздаем папку для клиента
createFolder(client_dir)
# Генерируем публичный и приватный ключ клиента
generateClientKeys(client_priv_key, client_pub_key)
# Генерация клиентского конфига и запись в файл
writeData(client_conf, generateClientConfig(client_priv_key, free_ip, dns, wireguardPubKeyFile, wireguardIP))

peers = peer.Peers()
peers.add_peer(peer.Peer(getFileContent(client_pub_key), free_ip))
peers.append_data(wireguardConfFile,peers)
# Создание клиентского QR кода
makeQR(client_conf,client_qr_code)
restartWireguard()