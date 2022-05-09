"""
TCP/IP Protocol Stack

WARNING: before parsing the application layer over a TCP stream, you must first combine all the TCP frames into a stream. See utils.tcpip for some solutions.
"""

from construct import *  # type: ignore
from construct.lib import *  # type: ignore
import construct_editor.helper.wrapper as cse_wrapper
from . import GalleryItem


#===============================================================================
# layer 2, Ethernet
#===============================================================================

MacAddress = ExprAdapter(Byte[6],
    decoder = lambda obj,ctx: "-".join("%02x" % b for b in obj),
    encoder = lambda obj,ctx: [int(part, 16) for part in obj.split("-")],  # type: ignore
)

ethernet_header = Struct(
    "destination" / MacAddress,
    "source" / MacAddress,
    "type" / Enum(Int16ub,
        IPv4 = 0x0800,
        ARP = 0x0806,
        RARP = 0x8035,
        X25 = 0x0805,
        IPX = 0x8137,
        IPv6 = 0x86DD,
        # default = Pass,
    ),
)

#===============================================================================
# layer 2, ARP
#===============================================================================

# HwAddress = IfThenElse(this.hardware_type == "ETHERNET",
#     MacAddressAdapter(Bytes(this.hwaddr_length)),
#     Bytes(this.hwaddr_length)
# )

HwAddress = Bytes(this.hwaddr_length)

# ProtoAddress = IfThenElse(this.protocol_type == "IP",
#     IpAddressAdapter(Bytes(this.protoaddr_length)),
#     Bytes(this.protoaddr_length)
# )

ProtoAddress = Bytes(this.protoaddr_length)

arp_header = Struct(
    "hardware_type" / Enum(Int16ub,
        ETHERNET = 1,
        EXPERIMENTAL_ETHERNET = 2,
        ProNET_TOKEN_RING = 4,
        CHAOS = 5,
        IEEE802 = 6,
        ARCNET = 7,
        HYPERCHANNEL = 8,
        ULTRALINK = 13,
        FRAME_RELAY = 15,
        FIBRE_CHANNEL = 18,
        IEEE1394 = 24,
        HIPARP = 28,
        ISO7816_3 = 29,
        ARPSEC = 30,
        IPSEC_TUNNEL = 31,
        INFINIBAND = 32,
    ),
    "protocol_type" / Enum(Int16ub,
        IP = 0x0800,
    ),
    "hwaddr_length" / Int8ub,
    "protoaddr_length" / Int8ub,
    "opcode" / Enum(Int16ub,
        REQUEST = 1,
        REPLY = 2,
        REQUEST_REVERSE = 3,
        REPLY_REVERSE = 4,
        DRARP_REQUEST = 5,
        DRARP_REPLY = 6,
        DRARP_ERROR = 7,
        InARP_REQUEST = 8,
        InARP_REPLY = 9,
        ARP_NAK = 10
    ),
    "source_hwaddr" / HwAddress,
    "source_protoaddr" / ProtoAddress,
    "dest_hwaddr" / HwAddress,
    "dest_protoaddr" / ProtoAddress,
)

#===============================================================================
# layer 2, Message Transport Part 2 (SS7 protocol stack)
# (untested)
#===============================================================================

mtp2_header = BitStruct(
    "flag1" / Octet,
    "bsn" / BitsInteger(7),
    "bib" / Bit,
    "fsn" / BitsInteger(7),
    "sib" / Bit,
    "length" / Octet,
    "service_info" / Octet,
    "signalling_info" / Octet,
    "crc" / BitsInteger(16),
    "flag2" / Octet,
)

#===============================================================================
# layer 3, IP v4
#===============================================================================

IpAddress = ExprAdapter(Byte[4],
    decoder = lambda obj,ctx: "{0}.{1}.{2}.{3}".format(*obj),
    encoder = lambda obj,ctx: [int(x) for x in obj.split(".")],  # type: ignore
)

ProtocolEnum = Enum(Int8ub,
    ICMP = 1,
    TCP = 6,
    UDP = 17,
)

