import firm_client

from airbrakes.constants import FIRM_PORT

client = firm_client.FIRMClient(FIRM_PORT)
client.start()

client.reboot()
