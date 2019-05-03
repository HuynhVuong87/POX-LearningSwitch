# Copyright 2012 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's quite similar to the one for NOX.  Credit where credit due. :)
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
from pox.lib.revent import *
from pox.lib.addresses import EthAddr
from pox.lib.util import dpid_to_str
import os
log = core.getLogger()



class Tutorial (EventMixin):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self):
    self.listenTo(core.openflow)
    core.openflow_discovery.addListeners(self)
    # connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  def resend_packet (self, event, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in
    msg.priority = 10
    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    event.connection.send(msg)


  def act_like_hub (self, event, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    log.debug("flood packet %s %s" , (packet.src), (packet.dst))
    self.resend_packet(event, packet_in, of.OFPP_ALL)



  def act_like_switch (self, event, packet, packet_in):
    """
    # Implement switch-like behavior.
    """
    self.mac_to_port[packet.src] = event.port
    

    if packet.dst in self.mac_to_port:
      outport = self.mac_to_port[packet.dst]
      log.debug("installing flow...")
      msg = of.ofp_flow_mod()
      ## Set fields to match received packet
      msg.match.dl_src = packet.src 
      msg.match.dl_dst = packet.dst
      msg.idle_timeout = 30
      msg.hard_timeout = 30
     ### msg.match = of.ofp_match.from_packet(packet)
      msg.priority = 40
      msg.actions.append(of.ofp_action_output(port = outport))
      msg.buffer_id = event.ofp.buffer_id
      event.connection.send(msg)

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(event, packet_in, of.OFPP_ALL)

    


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.
    # self.act_like_hub(event, packet, packet_in)
    self.act_like_switch(event, packet, packet_in)


  def _handle_ConnectionUp (self, event):
    log.debug("Switch %s is up", dpid_to_str(event.dpid))


def launch ():
  """
  Starts the component
  """
  pox.openflow.discovery.launch()
#  def start_switch (event):
 #   log.debug("Controlling %s" % (event.connection,))
  #  Tutorial(event.connection)
#  core.openflow.addListenerByName("ConnectionUp", start_switch)

  core.registerNew(Tutorial)