ipv4_header = Struct(
    "header" / BitStruct(
        "version" / Const(4, Nibble),
        "header_length" / ExprAdapter(Nibble,
            decoder = lambda obj, ctx: obj * 4,
            encoder = lambda obj, ctx: obj // 4,  # type: ignore
        ),
    ),
    "header_length" / Computed(this.header.header_length),
    "tos" / BitStruct(
        "precedence" / BitsInteger(3),
        "minimize_delay" / Flag,
        "high_throuput" / Flag,
        "high_reliability" / Flag,
        "minimize_cost" / Flag,
        Padding(1),
    ),
    "total_length" / Int16ub,
    "payload_length" / Computed(this.total_length - this.header_length),
    "identification" / Int16ub,
    "flags" / BitStruct(
        Padding(1),
        "dont_fragment" / Flag,
        "more_fragments" / Flag,
        "frame_offset" / BitsInteger(13),
    ),
    "ttl" / Int8ub,
    "protocol" / ProtocolEnum,
    "checksum" / Int16ub,
    "source" / IpAddress,
    "destination" / IpAddress,
    "options" / Bytes(this.header_length - 20),
)

#===============================================================================
# layer 3, IP v6
#===============================================================================
ProtocolEnum = Enum(Int8ub,
    ICMP = 1,
    TCP = 6,
    UDP = 17,
)

Ipv6Address = ExprAdapter(Byte[16],
    decoder = lambda obj,ctx: ":".join("%02x" % b for b in obj),
    encoder = lambda obj,ctx: [int(part, 16) for part in obj.split(":")],  # type: ignore
)

ipv6_header = Struct(
    "header" / BitStruct(
        "version" / OneOf(BitsInteger(4), [6]),
        "traffic_class" / BitsInteger(8),
        "flow_label" / BitsInteger(20),
    ),
    "payload_length" / Int16ub,
    "protocol" / ProtocolEnum,
    "hoplimit" / Int8ub,
    "ttl" / Computed(this.hoplimit),
    "source" / Ipv6Address,
    "destination" / Ipv6Address,
)

#===============================================================================
# layer 3
# Message Transport Part 3 (SS7 protocol stack)
# (untested)
#===============================================================================

mtp3_header = BitStruct(
    "service_indicator" / Nibble,
    "subservice" / Nibble,
)

#===============================================================================
# layer 3
# Internet Control Message Protocol for IPv4
#===============================================================================

echo_payload = Struct(
    "identifier" / Int16ub,
    "sequence" / Int16ub,
    "data" / Bytes(32),
    # length is implementation dependent, is anyone using more than 32 bytes?
)

dest_unreachable_payload = Struct(
    Padding(2),
    "next_hop_mtu" / Int16ub,
    "host" / IpAddress,
    "echo" / Bytes(8),
)

dest_unreachable_code = Enum(Byte,
    Network_unreachable_error = 0,
    Host_unreachable_error = 1,
    Protocol_unreachable_error = 2,
    Port_unreachable_error = 3,
    The_datagram_is_too_big = 4,
    Source_route_failed_error = 5,
    Destination_network_unknown_error = 6,
    Destination_host_unknown_error = 7,
    Source_host_isolated_error = 8,
    Desination_administratively_prohibited = 9,
    Host_administratively_prohibited2 = 10,
    Network_TOS_unreachable = 11,
    Host_TOS_unreachable = 12,
)

icmp_header = Struct(
    "type" / Enum(Byte,
        Echo_reply = 0,
        Destination_unreachable = 3,
        Source_quench = 4,
        Redirect = 5,
        Alternate_host_address = 6,
        Echo_request = 8,
        Router_advertisement = 9,
        Router_solicitation = 10,
        Time_exceeded = 11,
        Parameter_problem = 12,
        Timestamp_request = 13,
        Timestamp_reply = 14,
        Information_request = 15,
        Information_reply = 16,
        Address_mask_request = 17,
        Address_mask_reply = 18,
        # default = Pass,
    ),
    "code" / Switch(this.type,
        {
            "Destination_unreachable" : dest_unreachable_code,
        },
        default = Byte
    ),
    "crc" / Int16ub,
    "payload" / Switch(this.type,
        {
            "Echo_reply" : echo_payload,
            "Echo_request" : echo_payload,
            "Destination_unreachable" : dest_unreachable_payload,
        },
        # default = Pass,
    ),
)

