def ip_to_int(ip):
  return sum([int(byte)*256**(3-i) for i,byte in enumerate(ip.split("."))])
def int_to_ip(num):
  return ".".join([str((num//(256**(3-i)))%256) for i in range(4)])
def get_net_ip(ip,mask=None):
  if mask is None:
    mask=int(ip.split("/")[1])
    ip=ip.split("/")[0]
  devipint=ip_to_int(ip)
  maskint=256**4-2**(32-int(mask))
  netipint=int(devipint & maskint)
  return int_to_ip(netipint)
def get_broadcast(ip,mask=None):
  if mask is None:
    mask=int(ip.split("/")[1])
    ip=ip.split("/")[0]
  devipint=ip_to_int(ip)
  maskint=256**4-2**(32-int(mask))
  broadipint=int(devipint & maskint)+2**(32-int(mask))-1
  return int_to_ip(broadipint)
