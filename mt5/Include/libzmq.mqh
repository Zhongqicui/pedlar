//+------------------------------------------------------------------+
//|                                                       libzmq.mqh |
//|                                                            nuric |
//|                                  https://github.com/nuric/pedlar |
//+------------------------------------------------------------------+
#property copyright "nuric"
#property link      "https://github.com/nuric/pedlar"
//+------------------------------------------------------------------+
//| defines                                                          |
//+------------------------------------------------------------------+
// Extracted from: https://github.com/zeromq/libzmq/blob/master/include/zmq.h
/*  Socket types. */
#define ZMQ_PAIR 0
#define ZMQ_PUB 1
#define ZMQ_SUB 2
#define ZMQ_REQ 3
#define ZMQ_REP 4
#define ZMQ_DEALER 5
#define ZMQ_ROUTER 6
#define ZMQ_PULL 7
#define ZMQ_PUSH 8
#define ZMQ_XPUB 9
#define ZMQ_XSUB 10
#define ZMQ_STREAM 11
/* Polling options. */
#define ZMQ_POLLIN 1
#define ZMQ_POLLOUT 2
#define ZMQ_POLLERR 4
/* Socket options. */
#define ZMQ_AFFINITY 4
#define ZMQ_IDENTITY 5
#define ZMQ_SUBSCRIBE 6
#define ZMQ_UNSUBSCRIBE 7
#define ZMQ_RATE 8
#define ZMQ_RECOVERY_IVL 9
#define ZMQ_SNDBUF 11
#define ZMQ_RCVBUF 12
#define ZMQ_RCVMORE 13
#define ZMQ_FD 14
#define ZMQ_EVENTS 15
#define ZMQ_TYPE 16
#define ZMQ_LINGER 17
#define ZMQ_RECONNECT_IVL 18
#define ZMQ_BACKLOG 19
#define ZMQ_RECONNECT_IVL_MAX 21
#define ZMQ_MAXMSGSIZE 22
#define ZMQ_SNDHWM 23
#define ZMQ_RCVHWM 24
#define ZMQ_MULTICAST_HOPS 25
#define ZMQ_RCVTIMEO 27
#define ZMQ_SNDTIMEO 28
#define ZMQ_LAST_ENDPOINT 32
#define ZMQ_ROUTER_MANDATORY 33
#define ZMQ_TCP_KEEPALIVE 34
#define ZMQ_TCP_KEEPALIVE_CNT 35
#define ZMQ_TCP_KEEPALIVE_IDLE 36
#define ZMQ_TCP_KEEPALIVE_INTVL 37
#define ZMQ_TCP_ACCEPT_FILTER 38
#define ZMQ_IMMEDIATE 39
#define ZMQ_XPUB_VERBOSE 40
#define ZMQ_ROUTER_RAW 41
#define ZMQ_IPV6 42
#define ZMQ_MECHANISM 43
#define ZMQ_PLAIN_SERVER 44
#define ZMQ_PLAIN_USERNAME 45
#define ZMQ_PLAIN_PASSWORD 46
#define ZMQ_CURVE_SERVER 47
#define ZMQ_CURVE_PUBLICKEY 48
#define ZMQ_CURVE_SECRETKEY 49
#define ZMQ_CURVE_SERVERKEY 50
#define ZMQ_PROBE_ROUTER 51
#define ZMQ_REQ_CORRELATE 52
#define ZMQ_REQ_RELAXED 53
#define ZMQ_CONFLATE 54
#define ZMQ_ZAP_DOMAIN 55
//+------------------------------------------------------------------+
//| Buffer to store tick data                                        |
//+------------------------------------------------------------------+
struct tickbuf
  {
   uchar             topic;
   double            bid;
   double            ask;
  };
//+------------------------------------------------------------------+
//| Buffer to store bar data                                         |
//+------------------------------------------------------------------+
struct barbuf
  {
   uchar             topic;
   double            open;
   double            high;
   double            low;
   double            close;
  };
//+------------------------------------------------------------------+
//| Buffer to store request data                                     |
//+------------------------------------------------------------------+
struct requestbuf
  {
   uchar             action;
   ulong             order_id;
   double            volume;
  };
//+------------------------------------------------------------------+
//| Buffer to store response data                                    |
//+------------------------------------------------------------------+
struct responsebuf
  {
   int               retcode;
   ulong             order_id;
   double            price;
  };
//+------------------------------------------------------------------+
//| Buffer to store response data                                    |
//+------------------------------------------------------------------+
struct pollitem
  {
   long              socket;
   int               fd;
   short             events;
   short             revents;
  };
//+------------------------------------------------------------------+
//| DLL imports                                                      |
//+------------------------------------------------------------------+
// Reference: http://api.zeromq.org/
#import "libzmq.dll"
int zmq_errno();
long zmq_ctx_new();
int zmq_ctx_term(long context);
long zmq_socket(long context,int type);
int zmq_setsockopt(long socket,int option_name,int &option_value[],int option_len);
int zmq_close(long socket);
int zmq_bind(long socket,uchar &endpoint[]);
int zmq_connect(long socket,uchar &endpoint[]);
int zmq_send(long socket,tickbuf &buf,int len,int flags);
int zmq_send(long socket,barbuf &buf,int len,int flags);
int zmq_send(long socket,string buf,int len,int flags);
int zmq_poll(pollitem &items[],int nitems,long timeout);
int zmq_recv(long socket,requestbuf &buf,int len,int flags);
int zmq_send(long socket,responsebuf &buf,int len,int flags);
#import
//+------------------------------------------------------------------+