#===============================================================================
# layer 3
# Internet Group Management Protocol, Version 2
#
# http://www.ietf.org/rfc/rfc2236.txt
# jesse@housejunkie.ca
#===============================================================================

igmp_type = Enum(Byte,
    MEMBERSHIP_QUERY = 0x11,
    MEMBERSHIP_REPORT_V1 = 0x12,
    MEMBERSHIP_REPORT_V2 = 0x16,
    LEAVE_GROUP = 0x17,
)

igmpv2_header = Struct(
    "igmp_type" / igmp_type,
    "max_resp_time" / Byte,
    "checksum" / Int16ub,
    "group_address" / IpAddress,
)

#===============================================================================
# layer 4
# Dynamic Host Configuration Protocol for IPv4
#
# http://www.networksorcery.com/enp/protocol/dhcp.htm
# http://www.networksorcery.com/enp/protocol/bootp/options.htm
#===============================================================================

dhcp4_option = Struct(
    "code" / Enum(Byte,
        Pad = 0,
        Subnet_Mask = 1,
        Time_Offset = 2,
        Router = 3,
        Time_Server = 4,
        Name_Server = 5,
        Domain_Name_Server = 6,
        Log_Server = 7,
        Quote_Server = 8,
        LPR_Server = 9,
        Impress_Server = 10,
        Resource_Location_Server = 11,
        Host_Name = 12,
        Boot_File_Size = 13,
        Merit_Dump_File = 14,
        Domain_Name = 15,
        Swap_Server = 16,
        Root_Path = 17,
        Extensions_Path = 18,
        IP_Forwarding_enabledisable = 19,
        Nonlocal_Source_Routing_enabledisable = 20,
        Policy_Filter = 21,
        Maximum_Datagram_Reassembly_Size = 22,
        Default_IP_TTL = 23,
        Path_MTU_Aging_Timeout = 24,
        Path_MTU_Plateau_Table = 25,
        Interface_MTU = 26,
        All_Subnets_are_Local = 27,
        Broadcast_Address = 28,
        Perform_Mask_Discovery = 29,
        Mask_supplier = 30,
        Perform_router_discovery = 31,
        Router_solicitation_address = 32,
        Static_routing_table = 33,
        Trailer_encapsulation = 34,
        ARP_cache_timeout = 35,
        Ethernet_encapsulation = 36,
        Default_TCP_TTL = 37,
        TCP_keepalive_interval = 38,
        TCP_keepalive_garbage = 39,
        Network_Information_Service_domain = 40,
        Network_Information_Servers = 41,
        NTP_servers = 42,
        Vendor_specific_information = 43,
        NetBIOS_over_TCPIP_name_server = 44,
        NetBIOS_over_TCPIP_Datagram_Distribution_Server = 45,
        NetBIOS_over_TCPIP_Node_Type = 46,
        NetBIOS_over_TCPIP_Scope = 47,
        X_Window_System_Font_Server = 48,
        X_Window_System_Display_Manager = 49,
        Requested_IP_Address = 50,
        IP_address_lease_time = 51,
        Option_overload = 52,
        DHCP_message_type = 53,
        Server_identifier = 54,
        Parameter_request_list = 55,
        Message = 56,
        Maximum_DHCP_message_size = 57,
        Renew_time_value = 58,
        Rebinding_time_value = 59,
        Class_identifier = 60,
        Client_identifier = 61,
        NetWareIP_Domain_Name = 62,
        NetWareIP_information = 63,
        Network_Information_Service_Domain = 64,
        Network_Information_Service_Servers = 65,
        TFTP_server_name = 66,
        Bootfile_name = 67,
        Mobile_IP_Home_Agent = 68,
        Simple_Mail_Transport_Protocol_Server = 69,
        Post_Office_Protocol_Server = 70,
        Network_News_Transport_Protocol_Server = 71,
        Default_World_Wide_Web_Server = 72,
        Default_Finger_Server = 73,
        Default_Internet_Relay_Chat_Server = 74,
        StreetTalk_Server = 75,
        StreetTalk_Directory_Assistance_Server = 76,
        User_Class_Information = 77,
        SLP_Directory_Agent = 78,
        SLP_Service_Scope = 79,
        Rapid_Commit = 80,
        Fully_Qualified_Domain_Name = 81,
        Relay_Agent_Information = 82,
        Internet_Storage_Name_Service = 83,
        NDS_servers = 85,
        NDS_tree_name = 86,
        NDS_context = 87,
        BCMCS_Controller_Domain_Name_list = 88,
        BCMCS_Controller_IPv4_address_list = 89,
        Authentication = 90,
        Client_last_transaction_time = 91,
        Associated_ip = 92,
        Client_System_Architecture_Type = 93,
        Client_Network_Interface_Identifier = 94,
        Lightweight_Directory_Access_Protocol = 95,
        Client_Machine_Identifier = 97,
        Open_Group_User_Authentication = 98,
        Autonomous_System_Number = 109,
        NetInfo_Parent_Server_Address = 112,
        NetInfo_Parent_Server_Tag = 113,
        URL = 114,
        Auto_Configure = 116,
        Name_Service_Search = 117,
        Subnet_Selection = 118,
        DNS_domain_search_list = 119,
        SIP_Servers_DHCP_Option = 120,
        Classless_Static_Route_Option = 121,
        CableLabs_Client_Configuration = 122,
        GeoConf = 123,
    ),
    "value" / If(this.code != "Pad", Prefixed(Byte, GreedyBytes)),
)

dhcp4_header = Struct(
    "opcode" / Enum(Byte,
        BootRequest = 1,
        BootReply = 2,
    ),
    "hardware_type" / Enum(Byte,
        Ethernet = 1,
        Experimental_Ethernet = 2,
        ProNET_Token_Ring = 4,
        Chaos = 5,
        IEEE_802 = 6,
        ARCNET = 7,
        Hyperchannel = 8,
        Lanstar = 9,
    ),
    "hardware_address_length" / Byte,
    "hop_count" / Byte,
    "transaction_id" / Int32ub,
    "elapsed_time" / Int16ub,
    "flags" / BitStruct(
        "broadcast" / Flag,
        Padding(15),
    ),
    "client_addr" / IpAddress,
    "your_addr" / IpAddress,
    "server_addr" / IpAddress,
    "relay_addr" / IpAddress,
    "client_hardware_addr" / Bytes(16),
    "server_host_name" / Bytes(64),
    "boot_filename" / Bytes(128),
    # BOOTP/DHCP options
    # "The first four bytes contain the (decimal) values 99, 130, 83 and 99"
    "signature" / Const(b"\x63\x82\x53\x63"),
    "options" / GreedyRange(dhcp4_option),
)

#===============================================================================
# layer 4
# Dynamic Host Configuration Protocol for IPv6
#
# http://www.networksorcery.com/enp/rfc/rfc3315.txt
#===============================================================================

dhcp6_option = Struct(
    "code" / Enum(Int16ub,
        OPTION_CLIENTID = 1,
        OPTION_SERVERID = 2,
        OPTION_IA_NA = 3,
        OPTION_IA_TA = 4,
        OPTION_IAADDR = 5,
        OPTION_ORO = 6,
        OPTION_PREFERENCE = 7,
        OPTION_ELAPSED_TIME = 8,
        OPTION_RELAY_MSG = 9,
        OPTION_AUTH = 11,
        OPTION_UNICAST = 12,
        OPTION_STATUS_CODE = 13,
        OPTION_RAPID_COMMIT = 14,
        OPTION_USER_CLASS = 15,
        OPTION_VENDOR_CLASS = 16,
        OPTION_VENDOR_OPTS = 17,
        OPTION_INTERFACE_ID = 18,
        OPTION_RECONF_MSG = 19,
        OPTION_RECONF_ACCEPT = 20,
        SIP_SERVERS_DOMAIN_NAME_LIST = 21,
        SIP_SERVERS_IPV6_ADDRESS_LIST = 22,
        DNS_RECURSIVE_NAME_SERVER = 23,
        DOMAIN_SEARCH_LIST = 24,
        OPTION_IA_PD = 25,
        OPTION_IAPREFIX = 26,
        OPTION_NIS_SERVERS = 27,
        OPTION_NISP_SERVERS = 28,
        OPTION_NIS_DOMAIN_NAME = 29,
        OPTION_NISP_DOMAIN_NAME = 30,
        SNTP_SERVER_LIST = 31,
        INFORMATION_REFRESH_TIME = 32,
        BCMCS_CONTROLLER_DOMAIN_NAME_LIST = 33,
        BCMCS_CONTROLLER_IPV6_ADDRESS_LIST = 34,
        OPTION_GEOCONF_CIVIC = 36,
        OPTION_REMOTE_ID = 37,
        RELAY_AGENT_SUBSCRIBER_ID = 38,
        OPTION_CLIENT_FQDN = 39,
    ),
    "data" / Prefixed(Int16ub, GreedyBytes),
)

client_message = BitStruct(
    "transaction_id" / BitsInteger(24),
)

relay_message = Struct(
    "hop_count" / Byte,
    "linkaddr" / Ipv6Address,
    "peeraddr" / Ipv6Address,
)

dhcp6_message = Struct(
    "msgtype" / Enum(Byte,
        # these are client-server messages
        SOLICIT = 1,
        ADVERTISE = 2,
        REQUEST = 3,
        CONFIRM = 4,
        RENEW = 5,
        REBIND = 6,
        REPLY = 7,
        RELEASE_ = 8,
        DECLINE_ = 9,
        RECONFIGURE = 10,
        INFORMATION_REQUEST = 11,
        # these two are relay messages
        RELAY_FORW = 12,
        RELAY_REPL = 13,
    ),
    # relay messages have a different structure from client-server messages
    "params" / Switch(this.msgtype,
        {
            "RELAY_FORW" : relay_message,
            "RELAY_REPL" : relay_message,
        },
        default = client_message,
    ),
    "options" / GreedyRange(dhcp6_option),
)

#===============================================================================
# layer 4
# ISDN User Part (SS7 protocol stack)
#===============================================================================

isup_header = Struct(
    "routing_label" / Bytes(5),
    "cic" / Int16ub,
    "message_type" / Int8ub,
    # mandatory fixed parameters
    # mandatory variable parameters
    # optional parameters
)

#===============================================================================
# layer 4
# Transmission Control Protocol (TCP/IP protocol stack)
#===============================================================================

tcp_header = Struct(
    "source" / Int16ub,
    "destination" / Int16ub,
    "seq" / Int32ub,
    "ack" / Int32ub,
    "header" / BitStruct(
        "header_length" / ExprAdapter(Nibble,
            encoder = lambda obj,ctx: obj // 4,  # type: ignore
            decoder = lambda obj,ctx: obj * 4,
        ),
        Padding(3),
        # make into FlagsEnum?
        "flags" / Struct(
            "ns"  / Flag,
            "cwr" / Flag,
            "ece" / Flag,
            "urg" / Flag,
            "ack" / Flag,
            "psh" / Flag,
            "rst" / Flag,
            "syn" / Flag,
            "fin" / Flag,
        ),
    ),
    "header_length" / Computed(this.header.header_length),
    "window" / Int16ub,
    "checksum" / Int16ub,
    "urgent" / Int16ub,
    "options" / Bytes(this.header_length - 20),
)

#===============================================================================
# layer 4
# User Datagram Protocol (TCP/IP protocol stack)
#===============================================================================

udp_header = Struct(
    "header_length" / Computed(8),
    "source" / Int16ub,
    "destination" / Int16ub,
    "payload_length" / ExprAdapter(Int16ub,
        encoder = lambda obj,ctx: obj + 8,  # type: ignore
        decoder = lambda obj,ctx: obj - 8,
    ),
    "checksum" / Int16ub,
)

#===============================================================================
# layer 4
# Domain Name System (TCP/IP protocol stack)
#===============================================================================

class DnsStringAdapter(Adapter):
    def _decode(self, obj, context, path):
        return u".".join(obj[:-1])  # type: ignore
    def _encode(self, obj, context, path):
        return obj.split(u".") + [u""]  # type: ignore

class DnsNamesAdapter(Adapter):
    def _decode(self, obj, context, path):
        return [x.label if x.islabel else x.pointer & 0x3fff for x in obj]  # type: ignore
    def _encode(self, obj, context, path):
        return [dict(ispointer=1,pointer=x|0xc000) if isinstance(x,int) else dict(islabel=1,label=x) for x in obj]  # type: ignore

dns_record_class = Enum(Int16ub,
    RESERVED = 0,
    INTERNET = 1,
    CHAOS = 3,
    HESIOD = 4,
    NONE = 254,
    ANY = 255,
)

dns_record_type = Enum(Int16ub,
    IPv4 = 1,
    AUTHORITIVE_NAME_SERVER = 2,
    CANONICAL_NAME = 5,
    NULL = 10,
    MAIL_EXCHANGE = 15,
    TEXT = 16,
    X25 = 19,
    ISDN = 20,
    IPv6 = 28,
    UNSPECIFIED = 103,
    ALL = 255,
)

query_record = Struct(
    "name" / DnsStringAdapter(RepeatUntil(len_(obj_)==0, PascalString(Byte, "ascii"))),
    "type" / dns_record_type,
    "class" / dns_record_class,
)

labelpointer = Struct(
    "firstbyte" / Peek(Byte),
    "islabel" / Computed(this.firstbyte & 0b11000000 == 0),
    "ispointer" / Computed(this.firstbyte & 0b11000000 == 0b11000000),
    Check(this.islabel | this.ispointer),
    "label" / If(this.islabel, PascalString(Byte, "ascii")),
    "pointer" / If(this.ispointer, Int16ub),
)

resource_record = Struct(
    # based on http://www.zytrax.com/books/dns/ch15/#qname
    "names" / DnsNamesAdapter(RepeatUntil(obj_.ispointer | len_(obj_.label)==0, labelpointer)),
    "type" / dns_record_type,
    "class" / dns_record_class,
    "ttl" / Int32ub,
    "rdata" / Prefixed(Int16ub, GreedyBytes),
)

dns = Struct(
    "id" / Int16ub,
    "flags" / BitStruct(
        "type" / Enum(Bit,
            QUERY = 0,
            RESPONSE = 1,
        ),
        "opcode" / Enum(Nibble,
            STANDARD_QUERY = 0,
            INVERSE_QUERY = 1,
            SERVER_STATUS_REQUEST = 2,
            NOTIFY = 4,
            UPDATE = 5,
        ),
        "authoritive_answer" / Flag,
        "truncation" / Flag,
        "recursion_desired" / Flag,
        "recursion_available" / Flag,
        Padding(1),
        "authenticated_data" / Flag,
        "checking_disabled" / Flag,
        "response_code" / Enum(Nibble,
            SUCCESS = 0,
            FORMAT_ERROR = 1,
            SERVER_FAILURE = 2,
            NAME_DOES_NOT_EXIST = 3,
            NOT_IMPLEMENTED = 4,
            REFUSED = 5,
            NAME_SHOULD_NOT_EXIST = 6,
            RR_SHOULD_NOT_EXIST = 7,
            RR_SHOULD_EXIST = 8,
            NOT_AUTHORITIVE = 9,
            NOT_ZONE = 10,
        ),
    ),
    "question_count" / Rebuild(Int16ub, len_(this.questions)),
    "answer_count" / Rebuild(Int16ub, len_(this.answers)),
    "authority_count" / Rebuild(Int16ub, len_(this.authorities)),
    "additional_count" / Rebuild(Int16ub, len_(this.additionals)),
    "questions" / query_record[this.question_count],
    "answers" / resource_record[this.answer_count],
    "authorities" / resource_record[this.authority_count],
    "additionals" / resource_record[this.additional_count],
)

#===============================================================================
# entire IP stack
#===============================================================================

layer4_tcp = Struct(
    "header" / tcp_header,
    "next" / Bytes(this._.header.payload_length - this.header.header_length),
)

layer4_udp = Struct(
    "header" / udp_header,
    "next" / Bytes(this.header.payload_length),
)

layer3_payload = Switch(this.header.protocol,
    {
        "TCP" : layer4_tcp,
        "UDP" : layer4_udp,
        "ICMP" : icmp_header,
    },
    # default = Pass,
)

layer3_ipv4 = Struct(
    "header" / ipv4_header,
    "next" / layer3_payload,
)

layer3_ipv6 = Struct(
    "header" / ipv6_header,
    "next" / layer3_payload,
)

layer2_ethernet = Struct(
    "header" / ethernet_header,
    "next" / Switch(this.header.type,
        {
            "IPv4" : layer3_ipv4,
            "IPv6" : layer3_ipv6,
        },
        # default = Pass,
    ),
)

# ip_stack = "ip_stack" / layer2_ethernet
ip_stack = layer2_ethernet


cse_wrapper.add_adapter_mapping(
    type_str="MacAddress",
    obj_panel=cse_wrapper.AdapterPanelType.String,
    adapter=MacAddress
)
cse_wrapper.add_adapter_mapping(
    type_str="IpAddress",
    obj_panel=cse_wrapper.AdapterPanelType.String,
    adapter=IpAddress
)
cse_wrapper.add_adapter_mapping(
    type_str="Ipv6Address",
    obj_panel=cse_wrapper.AdapterPanelType.String,
    adapter=Ipv6Address
)


gallery_item = GalleryItem(
    construct=ip_stack,
    example_binarys={
        "1": bytes.fromhex("0011508c283c001150886b570800450001e971474000800684e4c0a80202525eedda112a0050d98ec61d54fe977d501844705dcc0000474554202f20485454502f312e310d0a486f73743a207777772e707974686f6e2e6f72670d0a557365722d4167656e743a204d6f7a696c6c612f352e30202857696e646f77733b20553b2057696e646f7773204e5420352e313b20656e2d55533b2072763a312e382e302e3129204765636b6f2f32303036303131312046697265666f782f312e352e302e310d0a4163636570743a20746578742f786d6c2c6170706c69636174696f6e2f786d6c2c6170706c69636174696f6e2f7868746d6c2b786d6c2c746578742f68746d6c3b713d302e392c746578742f706c61696e3b713d302e382c696d6167652f706e672c2a2f2a3b713d302e350d0a4163636570742d4c616e67756167653a20656e2d75732c656e3b713d302e350d0a4163636570742d456e636f64696e673a20677a69702c6465666c6174650d0a4163636570742d436861727365743a2049534f2d383835392d312c7574662d383b713d302e372c2a3b713d302e370d0a4b6565702d416c6976653a203330300d0a436f6e6e656374696f6e3a206b6565702d616c6976650d0a507261676d613a206e6f2d63616368650d0a43616368652d436f6e74726f6c3a206e6f2d63616368650d0a0d0a"),
        "2": bytes.fromhex("0002e3426009001150f2c280080045900598fd22000036063291d149baeec0a8023c00500cc33b8aa7dcc4e588065010ffffcecd0000485454502f312e3120323030204f4b0d0a446174653a204672692c2031352044656320323030362032313a32363a323520474d540d0a5033503a20706f6c6963797265663d22687474703a2f2f7033702e7961686f6f2e636f6d2f7733632f7033702e786d6c222c2043503d2243414f2044535020434f52204355522041444d204445562054414920505341205053442049564169204956446920434f4e692054454c6f204f545069204f55522044454c692053414d69204f54526920554e5269205055426920494e4420504859204f4e4c20554e49205055522046494e20434f4d204e415620494e542044454d20434e542053544120504f4c204845412050524520474f56220d0a43616368652d436f6e74726f6c3a20707269766174650d0a566172793a20557365722d4167656e740d0a5365742d436f6f6b69653a20443d5f796c683d58336f444d54466b64476c6f5a7a567842463954417a49334d5459784e446b4563476c6b417a45784e6a59794d5463314e5463456447567a64414d7742485274634777446157356b5a58677462412d2d3b20706174683d2f3b20646f6d61696e3d2e7961686f6f2e636f6d0d0a436f6e6e656374696f6e3a20636c6f73650d0a5472616e736665722d456e636f64696e673a206368756e6b65640d0a436f6e74656e742d547970653a20746578742f68746d6c3b20636861727365743d7574662d380d0a436f6e74656e742d456e636f64696e673a20677a69700d0a0d0a366263382020200d0a1f8b0800000000000003dcbd6977db38b200faf9fa9cf90f88326dd9b1169212b5d891739cd84ed2936d1277a7d3cbf1a1484a624c910c4979893bbfec7d7bbfec556121012eb29d65e6be7be7762c9240a1502854150a85c2c37b87af9f9c7c7873449e9dbc7c41defcf2f8c5f327a4d1ee76dff79e74bb872787ec43bfa3e9ddeed1ab06692cd234daed762f2e2e3a17bd4e18cfbb276fbb8b74e9f7bb491a7b76da7152a7b1bff110dfed3f5cb896030f4b37b508566dbb9f56def9a4f1240c523748db275791db20367b9a3452f732a5d0f688bdb0e2c44d27bf9c1cb7470830b1632f4a490a3578c18fd6b9c5dec2f7732b2641783109dc0b7268a56e2bd527a931497b93b43f49cd493a98a4c3493a9aa4e349aa6bf01f7cd78d89d6b2ed49b3d9baf223f8b307b5004a67eea627ded2dddadedb78d8656de428f856305f5973779223b0fff05ebbbde1db67082a499289ae0f06863e1c8f4c0639eaccbdd9a3547abf798a1f0ec6c73fafd2e4f151ffd5f1c9e2f9e37ff74e74fbddd941b375eadb0942b3e3d5723a69f6060373a6cff49e6df586dac8b11c4d1f1afd81319b0df45e6fd4925a6cee6db4dbfb19e225bc1b12e56a098aed9309715c3b74dc5fde3e7f122ea3308061dac22f4018a4f8878367af5f4f2ebcc001a2d187bfffbefeb2477f75026be9269165bb93d92ab0532f0cb68264fbda9b6ddd0b92bfff867f3abe1bccd3c5f675eca6ab3820c1caf7f7be20e05363029f93c8f7d2ad46a7b1bd475ff62614f2de2c8cb7f08537d93a35fed0fe9a4c1af44363fb91beabed790f4f0d0e7a6f67c7dbbe3eedfd01e5bcbffe9a64bf289e00307bb1f7852371dadb133df0c3798efba9d93a1db44e87dbd7d8b4cf50e95c780e304be745389fbbf11ef4cddfdcf4b162d629fa94d7defbe2fa892b3ece2c78d8fb221a84517003476a73dc3ad535d6e22c7fbd0db8cf3a511ca6211d3e28933fed9d8ea54f381f66c0c7f2cb0e4c3898ad2b3b0de3c9e918bf25abc88d6ddf02d65581418f94174addc9ebe94717e67ce557207b6d45f892773ae393adc62af57c18ecd27b46e5aa2feea5b58c7c173e6d94be1d3bd5afa3fcf571d409ded9b1eb06ef3d275d00c36f25f4916c6ed2a911cef88b0e4c0ecfa7a5b627936600b3d28d9bdbe411")
    },
)
